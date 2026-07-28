أنت مهندس برمجيات Senior ومتخصص في تصميم منصات SaaS، وDjango، وDjango REST Framework، وNext.js، وبناء الأنظمة القابلة للتوسع والصيانة.

أريد منك بناء النسخة الأولية لمنصة داخلية تشبه SaaS، تجمع عدة أدوات وخدمات تساعد موظفي المؤسسة في المهام اليومية. المنصة ليست نظام أتمتة معاملات أو Workflow للمؤسسة، بل هي **منصة موحدة للأدوات الإنتاجية والخدمات المساعدة**.

يجب أن تتعامل مع المشروع بوصفه منتجًا حقيقيًا طويل الأجل، وليس Prototype سريعًا أو مجموعة صفحات غير مترابطة.

# 1. الهدف العام

بناء منصة موحدة يستطيع المستخدم من خلالها:

* إنشاء حساب.
* تسجيل الدخول باستخدام اسم المستخدم أو البريد الإلكتروني.
* استعراض جميع الخدمات المتاحة.
* البحث عن خدمة.
* فتح خدمة وتنفيذها داخل المنصة إذا كانت خدمة مدمجة.
* الانتقال إلى منصة خارجية إذا كانت الخدمة مستقلة.
* مشاهدة سجل استخدامه للخدمات.
* متابعة المهام الطويلة ونتائجها.
* تنزيل الملفات الناتجة.
* إضافة الخدمات إلى المفضلة مستقبلًا.
* استخدام المنصة من الهاتف أو الحاسوب أو الجهاز اللوحي.

توجد فئتان من الخدمات:

## النوع الأول: External Service

خدمة مبنية كمنصة مستقلة ولها رابط منفصل.

مثال:

* منصة رفع صور بطاقات الأعمال.
* تستخرج بيانات البطاقات باستخدام OCR والذكاء الاصطناعي.
* تحفظ البيانات في قاعدة بياناتها الخاصة.
* تظهر داخل منصة الخدمات كبطاقة.
* عند الضغط عليها يتم التحقق من صلاحية المستخدم ثم تحويله إلى رابط المنصة الخارجية.
* يجب تسجيل عملية فتح الخدمة ضمن إحصائيات الاستخدام.

سأرسل رابط منصة البطاقات لاحقًا.

## النوع الثاني: Internal Tool

أداة مدمجة مباشرة داخل المنصة.

أمثلة حالية:

* رفع ملف Excel واستخراج معلومات معينة منه.
* ملء نموذج داخل المنصة ثم إنشاء ملف Word باستخدام قالب محدد.
* إزالة خلفية صورة.
* ضغط صورة.
* تغيير أبعاد صورة.
* تحويل صيغ الصور.
* دمج أو تقسيم ملفات PDF مستقبلًا.
* أدوات صغيرة أخرى يمكن إضافتها بسرعة.

سأرسل لاحقًا:

* كود خدمة استخراج البيانات من Excel.
* كود خدمة تعبئة قالب Word.
* رابط منصة البطاقات.
* الهوية البصرية.
* الألوان.
* الخطوط.
* تصميم الـTop Bar.
* الشعارات والأيقونات.

لا تضع منطقًا وهميًا بدل الأكواد التي سأرسلها. أنشئ حاليًا Interfaces وAdapters وStubs واضحة لاستقبالها لاحقًا.

# 2. التقنيات الإلزامية

استخدم:

## Backend

* Python.
* Django.
* Django REST Framework.
* PostgreSQL.
* Redis.
* Celery للمهام غير المتزامنة.
* Celery Beat عند الحاجة إلى مهام دورية.
* تخزين ملفات متوافق مع S3.
* MinIO في بيئة التطوير المحلية.
* إمكانية استبداله لاحقًا بـAWS S3 أو Google Cloud Storage أو أي Object Storage.
* OpenAPI/Swagger لتوثيق الـAPI.

## Frontend

* Next.js باستخدام App Router.
* TypeScript.
* واجهة Responsive بالكامل.
* دعم RTL والعربية من البداية.
* بنية جاهزة لإضافة الإنجليزية مستقبلًا.
* استخدم Tailwind CSS أو نظام Styling منظم ومتوافق مع Next.js.
* لا تضع الألوان مباشرة داخل المكونات.
* استخدم Design Tokens وCSS Variables لاستقبال الهوية البصرية لاحقًا.

## التشغيل

* Docker.
* Docker Compose لبيئة التطوير.
* ملفات Environment منفصلة.
* `.env.example`.
* إعداد واضح للتشغيل المحلي.

استخدم الإصدارات المستقرة والمتوافقة وقت التنفيذ، ولا تربط المشروع بإصدارات قديمة دون سبب.

# 3. الأسلوب المعماري

لا تنشئ Microservice لكل أداة صغيرة.

استخدم في النسخة الأولى:

> Modular Monolith احترافي في الـBackend، مع حدود واضحة بين الوحدات، وقابلية فصل أي وحدة إلى Microservice مستقبلًا.

استخدم مبادئ:

* Separation of Concerns.
* SOLID.
* Dependency Inversion.
* Clean Architecture بصورة عملية غير مبالغ بها.
* Domain-oriented modules.
* Service Layer.
* Adapter Pattern.
* Strategy Pattern للأدوات المختلفة.
* Registry Pattern لتسجيل الأدوات الداخلية.
* Factory Pattern عند إنشاء منفذ الأداة المناسب.
* Repository abstraction فقط عندما يحقق فائدة حقيقية، ولا تنشئ طبقات فارغة فوق Django ORM.
* Thin Views.
* Thin Serializers.
* Business logic خارج Views وReact Components.
* عدم ربط الواجهة بمنطق أداة محددة بشكل عشوائي.

