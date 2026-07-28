# تدقيق المعمارية الحالية — Current Architecture Audit

> وثيقة تدقيق أولية لمشروع **منصة توليد التقارير**. تصف الحالة الفعلية للكود كما هو الآن (Baseline)، وهي **مصدر الحقيقة** للحالة الراهنة قبل أي إعادة هيكلة.
>
> - تاريخ التدقيق: 2026-07-14
> - نوع المشروع: Local Development MVP (لم يُنشر بعد)
> - الفرع/الحالة: لا يوجد Git repository (سيُنشأ محلياً)

---

## 1. ملخص النظام الحالي

المشروع منصة داخلية لتوليد تقارير **Word (DOCX)** و**PDF** من قوالب DOCX جاهزة، باستخدام بيانات يدخلها المستخدم عبر نماذج ديناميكية.

- **Backend**: Django 5 + Django REST Framework، تطبيق واحد فقط اسمه `reports`.
- **Frontend**: Next.js 16 (App Router) + React 19 + TypeScript، واجهة عربية RTL.
- **Auth**: JWT عبر `djangorestframework-simplejwt`، التوكن يُرجَع في جسم الاستجابة ويُخزَّن في `localStorage`.
- **التوليد**: **synchronous** — يتم داخل نفس HTTP request عبر `docxtpl` ثم LibreOffice headless لتحويل PDF.
- **قاعدة البيانات**: **PostgreSQL بالفعل** (لا يوجد SQLite في المشروع إطلاقاً).
- **التشغيل**: Docker Compose (db + backend + frontend). لا يوجد Redis ولا Celery.
- **الاختبارات**: **لا توجد أي اختبارات** (backend أو frontend).

النظام صغير ونظيف ومترابط، لكنه MVP: منطق الأعمال مبعثر بين Views وServices وSerializers، ولا يوجد فصل واضح بين الوحدات، ولا شبكة أمان اختبارية.

---

## 2. Project tree مختصر

```text
professional-reports-mvp/
├── .env, .env.example, .gitignore
├── README.md
├── docker-compose.yml
├── backend/
│   ├── Dockerfile, .dockerignore, requirements.txt, manage.py
│   ├── config/
│   │   ├── settings.py          # إعداد واحد لكل البيئات
│   │   ├── urls.py              # auth endpoints + include reports.urls
│   │   ├── wsgi.py, asgi.py
│   └── reports/                 # التطبيق الوحيد — كل شيء هنا
│       ├── models.py            # ReportType, GeneratedReport
│       ├── serializers.py       # Login + ReportType + GeneratedReport(+Create)
│       ├── views.py             # Auth + ReportType + Report + Dashboard
│       ├── permissions.py       # IsAdminOrReadOnly, IsOwnerOrAdmin
│       ├── urls.py
│       ├── admin.py, apps.py
│       ├── services/
│       │   ├── report_generation.py   # ReportGenerationService (sync)
│       │   └── pdf_converter.py        # LibreOfficePDFConverter
│       ├── management/commands/seed_initial_data.py
│       ├── migrations/0001_initial.py
│       ├── templates/reports/*.docx    # قوالب Word مخزّنة في الكود
│       └── static/report_assets/*.png
└── frontend/
    ├── Dockerfile, next.config.js, package.json (لا يوجد lockfile)
    ├── tsconfig.json
    └── src/
        ├── app/                 # login, dashboard, reports, reports/new, reports/[id], report-types
        ├── components/          # TopBar, PageHero, StatusBadge, DownloadButton
        └── lib/                 # api.ts, auth.ts, useRequireAuth.ts
```

---

## 3. Backend modules الحالية

عملياً **module واحد** (`reports`) يحمل كل المسؤوليات. لا يوجد فصل حدود:

| الملف | المسؤوليات المختلطة داخله |
|---|---|
| `views.py` | مصادقة (Login/Logout/Me) + إدارة أنواع التقارير + إنشاء التقارير + **استدعاء التوليد synchronously** + التحميل من نظام الملفات + إحصاءات Dashboard |
| `serializers.py` | تحقق تسجيل الدخول + serialization لأنواع التقارير + serialization للتقارير + **تحقق `fields_schema` (business logic)** |
| `services/report_generation.py` | تحديد مسار القالب + render DOCX + استدعاء PDF + كتابة الملفات + تحديث الحالة + معالجة الأخطاء |
| `services/pdf_converter.py` | تحويل LibreOffice (أنظف جزء في المشروع) |
| `permissions.py` | صلاحيتان مبنيتان على `is_staff` فقط |

لا يوجد: `application` layer, `domain` layer, `selectors`, storage abstraction, audit, dashboard module منفصل.

