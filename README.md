# بوابة الخدمات الرقمية

بوابة عربية موحدة تجمع الخدمات الداخلية والخارجية ضمن حساب واحد وكتالوج
مدار من قاعدة البيانات. النسخة الحالية تتضمن:

- منصة التقارير الاحترافية لإنتاج ملفات Word وPDF.
- أداة تهيئة جهات الاتصال من Excel وإنتاج VCF وتقارير التنظيف.
- تشغيل آمن لمنصة بطاقات الأعمال عبر رابط يملكه الخادم.
- صلاحيات تقييد مجدولة أو دائمة على مستوى الخدمة، مع سجل تدقيق لعمليات التشغيل.

تُدار الخدمات والقيود من مركز التحكم الإداري. لا تحتوي واجهة Next.js على
قائمة خدمات ثابتة؛ بل تقرأها من `GET /api/services/` وتستخدم
`POST /api/services/{slug}/launch/` قبل فتح أي خدمة.

## التشغيل السريع

من PowerShell داخل مجلد المشروع:

```powershell
Copy-Item .env.example .env
docker-compose up --build -d
docker-compose ps
```

على الأجهزة التي تحتوي إضافة Compose الحديثة يمكن استخدام `docker compose`
بدلاً من `docker-compose`.

تنتظر حاوية `setup` جاهزية PostgreSQL، ثم تنفذ migrations وتهيئة الحسابات
والخدمات مرة واحدة قبل تشغيل Django وCelery وNext.js.

بعد أن تصبح الخدمات `healthy`:

- البوابة: http://localhost:3000
- API: http://localhost:8000/api
- مركز التحكم الإداري: http://localhost:3000/admin
- الإدارة: http://localhost:8000/admin

بيانات التجربة المحلية الافتراضية:

| الدور | اسم المستخدم | كلمة المرور |
|---|---|---|
| مدير | `admin` | `admin123456` |
| مستخدم | `user` | `user123456` |

غيّر كلمات المرور في `.env` قبل أي نشر فعلي.

عند تسجيل الدخول بحساب `admin` تنقل الواجهة المستخدم مباشرة إلى `/admin`. أما الحسابات
العادية فتنقل إلى `/dashboard`. مركز التحكم مستقل عن واجهة المستخدم ويضم إدارة
المستخدمين والخدمات والوظائف والتحليلات وسجل التدقيق والإعدادات.

### التحقق من PostgreSQL

```powershell
docker-compose exec db psql -U reports_user -d reports_db -c "\dt"
docker-compose exec backend python manage.py check
docker-compose logs setup backend db --tail=100
```

لاختبار Admin API وقاعدة البيانات:

```powershell
docker-compose exec backend python -m pytest -q
docker-compose exec db psql -U reports_user -d reports_db -c "\dt"
```

إعداد Django العادي يستخدم محرك `django.db.backends.postgresql` حصراً.
SQLite موجود فقط في `config/settings_test.py` لتشغيل اختبارات الوحدات محلياً؛
ولا تستخدمه حاويات المنصة.

### الإيقاف وإعادة التشغيل

```powershell
docker-compose stop
docker-compose start
docker-compose down
```

لإعادة إنشاء قاعدة التطوير من الصفر، وهذا يحذف بيانات PostgreSQL المحلية:

```powershell
docker-compose down -v
docker-compose up --build -d
```

## الاختبارات

```bash
cd backend
python -m pytest

cd ../frontend
npm run typecheck
npm test
npm run test:excel
npm run build
```

---

# منصة توليد التقارير الاحترافية - MVP

مشروع MVP كامل لتوليد تقارير Word و PDF من قوالب DOCX جاهزة، مع واجهة Next.js عربية RTL، وBackend مبني بـ Django REST Framework، وتشغيل كامل عبر Docker Compose.

## 1. Architecture مختصرة

```text
Browser / Next.js
  - Login
  - Dashboard
  - إنشاء تقرير
  - سجل التقارير
  - تفاصيل التقرير
      |
      | REST API + JWT
      v
Django REST Framework
  - Authentication APIs
  - Report Types APIs
  - Reports APIs
  - Dashboard Stats API
      |
      | ReportGenerationService
      v
DOCX Template Rendering باستخدام docxtpl
      |
      v
LibreOffice Headless داخل Docker
      |
      v
PDF Output
      |
      v
PostgreSQL + Media Storage
```

التوليد في هذا الـ MVP يتم بشكل synchronous لتقليل التعقيد، لكن منطق التوليد موجود في `reports/services/` ويمكن نقله لاحقاً إلى Celery worker بدون تغيير كبير في الـ API.