يجب أن تكون الخدمات الموجودة في الواجهة قادمة من قاعدة البيانات، وليس Hardcoded داخل Next.js.

# 4. هيكل المشروع المقترح

أنشئ Monorepo منظمًا بالشكل التالي أو بشكل أفضل مع الحفاظ على نفس الفصل:

```text
project-root/
├── apps/
│   ├── backend/
│   │   ├── config/
│   │   ├── modules/
│   │   │   ├── accounts/
│   │   │   ├── service_catalog/
│   │   │   ├── access_control/
│   │   │   ├── tool_execution/
│   │   │   ├── assets/
│   │   │   ├── jobs/
│   │   │   ├── analytics/
│   │   │   ├── notifications/
│   │   │   └── audit/
│   │   ├── common/
│   │   ├── manage.py
│   │   └── tests/
│   │
│   └── frontend/
│       ├── src/
│       │   ├── app/
│       │   ├── features/
│       │   ├── components/
│       │   ├── layouts/
│       │   ├── lib/
│       │   ├── services/
│       │   ├── hooks/
│       │   ├── types/
│       │   ├── styles/
│       │   └── config/
│       └── tests/
│
├── docs/
│   ├── ADR/
│   ├── API.md
│   └── DEVELOPMENT.md
│
├── infrastructure/
│   ├── docker/
│   └── scripts/
│
├── ARCHITECTURE.md
├── CONTRIBUTING.md
├── README.md
├── docker-compose.yml
└── .env.example
```

يمكنك تحسين البنية إذا كان لديك سبب معماري واضح، لكن يجب توثيق السبب داخل `ARCHITECTURE.md`.

# 5. المستخدمون والمصادقة

أنشئ Custom User Model من بداية المشروع.

بيانات المستخدم:

* `id`
* `username`
* `email`
* `first_name`
* `last_name`
* `mobile_number`
* `password`
* `role`
* `is_active`
* `is_staff`
* `date_joined`
* `last_login`
* `created_at`
* `updated_at`

القواعد:

* `username` إجباري وفريد.
* `email` إجباري وفريد.
* `first_name` إجباري.
* `last_name` إجباري.
* `mobile_number` اختياري.
* لا يستخدم رقم الهاتف لتسجيل الدخول حاليًا.
* خزّن رقم الهاتف بصيغة موحدة وقابلة للتحقق.
* لا تفرض أن رقم الهاتف فريد حاليًا إلا إذا أصبح ذلك مطلوبًا لاحقًا.
* كلمة المرور لا تخزن نصيًا أبدًا.
* استخدم نظام Hashing الخاص بـDjango.
* يوجد دوران فقط حاليًا:

  * `USER`
  * `ADMIN`
* لا توجد أقسام أو إدارات للمستخدمين.
* لا يوجد Multi-Tenancy في النسخة الأولى.
* لا توجد خطط اشتراك أو دفع.
* جميع الخدمات متاحة لجميع المستخدمين افتراضيًا، ما لم:

  * تكن الخدمة معطلة عالميًا.
  * يكن حساب المستخدم معطلًا.
  * يكن المستخدم محظورًا من الخدمة.
  * يكن المستخدم محظورًا من تصنيف أو مجموعة خدمات.

## تسجيل الدخول

يستطيع المستخدم تسجيل الدخول باستخدام:

* اسم المستخدم.
* أو البريد الإلكتروني.

اجعل Endpoint تسجيل الدخول يستقبل حقلًا واحدًا مثل:

```json
{
  "identifier": "username-or-email",
  "password": "user-password"
}
```

يجب تحديد ما إذا كان `identifier` بريدًا إلكترونيًا أو اسم مستخدم بصورة آمنة.

استخدم JWT بصورة آمنة، ويفضل:

* Access Token قصير العمر.
* Refresh Token.
* تخزين التوكنات في HttpOnly Secure Cookies.
* حماية CSRF عند الحاجة.
* عدم تخزين Access Token في Local Storage.
* دعم Logout وإبطال Refresh Token.
* دعم Refresh Rotation وBlacklisting.
* تقييد CORS.
* Rate Limiting على تسجيل الدخول.
* حماية من محاولات التخمين المتكررة.

# 6. كتالوج الخدمات

أنشئ Service Catalog مركزيًا.

كل خدمة يجب أن تكون سجلًا في قاعدة البيانات.

أنشئ نماذج مناسبة، مثل:

## ServiceCategory

حقول مقترحة:

* `id`
* `name_ar`
* `name_en`
* `slug`
* `description`
* `icon`
* `sort_order`
* `is_active`
* `created_at`
* `updated_at`

## Service

حقول مقترحة:

* `id`
* `name_ar`
* `name_en`
* `slug`
* `short_description_ar`
* `short_description_en`
* `full_description_ar`
* `full_description_en`
* `category`
* `service_type`
* `execution_mode`
* `icon`
* `cover_image`
* `is_active`
* `is_featured`
* `sort_order`
* `external_url`
* `internal_tool_key`
* `frontend_key`
* `ui_mode`
* `input_schema`
* `ui_schema`
* `configuration`
* `maximum_file_size`
* `allowed_file_types`
* `retention_hours`
* `created_at`
* `updated_at`

