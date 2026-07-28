import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from reports.models import ReportType, Service, ServiceCategory

FIELD_VISIT_FIELDS = [
    {"name": "organization_name", "label_ar": "اسم الجهة", "type": "text", "required": True},
    {"name": "visit_date", "label_ar": "تاريخ الزيارة", "type": "date", "required": True},
    {"name": "official_name", "label_ar": "اسم المسؤول", "type": "text", "required": True},
    {"name": "location", "label_ar": "الموقع", "type": "text", "required": True},
    {"name": "visit_goal", "label_ar": "الهدف من الزيارة", "type": "textarea", "required": True},
    {"name": "notes", "label_ar": "الملاحظات", "type": "textarea", "required": True},
    {"name": "recommendations", "label_ar": "التوصيات", "type": "textarea", "required": True},
    {"name": "prepared_by", "label_ar": "اسم معد التقرير", "type": "text", "required": True},
]

EMPLOYEE_EVALUATION_FIELDS = [
    {"name": "employee_name", "label_ar": "اسم الموظف", "type": "text", "required": True},
    {"name": "department", "label_ar": "القسم", "type": "text", "required": True},
    {"name": "evaluation_date", "label_ar": "تاريخ التقييم", "type": "date", "required": True},
    {"name": "evaluator", "label_ar": "المقيم", "type": "text", "required": True},
    {"name": "strengths", "label_ar": "نقاط القوة", "type": "textarea", "required": True},
    {"name": "improvement_points", "label_ar": "نقاط التحسين", "type": "textarea", "required": True},
    {
        "name": "overall_rating",
        "label_ar": "التقييم العام",
        "type": "select",
        "required": True,
        "options": ["ممتاز", "جيد جداً", "جيد", "بحاجة إلى تحسين"],
    },
    {"name": "recommendations", "label_ar": "التوصيات", "type": "textarea", "required": True},
]


class Command(BaseCommand):
    help = "Create initial admin/user accounts and MVP report types."

    def handle(self, *args, **options):
        User = get_user_model()

        admin_username = os.getenv("ADMIN_USERNAME", "admin")
        admin_email = os.getenv("ADMIN_EMAIL", "admin@example.com")
        admin_password = os.getenv("ADMIN_PASSWORD", "admin123456")

        normal_username = os.getenv("NORMAL_USERNAME", "user")
        normal_email = os.getenv("NORMAL_EMAIL", "user@example.com")
        normal_password = os.getenv("NORMAL_PASSWORD", "user123456")

        admin, created = User.objects.get_or_create(username=admin_username, defaults={"email": admin_email})
        if created:
            admin.set_password(admin_password)
            admin.is_staff = True
            admin.is_superuser = True
            admin.save()
            self.stdout.write(self.style.SUCCESS(f"Created admin user: {admin_username}"))
        else:
            changed = False
            if not admin.is_staff or not admin.is_superuser:
                admin.is_staff = True
                admin.is_superuser = True
                changed = True
            if admin.email != admin_email:
                admin.email = admin_email
                changed = True
            if changed:
                admin.save()
            self.stdout.write(f"Admin user already exists: {admin_username}")

        normal, created = User.objects.get_or_create(username=normal_username, defaults={"email": normal_email})
        if created:
            normal.set_password(normal_password)
            normal.save()
            self.stdout.write(self.style.SUCCESS(f"Created normal user: {normal_username}"))
        else:
            self.stdout.write(f"Normal user already exists: {normal_username}")

        report_types = [
            {
                "slug": "field-visit",
                "name": "تقرير زيارة ميدانية",
                "description": "قالب عربي منسق لتوثيق الزيارات الميدانية والملاحظات والتوصيات.",
                "template_file": "field_visit_template.docx",
                "fields_schema": FIELD_VISIT_FIELDS,
            },
            {
                "slug": "employee-evaluation",
                "name": "تقرير تقييم موظف",
                "description": "قالب لتقييم الموظفين وتوثيق نقاط القوة والتحسين والتوصيات.",
                "template_file": "employee_evaluation_template.docx",
                "fields_schema": EMPLOYEE_EVALUATION_FIELDS,
            },
        ]

        for item in report_types:
            report_type, created = ReportType.objects.update_or_create(
                slug=item["slug"],
                defaults={**item, "is_active": True},
            )
            action = "Created" if created else "Updated"
            self.stdout.write(self.style.SUCCESS(f"{action} report type: {report_type.name}"))

        productivity, _ = ServiceCategory.objects.update_or_create(
            slug="productivity",
            defaults={
                "name": "الإنتاجية والمستندات",
                "description": "أدوات تجهيز البيانات والتقارير والمستندات الرسمية.",
                "icon": "briefcase",
                "sort_order": 10,
                "is_active": True,
            },
        )
        identity, _ = ServiceCategory.objects.update_or_create(
            slug="digital-identity",
            defaults={
                "name": "الهوية الرقمية",
                "description": "خدمات البطاقات والتعريف المهني.",
                "icon": "badge",
                "sort_order": 20,
                "is_active": True,
            },
        )

        services = [
            {
                "slug": "professional-reports",
                "category": productivity,
                "name": "التقارير الاحترافية",
                "description": "إنشاء تقارير Word وPDF من قوالب عربية معتمدة ومتابعة سجل الملفات.",
                "kind": Service.Kind.INTERNAL,
                "launch_target": "/reports/new",
                "icon": "file-text",
                "accent": "green",
                "sort_order": 10,
            },
            {
                "slug": "whatsapp-contacts",
                "category": productivity,
                "name": "تهيئة جهات الاتصال",
                "description": "تنظيف ملف Excel ودمج المكررات وإنتاج ملف VCF جاهز للاستيراد.",
                "kind": Service.Kind.INTERNAL,
                "launch_target": "/tools/excel-contacts",
                "icon": "sheet",
                "accent": "teal",
                "sort_order": 20,
            },
            {
                "slug": "business-cards",
                "category": identity,
                "name": "منصة بطاقات الأعمال",
                "description": "الدخول إلى منصة البطاقات الرقمية وإدارة بيانات البطاقة المهنية.",
                "kind": Service.Kind.EXTERNAL,
                "launch_target": os.getenv("CARDNEST_URL", "https://cardnest.moid.gov.sy/login"),
                "icon": "contact",
                "accent": "gold",
                "sort_order": 10,
            },
        ]
        for item in services:
            service, created = Service.objects.update_or_create(
                slug=item["slug"],
                defaults={**item, "is_active": True},
            )
            action = "Created" if created else "Updated"
            self.stdout.write(self.style.SUCCESS(f"{action} service: {service.name}"))