## 2. Database Schema

### ReportType

| الحقل | النوع | الوصف |
|---|---|---|
| id | BigAutoField | المعرف |
| name | CharField | اسم نوع التقرير |
| slug | SlugField | slug فريد |
| description | TextField | وصف النوع |
| template_file | CharField | اسم ملف قالب Word داخل `reports/templates/reports/` |
| fields_schema | JSONField | تعريف الحقول المطلوبة للواجهة والتحقق |
| is_active | BooleanField | تفعيل/تعطيل النوع |
| created_at | DateTimeField | تاريخ الإنشاء |
| updated_at | DateTimeField | آخر تحديث |

### GeneratedReport

| الحقل | النوع | الوصف |
|---|---|---|
| id | BigAutoField | المعرف |
| report_type | ForeignKey | نوع التقرير |
| created_by | ForeignKey | المستخدم الذي أنشأ التقرير |
| title | CharField | عنوان التقرير |
| input_data | JSONField | بيانات الفورم |
| docx_file | FileField | ملف Word الناتج |
| pdf_file | FileField | ملف PDF الناتج |
| status | CharField | pending / processing / completed / failed |
| error_message | TextField | رسالة الخطأ عند الفشل |
| created_at | DateTimeField | تاريخ الإنشاء |
| updated_at | DateTimeField | آخر تحديث |

## 3. التشغيل

انسخ ملف البيئة:

```bash
cp .env.example .env
```

شغل المشروع:

```bash
docker compose up --build
```

بعد التشغيل:

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000/api
- Django Admin: http://localhost:8000/admin

## 4. بيانات الدخول الافتراضية

يتم إنشاؤها تلقائياً عبر الأمر `seed_initial_data` عند تشغيل Docker:

| الدور | username | password |
|---|---|---|
| admin | admin | admin123456 |
| user | user | user123456 |

يمكن تعديلها من `.env` قبل التشغيل.

## 5. APIs

### Authentication

```http
POST /api/auth/login/
POST /api/auth/logout/
GET  /api/auth/me/
```

### Report Types

```http
GET    /api/report-types/
GET    /api/report-types/{id}/
POST   /api/report-types/          # admin فقط
PUT    /api/report-types/{id}/      # admin فقط
DELETE /api/report-types/{id}/      # admin فقط
```

### Reports

```http
GET  /api/reports/
POST /api/reports/
GET  /api/reports/{id}/
GET  /api/reports/{id}/download-docx/
GET  /api/reports/{id}/download-pdf/
```

### Dashboard

```http
GET /api/dashboard/stats/
```

## 6. الصلاحيات

- المستخدم العادي يرى تقاريره فقط.
- المستخدم العادي يستطيع إنشاء تقرير وتحميل ملفاته.
- الأدمن يرى كل التقارير.
- إدارة أنواع التقارير عبر API متاحة للأدمن فقط.
- Django Admin متاح للأدمن لإدارة البيانات بسرعة في مرحلة MVP.

## 7. قوالب Word

القوالب موجودة هنا:

```text
backend/reports/templates/reports/
  field_visit_template.docx
  employee_evaluation_template.docx
```

تستخدم placeholders مثل:

```text
{{ organization_name }}
{{ visit_date }}
{{ notes }}
```

يمكن تعديل القوالب مباشرة في Word مع الحفاظ على أسماء الـ placeholders الموجودة في `fields_schema`.

## 8. تحويل PDF

التحويل يتم داخل Docker من خلال LibreOffice headless، ولا يحتاج أي برنامج مثبت على جهازك:

```python
libreoffice --headless --convert-to pdf --outdir <output_dir> <docx_file>
```

الكود الفعلي موجود في:

```text
backend/reports/services/pdf_converter.py
```

## 9. الهوية البصرية

تمت إعادة استخدام عناصر الهوية البصرية من مشروع الواجهة المرفق:

- الخطوط: Tajawal و Cairo.
- اتجاه RTL.
- الأخضر الداكن والذهبي والكريمي.
- نمط الشريط العلوي مع الخلفية `topbar-bg.jpg`.
- الشعار `header-logo-ar.png`.
- نمط الكروت والجداول والأزرار والمسافات.

## 10. التطوير لاحقاً

اقتراحات المرحلة التالية:

- نقل `ReportGenerationService.generate()` إلى Celery task.
- إضافة معاينة للتقرير قبل التوليد.
- إضافة فحص antivirus خارجي لقوالب Word المرفوعة من واجهة الأدمن.
- إضافة صلاحيات تفصيلية حسب الإدارات.