## Service Type

استخدم Enum واضحًا:

```text
EXTERNAL
INTERNAL
```

## Execution Mode

```text
SYNC
ASYNC
```

## UI Mode

```text
GENERIC
CUSTOM
```

### قواعد الخدمة الخارجية

عندما تكون الخدمة `EXTERNAL`:

* يكون لها `external_url`.
* لا يفتح الـFrontend الرابط مباشرة من بيانات البطاقة.
* يستدعي Endpoint مثل:

```text
POST /api/v1/services/{slug}/launch/
```

يقوم الـBackend بـ:

1. التحقق من المستخدم.
2. التحقق من أن الحساب مفعل.
3. التحقق من أن الخدمة مفعلة.
4. التحقق من أن المستخدم غير محظور.
5. تسجيل حدث استخدام.
6. التحقق من أن الرابط صالح ومسموح.
7. إرجاع الرابط أو تنفيذ Redirect آمن.

يجب منع Open Redirect Vulnerabilities.

لا تسمح للمستخدم بإرسال أي رابط خارجي من الطلب.

الرابط يأتي فقط من قاعدة البيانات ويُدار من لوحة التحكم.

جهز Interface مستقبلية لإضافة SSO أو Signed Launch Token للخدمات الخارجية، لكن لا تنفذ SSO وهميًا دون متطلبات فعلية.

### قواعد الخدمة الداخلية

عندما تكون الخدمة `INTERNAL`:

* تستخدم `internal_tool_key`.
* ترتبط بأداة مسجلة داخل Tool Registry.
* قد تستخدم نموذج إدخال Generic مبنيًا من `input_schema`.
* أو واجهة Custom إذا احتاجت الخدمة تجربة خاصة.
* لا تربط اسم الخدمة مباشرة بـ`if/else` داخل View واحدة ضخمة.

# 7. Registry للأدوات الداخلية

أنشئ نظامًا قابلًا للتوسع لتسجيل الأدوات الداخلية.

يجب أن يكون لكل أداة Contract واضح، مثل:

```python
class BaseTool:
    key: str
    execution_mode: str

    def validate_input(self, *, user, files, parameters):
        ...

    def execute(self, *, user, files, parameters, job):
        ...

    def build_result(self, execution_result):
        ...

    def cleanup(self, job):
        ...
```

أنشئ Tool Registry يسمح بتسجيل أدوات مثل:

```text
excel_information_extractor
word_template_filler
image_background_remover
image_compressor
image_resizer
image_format_converter
```

تجنب وضع Business Logic داخل:

* Django Views.
* DRF Serializers.
* Celery Tasks.
* React Components.

يجب أن تستدعي Celery Task الـTool Adapter المناسب من خلال Registry.

# 8. الأدوات الأولية

## 8.1 منصة بطاقات الأعمال

هذه خدمة خارجية.

حاليًا:

* أنشئ سجل Service تجريبي.
* ضع رابطًا من Environment Variable أو قيمة Placeholder واضحة.
* لا تخترع API أو تكاملًا غير موجود.
* جهز Launch Flow.
* سجل عدد مرات فتحها.
* اجعل تعديل الرابط وتفعيل الخدمة من لوحة الإدارة.

سأرسل الرابط الحقيقي لاحقًا.

## 8.2 استخراج المعلومات من Excel

هذه أداة داخلية.

سأرسل الكود الحالي لاحقًا.

حاليًا أنشئ:

* Tool Adapter باسم `ExcelInformationExtractorTool`.
* Endpoint موحد لتنفيذ الأداة.
* رفع ملف Excel.
* التحقق من الامتداد وMIME والحجم.
* Job لمعالجة الملف.
* مكان واضح لإضافة الكود الحالي.
* Result Object منظم.
* واجهة لعرض البيانات المستخرجة.
* إمكانية تنزيل النتيجة مستقبلًا بصيغة Excel أو CSV أو JSON.
* لا تنفذ قواعد استخراج افتراضية من عندك.

## 8.3 تعبئة نموذج وإنتاج Word

هذه أداة داخلية.

سأرسل:

* الكود.
* قالب Word.
* الحقول المطلوبة.

حاليًا أنشئ:

* Tool Adapter باسم `WordTemplateFillerTool`.
* دعم Dynamic Form باستخدام JSON Schema.
* دعم حقول:

  * نص.
  * نص طويل.
  * رقم.
  * تاريخ.
  * اختيار.
  * Checkbox.
  * رفع صورة أو ملف عند الحاجة.
* إمكانية ربط الأداة بقالب Word محفوظ في التخزين.
* إنشاء Job.
* إنتاج ملف DOCX.
* Asset للنتيجة.
* رابط تنزيل مؤقت.
* عدم وضع تفاصيل قالب افتراضي داخل الكود.

## 8.4 إزالة خلفية صورة

هذه أداة داخلية يمكن تنفيذها ضمن النسخة الأولى.

المطلوب:

* رفع PNG أو JPEG.
* فحص الحجم والنوع.
* إنشاء Job غير متزامن.
* تنفيذ المعالجة داخل Worker.
* إنتاج PNG بخلفية شفافة.
* الاحتفاظ بالصورة الناتجة مدة محددة.
* توفير معاينة قبل التنزيل.
* التعامل مع الأخطاء بصورة واضحة.
* عزل مكتبة أو نموذج إزالة الخلفية داخل Adapter حتى يمكن استبداله لاحقًا.