---

## 4. Frontend modules الحالية

بنية App Router بسيطة، لكن **كل المنطق داخل `page.tsx`**:

- `src/app/login/page.tsx` — تسجيل الدخول + حفظ التوكن في localStorage.
- `src/app/reports/new/page.tsx` — تحميل الأنواع + بناء النموذج الديناميكي + التحقق + الإرسال + عرض النتيجة (≈170 سطر، كلها في المكوّن).
- `src/app/reports/[id]/page.tsx` — تفاصيل التقرير.
- `src/app/reports/page.tsx`, `dashboard/page.tsx`, `report-types/page.tsx`.
- `src/lib/api.ts` — عميل `fetch` بسيط + أنواع + `downloadFile` عبر blob.
- `src/lib/auth.ts` — قراءة/كتابة التوكن في `localStorage` (**مشكلة أمنية**).
- `src/lib/useRequireAuth.ts` — حارس مصادقة على العميل فقط.

لا يوجد: مجلد `features/`، عميل API موحّد بمعالجة أخطاء موحّدة، منطق polling، إدارة حالة مصادقة مركزية، أو أي اختبارات.

---

## 5. Database الحالية

- المحرك: **PostgreSQL** (`django.db.backends.postgresql`، psycopg 3). **لا يوجد SQLite** — لذا مسار "الهجرة من SQLite" غير مطلوب؛ يبقى فقط توثيقه كـ N/A مع أدوات احتياطية إن ظهرت لاحقاً.
- الاتصال من متغيرات بيئة منفصلة (`POSTGRES_DB/USER/PASSWORD/HOST/PORT`) وليس `DATABASE_URL`.
- Migration واحدة فقط: `reports/migrations/0001_initial.py`.
- `USE_TZ = True`، لكن `TIME_ZONE = 'Asia/Damascus'` (ليس UTC — يخالف متطلب UTC).
- النماذج:
  - **ReportType**: `name, slug(unique), description, template_file(CharField باسم الملف), fields_schema(JSON list), is_active, timestamps`.
  - **GeneratedReport**: `report_type(FK PROTECT), created_by(FK CASCADE), title, input_data(JSON), docx_file, pdf_file, status(4 states), error_message, timestamps` + indexes على `(created_by,-created_at)` و`status`.
- أسماء الجداول الافتراضية: `reports_reporttype`, `reports_generatedreport` (مهم عند نقل النماذج لاحقاً — انظر §20).

---

## 6. مسار تسجيل الدخول (الحالي)

```
Frontend login/page.tsx
  → POST /api/auth/login/  { username, password }
    → LoginView (AllowAny)
      → LoginSerializer.validate() → authenticate()
      → RefreshToken.for_user(user)
    ← { access, refresh, user }   ← التوكن يُرجَع في الجسم
  → saveAuth() → localStorage.setItem('reports_access'/'reports_refresh'/'reports_user')
الطلبات اللاحقة: Authorization: Bearer <access> من localStorage
Logout: POST /api/auth/logout/ { refresh } → blacklist() + مسح localStorage محلياً
```

مشاكل: التوكن مقروء من JavaScript (XSS)، لا refresh rotation فعّال، لا refresh endpoint، عمر access طويل جداً (12 ساعة)، لا CSRF (لأنه Bearer).

---

## 7. مسار إنشاء التقرير (الحالي)

```
Frontend reports/new → POST /api/reports/ { report_type_id, title, input_data }
  → GeneratedReportViewSet.create()
    → GeneratedReportCreateSerializer (تحقق required فقط)
    → report = serializer.save(created_by=request.user)      status=pending
    → ReportGenerationService(report).generate()   ← يحجب الطلب حتى انتهاء LibreOffice
    ← 201 عند completed / 500 عند failed
```

**مشكلة جوهرية**: HTTP request ينتظر توليد DOCX + تحويل PDF (ثوانٍ). عند الفشل يُرجِع 500 مع محتوى، ويُخزَّن `str(exc)` الكامل في `error_message` (تسريب تفاصيل داخلية).

---

## 8. مسار توليد DOCX وPDF (الحالي)

```
ReportGenerationService.generate():
  status=processing
  output_dir = MEDIA_ROOT/generated_reports/<id>/        ← مسار نظام ملفات مباشر
  template_path = BASE_DIR/reports/templates/reports/<template_file>
  DocxTemplate(template).render(context, autoescape=True).save(docx_path)
  LibreOfficePDFConverter().convert(docx_path, output_dir)
  report.docx_file.name / pdf_file.name = relative path
  status=completed  (أو failed + error_message=str(exc)[:4000])
```