## 8.5 أدوات صغيرة قابلة للإضافة سريعًا

جهز البنية لإضافة أدوات مثل:

* ضغط الصور.
* تغيير أبعاد الصور.
* تحويل PNG إلى JPG والعكس.
* إضافة علامة مائية.
* دمج PDF.
* تقسيم PDF.
* ضغط PDF.
* استخراج النص من صورة.
* إنشاء QR Code.

لا تنفذ جميع هذه الأدوات في المرحلة الأولى إلا إذا كانت بسيطة ولا تؤخر الأساس المعماري.

الأولوية هي جودة الأساس، وليس عدد الأدوات.

# 9. إدارة الملفات

أنشئ Asset Service مركزية.

لا تخزن الملفات الثنائية داخل PostgreSQL.

أنشئ نموذجًا مثل:

## Asset

* `id`
* `owner`
* `original_filename`
* `storage_key`
* `mime_type`
* `size_bytes`
* `checksum`
* `asset_type`
* `status`
* `source_service`
* `is_temporary`
* `expires_at`
* `created_at`
* `updated_at`

المطلوب:

* استخدام Object Storage.
* MinIO محليًا.
* روابط رفع وتنزيل مؤقتة عند الإمكان.
* منع Path Traversal.
* عدم الثقة بامتداد الملف فقط.
* التحقق من MIME الحقيقي.
* وضع حدود للحجم.
* أسماء تخزين غير قابلة للتخمين.
* حساب Checksum.
* إمكانية إضافة Antivirus Scanning لاحقًا.
* حذف الملفات المؤقتة تلقائيًا بعد انتهاء مدة الاحتفاظ.
* عدم تسجيل محتويات الملفات في Logs.
* منع مستخدم من الوصول إلى ملفات مستخدم آخر.

# 10. نظام المهام Jobs

أنشئ Job Model موحدًا للعمليات الداخلية.

حقول مقترحة:

* `id`
* `user`
* `service`
* `tool_key`
* `status`
* `progress`
* `input_assets`
* `output_assets`
* `parameters`
* `result_metadata`
* `error_code`
* `safe_error_message`
* `started_at`
* `completed_at`
* `duration_ms`
* `created_at`
* `updated_at`

الحالات:

```text
CREATED
QUEUED
RUNNING
SUCCEEDED
FAILED
CANCELLED
EXPIRED
```

المطلوب:

* دعم العمليات غير المتزامنة.
* Polling في النسخة الأولى أو Server-Sent Events إذا كانت الإضافة منظمة.
* عدم كشف Stack Trace للمستخدم.
* الاحتفاظ بالتفاصيل التقنية داخل Logs فقط.
* إمكانية إعادة المحاولة حسب نوع الخطأ.
* Idempotency للطلبات التي قد تتكرر.
* عرض سجل مهام المستخدم.
* عرض الحالة والتقدم والنتيجة.

# 11. التحكم بصلاحية الخدمات

جميع الخدمات متاحة لجميع المستخدمين افتراضيًا.

أنشئ نماذج واضحة للتحكم بالاستثناءات.

## UserServiceRestriction

* `user`
* `service`
* `is_blocked`
* `reason`
* `expires_at`
* `created_by`
* `created_at`

## UserCategoryRestriction

* `user`
* `category`
* `is_blocked`
* `reason`
* `expires_at`
* `created_by`
* `created_at`

القواعد:

* تعطيل الحساب يمنع استخدام جميع الخدمات.
* تعطيل الخدمة يمنع الجميع.
* حظر المستخدم من خدمة يمنعه منها فقط.
* حظر المستخدم من Category يمنعه من جميع خدماتها.
* انتهاء الحظر يعيد الوصول تلقائيًا.
* يجب تطبيق الصلاحية في Backend.
* إخفاء البطاقة في Frontend ليس حماية كافية.
* تحقق من الصلاحية عند:

  * فتح الخدمة.
  * Launch للخدمة الخارجية.
  * رفع الملف.
  * بدء Job.
  * قراءة Job.
  * تنزيل النتيجة.

أنشئ Permission Service مركزيًا بدل تكرار نفس الشروط في كل View.

مثال:

```python
service_access_policy.can_access(
    user=request.user,
    service=service,
)
```

# 12. الإحصائيات والتحليلات

أنشئ نظام Analytics داخليًا لا يخزن بيانات الملفات الحساسة.

## ServiceUsageEvent

حقول مقترحة:

* `id`
* `user`
* `service`
* `event_type`
* `job`
* `success`
* `duration_ms`
* `metadata`
* `created_at`

Event Types:

```text
SERVICE_VIEWED
EXTERNAL_SERVICE_LAUNCHED
TOOL_EXECUTION_STARTED
TOOL_EXECUTION_SUCCEEDED
TOOL_EXECUTION_FAILED
RESULT_DOWNLOADED
```

يجب تنقية `metadata` وعدم تخزين:

* كلمات المرور.
* التوكنات.
* محتوى المستند.
* البيانات الشخصية المستخرجة.
* الملفات.
* المفاتيح السرية.

## لوحة الإحصائيات العامة

اعرض:

* إجمالي المستخدمين.
* المستخدمون النشطون.
* المستخدمون المعطلون.
* إجمالي الخدمات.
* الخدمات المفعلة والمعطلة.
* إجمالي العمليات.
* العمليات الناجحة والفاشلة.
* عدد الاستخدامات اليومي والأسبوعي والشهري.
* الخدمات الأكثر استخدامًا.
* الخدمات الأقل استخدامًا.
* متوسط زمن تنفيذ الأدوات.
* نسبة نجاح كل خدمة.
* عدد المستخدمين الفريدين لكل خدمة.
* العمليات الأخيرة.
* الأخطاء الأخيرة الآمنة.

## إحصائيات الخدمة

لكل خدمة:

* إجمالي مرات الاستخدام.
* عدد المستخدمين الفريدين.
* الاستخدام حسب الفترة الزمنية.
* النجاح والفشل.
* متوسط زمن التنفيذ.
* عدد مرات فتح الخدمة الخارجية.
* عدد النتائج التي تم تنزيلها.
* آخر استخدام.
* أكثر المستخدمين استخدامًا إذا كان ذلك مسموحًا لمدير النظام.

أضف فلترة حسب:

* اليوم.
* آخر سبعة أيام.
* آخر ثلاثين يومًا.
* نطاق زمني مخصص.

لا تبنِ Data Warehouse في النسخة الأولى. استخدم PostgreSQL مع Indexes مناسبة وتجميعات محسوبة بصورة منظمة.

# 13. لوحة الإدارة

لا تعتمد على Django Admin وحده.

أنشئ لوحة إدارة احترافية داخل Next.js، مع إمكانية إبقاء Django Admin كأداة تقنية احتياطية.

## إدارة المستخدمين

يستطيع Admin:

* مشاهدة المستخدمين.
* البحث والفلترة.
* إنشاء مستخدم.
* تعديل بيانات المستخدم.
* تفعيل الحساب.
* تعطيل الحساب.
* إعادة ضبط كلمة المرور أو إرسال رابط إعادة تعيين.
* مشاهدة آخر تسجيل دخول.
* مشاهدة إحصائيات استخدام المستخدم.
* حظر المستخدم من خدمة.
* حظره من عدة خدمات.
* حظره من Category.
* تحديد سبب الحظر.
* تحديد تاريخ انتهاء الحظر.
* إزالة الحظر.

## إدارة الخدمات

يستطيع Admin:

* إضافة خدمة.
* تعديلها.
* حذفها Soft Delete أو أرشفتها.
* تفعيلها وتعطيلها.
* تحديد نوعها External أو Internal.
* تعديل الرابط الخارجي.
* تحديد Tool Key.
* رفع Icon أو Cover.
* تحديد التصنيف.
* ترتيب الخدمات.
* جعل الخدمة Featured.
* تحديد أنواع الملفات.
* تحديد الحجم الأقصى.
* تحديد مدة الاحتفاظ.
* تعديل Input Schema وUI Schema من واجهة آمنة أو من خلال JSON Editor مع Validation.
* مشاهدة إحصائيات الخدمة.

## إدارة المهام

يستطيع Admin:

* مشاهدة Jobs.
* الفلترة حسب الحالة والخدمة والمستخدم.
* مشاهدة الأخطاء الآمنة.
* مشاهدة وقت التنفيذ.
* إعادة المحاولة إذا كان ذلك آمنًا.
* إلغاء Job قيد الانتظار.
* عدم عرض محتوى الملفات افتراضيًا.

# 14. واجهات الـAPI

استخدم Versioned API:

```text
/api/v1/
```

أنشئ على الأقل:

## Authentication

```text
POST /api/v1/auth/register/
POST /api/v1/auth/login/
POST /api/v1/auth/logout/
POST /api/v1/auth/refresh/
GET  /api/v1/auth/me/
POST /api/v1/auth/change-password/
POST /api/v1/auth/request-password-reset/
POST /api/v1/auth/reset-password/
```

## Services

```text
GET  /api/v1/services/
GET  /api/v1/services/{slug}/
POST /api/v1/services/{slug}/launch/
GET  /api/v1/service-categories/
```

## Tools and Jobs

```text
POST /api/v1/tools/{service_slug}/execute/
GET  /api/v1/jobs/
GET  /api/v1/jobs/{job_id}/
POST /api/v1/jobs/{job_id}/cancel/
GET  /api/v1/jobs/{job_id}/result/
```

## Assets

```text
POST /api/v1/assets/upload/
GET  /api/v1/assets/{asset_id}/
GET  /api/v1/assets/{asset_id}/download/
DELETE /api/v1/assets/{asset_id}/
```

## Admin

أنشئ Endpoints منظمة تحت:

```text
/api/v1/admin/
```

مع Permission Class خاصة بالـAdmin.

لا تجعل Endpoint إداريًا متاحًا لمستخدم عادي حتى لو أخفيته في الواجهة.

# 15. صفحات الـFrontend

## صفحات عامة

* تسجيل الدخول.
* إنشاء حساب.
* نسيت كلمة المرور.
* إعادة تعيين كلمة المرور.

## صفحات المستخدم

* Dashboard.
* جميع الخدمات.
* صفحة Category.
* صفحة تفاصيل الخدمة.
* صفحة تنفيذ الأداة الداخلية.
* صفحة نتيجة الأداة.
* سجل العمليات.
* تفاصيل Job.
* الملف الشخصي.
* تغيير كلمة المرور.
* صفحة 403.
* صفحة 404.
* صفحة خطأ عامة.

## صفحات الإدارة

* Admin Dashboard.
* Users.
* User Details.
* Services.
* Service Editor.
* Categories.
* Jobs.
* Analytics.
* Restrictions.
* System Health مستقبلًا.