`LibreOfficePDFConverter` (الأنظف): يستخدم قائمة arguments (لا `shell=True`)، `UserInstallation` profile منفصل عبر `tempfile`, timeout=120، يتحقق من returncode ووجود PDF. نقص: لا concurrency guard، لا idempotency، لا تنظيف مجلد المخرجات عند الفشل.

---

## 9. مسار تخزين وتحميل الملفات (الحالي)

- التخزين: `FileField` على `MEDIA_ROOT` (حجم/الملفات في Docker volume `backend_media`).
- التحميل: `GET /api/reports/{id}/download-docx|download-pdf` → `_download_file` يقرأ `file_field.path` مباشرة عبر `open(path,'rb')` ويعيد `FileResponse(as_attachment=True)`.
- الصلاحية: `IsOwnerOrAdmin` عبر `get_object()` (queryset مفلتر بالمالك) → المالك/الأدمن فقط. جيد، لكن:
  - **`FileField.path` مستخدَم داخل الـ view مباشرة** — يخالف storage abstraction ويكسر مع أي backend غير محلي.
  - `download_url` تُبنى في الـ serializer وتُرجَع، والتحميل الفعلي في الـ frontend يضيف `Authorization` header يدوياً.

---

## 10. المسؤوليات المتداخلة

1. `GeneratedReportViewSet.create` = تحقق + حفظ + **تنسيق توليد** + قرار status code. (View تدير workflow كامل)
2. `views.py` يخلط 4 مجالات: auth، catalog، generation، dashboard.
3. `GeneratedReportCreateSerializer.validate` يحمل **قواعد أعمال** (تحقق `fields_schema`) بدل خدمة تحقق مركزية.
4. `ReportGenerationService` يخلط: مسارات ملفات + render + conversion + إدارة حالة + معالجة أخطاء + بناء context.
5. Frontend `page.tsx` يخلط: fetching + form state + validation + submit + عرض.

---

## 11. الملفات متعددة المسؤوليات

| الملف | # مسؤوليات | ملاحظة |
|---|---|---|
| `reports/views.py` | 4+ | يجب تقسيمه على accounts / report_catalog / report_generation / dashboard |
| `reports/serializers.py` | 3+ | فصل بحسب الـ module + سحب تحقق الأعمال لخدمة |
| `services/report_generation.py` | 5+ | فصل rendering/conversion/paths/state/context |
| `frontend/.../reports/new/page.tsx` | 5+ | استخراج feature hooks/components |

---

## 12. Business Logic داخل Views أو Components

- **Views**: قرار توليد التقرير synchronously، اختيار status code بناءً على نتيجة التوليد، فلترة الرؤية بحسب المستخدم، تجميع إحصاءات Dashboard.
- **Serializers**: تحقق الحقول المطلوبة مقابل `fields_schema` (منطق أعمال).
- **Components**: تحقق النموذج، منطق اختيار النوع الافتراضي من query string، بناء context الإرسال.

الهدف المستقبلي: نقلها إلى `application/use cases` و`selectors` وخدمات تحقق مركزية، وطبقة `features/*` في الـ frontend.

---

## 13. مشكلات الاختبارات

- **لا توجد أي اختبارات** في المشروع (backend/frontend).
- لا يوجد `pytest`, `pytest-django`, factories، ولا إعداد اختبار.
- لا يوجد frontend test runner (Jest/Vitest/Testing Library).
- لا CI. لا توجد شبكة أمان قبل إعادة الهيكلة → **أعلى خطر على إعادة الهيكلة**.

---

## 14. مشكلات البيانات وMigrations

- Migration واحدة فقط (`0001_initial`) — سليمة، لكن نقل النماذج بين apps لاحقاً يتطلب حذراً شديداً (انظر §20).
- `TIME_ZONE = Asia/Damascus` بدل UTC.
- لا توجد بيانات على القرص في المستودع (تعيش في Docker volume فقط) — لا يوجد SQLite أو media للنسخ الاحتياطي الآن.
- `seed_initial_data` يعمل **تلقائياً عند كل تشغيل Docker** ويُنشئ admin/user — يخالف متطلب "لا تنشئ Admin تلقائياً".

---

## 15. المشكلات الأمنية