# 16. تصميم تجربة المستخدم

يجب أن تكون المنصة مشابهة لتجربة SaaS حديثة.

## الصفحة الرئيسية

تحتوي على:

* Top Bar.
* شعار المنصة.
* بحث عن خدمة.
* بيانات المستخدم.
* قائمة الحساب.
* الخدمات المميزة.
* جميع الخدمات.
* التصنيفات.
* الخدمات المستخدمة مؤخرًا.
* المهام الجارية.
* Empty States واضحة.
* Loading Skeletons.
* Error States واضحة.

## بطاقة الخدمة

تعرض:

* الأيقونة.
* اسم الخدمة.
* وصفًا مختصرًا.
* التصنيف.
* External أو Internal بطريقة غير مربكة للمستخدم.
* حالة الخدمة.
* زر فتح أو استخدام.
* Badge مثل:

  * جديدة.
  * شائعة.
  * تجريبية.
  * غير متاحة مؤقتًا.

## Responsive Design

يجب دعم:

* الهواتف الصغيرة.
* الهواتف الكبيرة.
* الأجهزة اللوحية.
* الحاسوب المحمول.
* الشاشات الكبيرة.

قواعد:

* Mobile-first.
* لا يوجد Horizontal Scroll غير ضروري.
* الجداول تتحول إلى Cards أو عرض مناسب على الهاتف.
* الـSidebar يصبح Drawer.
* النوافذ والنماذج تعمل باللمس.
* الأزرار لها مساحة لمس مناسبة.
* رفع الملفات يعمل على الهاتف.
* المعاينة والتنزيل يعملان على مختلف الشاشات.

# 17. الهوية البصرية

سأرسل الهوية البصرية لاحقًا.

حاليًا:

* استخدم Theme مؤقتًا ومحايدًا.
* لا توزع قيم الألوان داخل الملفات.
* أنشئ Design Tokens مثل:

```text
--color-primary
--color-primary-hover
--color-secondary
--color-background
--color-surface
--color-text
--color-text-muted
--color-border
--color-success
--color-warning
--color-error
```

أنشئ أيضًا Tokens لـ:

* Spacing.
* Border radius.
* Shadows.
* Typography.
* Container widths.
* Top Bar height.
* Sidebar width.

ضع جميع إعدادات الهوية في مكان مركزي بحيث يمكن تغييرها لاحقًا دون تعديل عشرات المكونات.

أنشئ مكونات مشتركة مثل:

* Button.
* Input.
* Select.
* Checkbox.
* Modal.
* Drawer.
* Card.
* ServiceCard.
* FileUploader.
* JobStatus.
* EmptyState.
* ErrorState.
* DataTable.
* Pagination.
* SearchBox.
* StatCard.
* ChartContainer.
* ConfirmDialog.

# 18. الأمن

طبّق متطلبات أمنية أساسية منذ البداية:

* Validation لجميع المدخلات.
* Authorization في Backend.
* Object-level permissions.
* حماية الملفات.
* منع الوصول إلى Job أو Asset لمستخدم آخر.
* Rate Limiting.
* CSRF Protection حسب طريقة المصادقة.
* CORS محدود.
* Secure Cookies في Production.
* عدم إظهار أسرار أو Stack Traces.
* عدم تسجيل Passwords أو Tokens.
* عدم تخزين Secrets في Git.
* استخدام Environment Variables.
* حماية Admin APIs.
* فحص روابط الخدمات الخارجية.
* منع Open Redirect.
* منع Path Traversal.
* تحديد MIME والحجم.
* منع رفع الملفات التنفيذية.
* Security Headers.
* Content Security Policy مناسبة.
* Soft Delete عندما يكون ذلك مطلوبًا.
* Audit Log للأحداث الإدارية الحساسة.

# 19. Audit Log

أنشئ Audit Log منفصلًا للأحداث الحساسة، مثل:

* تفعيل أو تعطيل مستخدم.
* تغيير دور مستخدم.
* حظر مستخدم من خدمة.
* إزالة الحظر.
* إنشاء أو تعديل خدمة.
* تعطيل خدمة.
* تعديل رابط خارجي.
* تغيير إعدادات أداة.
* حذف Asset.
* إعادة محاولة Job إداريًا.

سجل:

* الفاعل.
* نوع الإجراء.
* الهدف.
* التاريخ.
* IP عند الحاجة.
* القيم المعدلة بصورة آمنة.
* Correlation ID.

لا تسجل محتويات المستندات أو الملفات.

# 20. Logs والمراقبة

استخدم Structured Logging.

كل Request وJob يجب أن يدعم:

* Correlation ID.
* Request ID.
* Job ID.
* User ID بصورة آمنة.
* Service Slug.
* مدة التنفيذ.
* حالة النجاح أو الفشل.

أنشئ:

```text
GET /health/
GET /ready/
```

وجهز النظام مستقبلًا لإضافة:

* OpenTelemetry.
* Prometheus.
* Grafana.
* Sentry.

لا تشترط تشغيل جميعها في النسخة الأولى، لكن لا تمنع البنية إضافتها.

# 21. الاختبارات

أنشئ اختبارات حقيقية.

## Backend

* Unit Tests.
* API Tests.
* Permission Tests.
* Authentication Tests.
* Service Access Tests.
* Restriction Tests.
* Job Tests.
* Asset Ownership Tests.
* External Launch Security Tests.
* Tool Registry Tests.