| # | المشكلة | الخطورة |
|---|---|---|
| S1 | JWT في `localStorage` (عرضة لـ XSS) بدل HttpOnly cookies | **Critical** |
| S2 | `error_message = str(exc)[:4000]` + إرجاع 500 بمحتوى → تسريب تفاصيل داخلية للمستخدم | **High** |
| S3 | `SECRET_KEY` افتراضي `change-me` و`DEBUG=True` افتراضياً، بلا حماية production | **High** |
| S4 | كلمات مرور افتراضية في `.env.example` وseed، ومعروضة في README | **High** |
| S5 | لا يوجد أي تحقق أمني عند رفع/استخدام قوالب DOCX (لا توجد ميزة رفع بعد، القوالب من الكود) | **Medium** (يصبح Critical عند إضافة رفع القوالب) |
| S6 | لا Rate limiting (login brute-force ممكن) | **High** |
| S7 | لا refresh rotation، عمر access = 12 ساعة، لا revocation عند logout سوى blacklist اختياري | **Medium** |
| S8 | لا CSRF/غير مطبّق (Bearer فقط) — سيصبح مطلوباً عند التحول لـ cookies | **Medium** |
| S9 | لا audit log لأي عملية حساسة | **Medium** |
| S10 | `error_message` قد يحوي مسارات نظام ملفات داخلية | **Medium** |

---

## 16. مشكلات الاعتمادات وDocker

- **Backend**: نطاقات واسعة (`Django>=5.0,<6.0` ...) بلا lockfile → بناء غير reproducible.
- **Frontend**: **لا يوجد lockfile** (`package-lock.json` غائب)، `Dockerfile` يستخدم `npm install` لا `npm ci`؛ إصدارات دقيقة في `package.json` لكن بلا قفل شجرة الاعتماد.
- **TypeScript 7.0.2** إصدار غير مألوف/محتمل خاطئ (أحدث مستقر وقت التدقيق ~5.x) — يحتاج تحقق.
- **Dockerfiles**: dev فقط؛ backend بلا `CMD` (الأمر في compose)، frontend بلا multi-stage/`build`/`start` للإنتاج.
- `docker-compose.yml`: migrations + seed داخل أمر الـ backend (يخالف "لا تشغّل migrations/seed تلقائياً")؛ لا Redis؛ لا Celery؛ لا healthcheck للـ backend/frontend؛ لا readiness.
- لا أدوات lint/format (ruff/black/eslint/prettier) ولا فحص migrations.

---

## 17. المخاطر مرتبة حسب الأولوية

### Critical
- **C1** لا اختبارات + لا Git → أي إعادة هيكلة بلا شبكة أمان. **يجب** إنشاء Git + characterization tests أولاً.
- **C2** JWT في localStorage (S1).
- **C3** التوليد synchronous يحجب الطلب — يفشل تحت الحمل ومع ملفات كبيرة/timeouts.

### High
- **H1** تسريب أخطاء داخلية للمستخدم (S2, S10).
- **H2** إعدادات production غير محمية (S3) وكلمات مرور افتراضية (S4).
- **H3** لا rate limiting (S6).
- **H4** بناء غير reproducible (لا lockfiles).
- **H5** seed/migrate تلقائي عند كل إقلاع.

### Medium
- **M1** غياب storage abstraction (استخدام `FileField.path` مباشرة).
- **M2** لا template versioning (تعديل قالب يغيّر معنى تقارير قديمة).
- **M3** تحقق `fields_schema` ضعيف ومكرّر في مكانين (serializer + frontend).
- **M4** لا audit log.
- **M5** `TIME_ZONE` ليس UTC.
- **M6** لا health checks / structured logging / correlation id.

### Low
- **L1** Frontend logic داخل الصفحات (صيانة أصعب).
- **L2** لا معالجة أخطاء موحّدة (API error model).
- **L3** TypeScript إصدار مشكوك فيه.
- **L4** لا backup/restore scripts.

---

## 18. خطة التنفيذ الفعلية

المراحل بالترتيب، **كل مرحلة**: كتابة/تشغيل اختبارات → فحص → تحديث `refactor-progress.md` → commit محلي (بدون push). لا انتقال عند فشل غير محلول.