اختبر خصوصًا:

* الدخول بالبريد.
* الدخول باسم المستخدم.
* منع حساب معطل.
* منع مستخدم محظور من خدمة.
* منع مستخدم محظور من Category.
* منع الوصول إلى ملف مستخدم آخر.
* منع تشغيل خدمة معطلة.
* منع Open Redirect.
* تسجيل Analytics Event.
* تنفيذ Job وفشله بصورة آمنة.

## Frontend

* Component Tests للمكونات المهمة.
* Form Validation Tests.
* Admin Permission Guards.
* E2E لأهم المسارات باستخدام Playwright أو أداة مناسبة:

  * التسجيل.
  * الدخول.
  * استعراض الخدمات.
  * فتح خدمة خارجية.
  * تنفيذ أداة داخلية.
  * مشاهدة Job.
  * تعطيل مستخدم من لوحة الإدارة.

# 22. التوثيق الإلزامي

أنشئ الملفات التالية:

## README.md

يتضمن:

* تعريف المشروع.
* المتطلبات.
* طريقة التشغيل.
* إعداد Environment.
* تشغيل Docker Compose.
* تشغيل Backend.
* تشغيل Frontend.
* إنشاء Superuser.
* تشغيل Migrations.
* تشغيل Celery.
* تشغيل الاختبارات.
* إضافة بيانات تجريبية.

## ARCHITECTURE.md

هذا الملف إلزامي ومهم جدًا.

يجب أن يكون تفصيليًا ويعمل كمرجع لأي مطور أو Claude Code أو Codex يعمل لاحقًا على المشروع.

يجب أن يحتوي على:

1. أهداف النظام.
2. نطاق النسخة الأولى.
3. ما هو خارج النطاق.
4. Architectural Style.
5. سبب اختيار Modular Monolith.
6. مخطط المكونات باستخدام Mermaid.
7. مخطط تدفق الخدمة الخارجية.
8. مخطط تدفق الأداة الداخلية.
9. Backend Modules ومسؤولية كل Module.
10. Frontend Architecture.
11. قواعد Dependency بين الوحدات.
12. Domain Models الرئيسية.
13. Authentication Flow.
14. Authorization Flow.
15. Service Access Policy.
16. Tool Registry.
17. طريقة إضافة Internal Tool جديدة.
18. طريقة إضافة External Service جديدة.
19. Asset Lifecycle.
20. Job Lifecycle.
21. Analytics Events.
22. Error Handling.
23. Logging and Observability.
24. Security Rules.
25. API Conventions.
26. Naming Conventions.
27. Database Rules.
28. Migration Rules.
29. Testing Strategy.
30. Deployment Architecture.
31. Environment Variables.
32. ما الذي يمنع المطور من فعله.
33. Checklist لإضافة خدمة جديدة.
34. Checklist قبل دمج Pull Request.
35. Future Evolution نحو Microservices عند الحاجة.

أضف قسمًا واضحًا باسم:

```text
Architectural Guardrails
```

يتضمن على الأقل:

* لا تضع Business Logic داخل Views.
* لا تضع Business Logic داخل Serializers.
* لا تضع Business Logic داخل React Components.
* لا تصل وحدة مباشرة إلى جداول وحدة أخرى بطريقة عشوائية.
* لا تضف خدمة Hardcoded في Frontend.
* لا تنشئ Microservice لكل أداة.
* لا تخزن الملفات في PostgreSQL.
* لا تثق ببيانات Frontend في الصلاحيات.
* لا تكشف روابط التخزين الدائمة.
* لا تسجل محتوى الملفات.
* لا تضف مكتبة كبيرة دون تبرير.
* لا تكرر منطق التحقق من الصلاحية.
* لا تضف أداة دون Registry وTests وتوثيق.

## CONTRIBUTING.md

يتضمن:

* طريقة إنشاء Branch.
* Naming.
* Commit conventions.
* تشغيل Linters.
* تشغيل Tests.
* شروط Pull Request.
* تحديث `ARCHITECTURE.md` عند تغيير قرار معماري.

## ADR

أنشئ Architecture Decision Records على الأقل للقرارات التالية:

* استخدام Modular Monolith.
* اختيار JWT عبر HttpOnly Cookies.
* استخدام Object Storage.
* استخدام Celery وRedis.
* استخدام Tool Registry.
* الفصل بين External Services وInternal Tools.

# 23. قواعد جودة الكود

* Type hints في Python.
* TypeScript strict mode.
* لا تستخدم `any` دون سبب.
* Formatter وLinter.
* أسماء واضحة.
* Functions قصيرة.
* لا تكرر المنطق.
* لا تترك ملفات ضخمة.
* لا تضع Constants متناثرة.
* استخدم Enums.
* استخدم Custom Exceptions.
* استخدم Error Codes مستقرة.
* أعد Responses موحدة.
* أضف Docstrings للأجزاء المعمارية المهمة.
* لا تكتب تعليقات تشرح ما يفعله السطر بوضوح؛ اشرح القرارات غير الواضحة فقط.

استخدم Response Error Format موحدًا مثل:

```json
{
  "error": {
    "code": "SERVICE_ACCESS_DENIED",
    "message": "You do not have access to this service.",
    "details": null,
    "correlation_id": "..."
  }
}
```

# 24. Seed Data

أنشئ Management Command أو Seed Script يضيف:

## Categories