- **Phase 0 — Audit & Safety** *(هذه المرحلة)*: فحص، تدقيق، تهيئة Git، تحديد أوامر baseline.
- **Phase 1 — Baseline Quality**: pytest + pytest-django، characterization tests للمسارات الحرجة، ruff/black، eslint/tsc، lockfiles، CI أولي.
- **Phase 2 — PostgreSQL hardening**: `DATABASE_URL`، UTC، healthcheck + readiness، تشغيل الاختبارات على Postgres، توثيق مسار SQLite كـ N/A + أدوات جاهزة إن لزم.
- **Phase 3 — Backend modular architecture**: استخراج `accounts`, `report_catalog`, `report_generation`, `audit`, `dashboard` + `shared` مع الحفاظ على `db_table` وسلوك API.
- **Phase 4 — Background generation**: Redis + Celery + آلة حالات + توليد async + retries + idempotency + polling API + correlation id.
- **Phase 5 — Storage abstraction**: `DocumentStorage` + LocalStorage + تحميل محمي + إزالة المسارات المباشرة.
- **Phase 6 — Templates**: template versioning + immutability + data migration + تحقق `fields_schema` مركزي + تحقق DOCX البنيوي (zip-slip, signature, macros...).
- **Phase 7 — Security**: HttpOnly cookies + refresh rotation + CSRF + تنظيف الأسرار + permissions + rate limiting + audit log + API error model.
- **Phase 8 — Frontend**: بنية `features/` + عميل API موحّد + حالة مصادقة + نموذج ديناميكي + polling + معالجة أخطاء + اختبارات.
- **Phase 9 — Local operations**: Docker dev stack (db+redis+backend+worker+frontend) + production-capable builds + health checks + structured logging + backup/restore.
- **Phase 10 — Docs & final validation**: architecture.md نهائية مطابقة للكود + ADRs + الأدلة + تشغيل نهائي + التقرير النهائي.

---

## 19. الاختلاف بين البنية الحالية والبنية المستهدفة

| الجانب | الحالي | المستهدف |
|---|---|---|
| هيكل Backend | app واحد `reports` | `apps/{accounts, report_catalog, report_generation, audit, dashboard}` + `shared/` |
| الطبقات | Views + Serializers + Services | API → Use Cases → Domain → ORM/Infra؛ قراءات عبر Selectors |
| التوليد | Synchronous داخل الطلب | Celery async + polling + آلة حالات |
| حالات التقرير | 4 (pending/processing/completed/failed) | 6 (+ queued, cancelled) + transitions صريحة |
| القوالب | ملف في الكود، بلا نسخ | `ReportTemplateVersion` immutable + checksum + statuses |
| التخزين | `FileField.path` مباشر | `DocumentStorage` abstraction (Local الآن، قابل للتوسع) |
| Auth | JWT في localStorage | JWT في HttpOnly cookies + rotation + CSRF |
| تحقق الحقول | داخل serializer + frontend | خدمة مركزية (source of truth في الـ backend) |
| Audit/Rate limit | لا يوجد | Audit log + throttling |
| الاختبارات | لا يوجد | pytest + factories + frontend tests + CI على Postgres |
| Frontend | منطق في الصفحات | `features/*` + عميل API موحّد |
| Docker | db+backend+frontend، seed تلقائي | + redis + worker، بلا seed تلقائي، health checks |

---

## 20. المخاطر الخاصة بنقل Django models بين apps

نقل `ReportType`/`GeneratedReport` من `reports` إلى `report_catalog`/`report_generation`:

- **خطر أهم**: تغيّر اسم الجدول تلقائياً من `reports_reporttype` إلى `report_catalog_reporttype` → Django قد ينشئ جداول جديدة فارغة ويهمل القديمة (فقد بيانات).
- **التخفيف الإلزامي**:
  - تثبيت أسماء الجداول عبر `Meta.db_table = 'reports_reporttype'` / `'reports_generatedreport'` قبل أي نقل.
  - استخدام migrations متدرّجة (staged) و`SeparateDatabaseAndState` **فقط** عند الضرورة ومع اختبار.
  - عدم السماح لـ Django بإنشاء جداول جديدة بدل القديمة؛ التحقق بـ `sqlmigrate` قبل التطبيق.
  - الحفاظ على أسماء FK/constraints؛ مقارنة عدد السجلات قبل/بعد.
  - نقل النماذج على دفعات صغيرة، كل دفعة مع اختبار characterization يمر.
- **قرار موصى به**: الإبقاء على `app_label`/`db_table` الأصلية للجداول مع نقل *الكود* فقط إلى الوحدات الجديدة، لتفادي إعادة تسمية الجداول كلياً (يُوثَّق في ADR-001).

---

## ملاحظة عن بيئة التنفيذ (شفافية)

بيئة العمل الحالية لهذا الـ agent تحتوي Python وNode وLibreOffice وGit، لكنها **لا تحتوي PostgreSQL ولا Redis ولا Docker**، كما أن مجلد المشروع مركّب عبر نظام ملفات (FUSE) **يمنع حذف الملفات** ويمنع تشغيل Git مباشرة داخله. لذلك لا يمكن من هذه البيئة: تشغيل الحزمة الكاملة على Postgres/Redis، أو تشغيل Docker، أو إنشاء Git commits دائمة داخل مجلدك. التفاصيل والخيارات المقترحة في نهاية جلسة العمل وفي `refactor-progress.md`.