* أدوات المستندات.
* أدوات البيانات.
* أدوات الصور.
* منصات خارجية.

## Services

* منصة بطاقات الأعمال — External.
* استخراج معلومات من Excel — Internal.
* تعبئة قالب Word — Internal.
* إزالة خلفية صورة — Internal.
* ضغط صورة — Internal Placeholder.
* تغيير أبعاد صورة — Internal Placeholder.

استخدم بيانات Placeholder واضحة ولا تستخدم روابط وهمية على أنها إنتاجية.

# 25. المطلوب تنفيذه الآن

ابدأ بالعمل على مراحل، لكن لا تكتفِ بإعطاء خطة نظرية.

## المرحلة الأولى

نفذ:

1. إنشاء Monorepo.
2. إعداد Django وNext.js.
3. إعداد PostgreSQL وRedis وMinIO وCelery عبر Docker Compose.
4. Custom User Model.
5. التسجيل وتسجيل الدخول بالبريد أو اسم المستخدم.
6. Logout وRefresh وMe.
7. Service Catalog.
8. Categories.
9. External/Internal Service Types.
10. Service Access Policy.
11. User and Category Restrictions.
12. Asset Model.
13. Job Model.
14. Analytics Event Model.
15. Audit Model.
16. Tool Registry الأساسي.
17. Launch Flow للخدمات الخارجية.
18. API Documentation.
19. Dashboard أولي.
20. Service Cards.
21. صفحات Authentication.
22. لوحة Admin أولية.
23. Seed Data.
24. الاختبارات الأساسية.
25. README.
26. `ARCHITECTURE.md`.
27. ملفات ADR.

## المرحلة الثانية

بعد ثبات الأساس:

1. تنفيذ أداة إزالة الخلفية.
2. واجهة رفع ومعاينة وتنزيل الصورة.
3. History للمستخدم.
4. Job Polling.
5. Analytics Dashboard.
6. إدارة الخدمات والمستخدمين والقيود من لوحة الإدارة.

## المرحلة الثالثة

بعد أن أرسل الأكواد:

1. دمج كود Excel داخل Adapter مناسب.
2. عدم نسخ الكود عشوائيًا داخل View.
3. إضافة Tests للكود.
4. دمج Word Template Filler.
5. إضافة Dynamic Form.
6. إضافة قوالب Word.
7. ربط رابط منصة بطاقات الأعمال الحقيقي.
8. تطبيق الهوية البصرية النهائية.

# 26. معايير القبول

لا تعتبر المرحلة الأولى مكتملة إلا إذا:

* يمكن تشغيل المشروع بالكامل عبر Docker Compose.
* يمكن إنشاء مستخدم.
* يمكن تسجيل الدخول بالبريد.
* يمكن تسجيل الدخول باسم المستخدم.
* لا يستطيع المستخدم المعطل الدخول.
* تظهر الخدمات من قاعدة البيانات.
* لا توجد الخدمات Hardcoded داخل واجهة المستخدم.
* يمكن للـAdmin تعطيل خدمة.
* تختفي الخدمة المعطلة أو تظهر كغير متاحة حسب القرار الموثق.
* لا يمكن تشغيل الخدمة المعطلة عبر API.
* يمكن حظر مستخدم من خدمة.
* يمكن حظره من Category.
* لا يمكن تجاوز الحظر بإرسال API Request يدوي.
* يمكن فتح خدمة خارجية عبر Launch Endpoint آمن.
* يتم تسجيل إحصائية فتح الخدمة الخارجية.
* يمكن إنشاء Job لأداة داخلية.
* يمكن للمستخدم مشاهدة Jobs الخاصة به فقط.
* يمكن رفع ملف بطريقة آمنة.
* لا يمكن لمستخدم تنزيل ملف مستخدم آخر.
* توجد لوحة Admin أولية.
* توجد إحصائيات أساسية.
* توجد اختبارات ناجحة.
* يوجد `ARCHITECTURE.md` شامل.
* يوجد README واضح.
* توجد `.env.example`.
* لا توجد أسرار داخل Git.
* التصميم Responsive.
* الواجهة تدعم RTL.
* الهوية البصرية قابلة للتعديل من مكان مركزي.

# 27. طريقة عملك

قبل تنفيذ تعديلات كبيرة:

1. افحص بنية المشروع الحالية إذا كانت موجودة.
2. لا تحذف كودًا موجودًا دون فهمه.
3. قدم خطة تنفيذ مختصرة.
4. نفذ المرحلة الحالية فعليًا.
5. شغل Migrations.
6. شغل الاختبارات.
7. شغل Linters.
8. أصلح الأخطاء.
9. حدّث التوثيق.
10. قدم تقريرًا نهائيًا يوضح:

* ما تم تنفيذه.
* الملفات المهمة.
* القرارات المعمارية.
* طريقة التشغيل.
* الاختبارات.
* الأمور المؤجلة.
* نقاط دمج الأكواد التي سأرسلها.

لا تسأل أسئلة إلا إذا كان هناك نقص يمنع التنفيذ فعليًا. استخدم افتراضات منطقية قابلة للتعديل، ووثق هذه الافتراضات.

لا تنفذ جميع الأدوات الممكنة قبل إنهاء أساس المنصة.

الأولوية هي:

> معمارية صحيحة، أمان، قابلية توسع، تجربة مستخدم جيدة، وتوثيق يسمح لأي مطور بإكمال المشروع دون كسر بنيته.
