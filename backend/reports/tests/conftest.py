import hashlib

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from reports.models import ReportTemplateVersion, ReportType
from reports.services.template_storage import template_storage

FIELD_VISIT_FIELDS = [
    {"name": "organization_name", "label_ar": "اسم الجهة", "type": "text", "required": True},
    {"name": "visit_date", "label_ar": "تاريخ الزيارة", "type": "date", "required": True},
    {"name": "notes", "label_ar": "الملاحظات", "type": "textarea", "required": True},
]


@pytest.fixture
def api():
    return APIClient()


@pytest.fixture
def admin_user(db):
    User = get_user_model()
    return User.objects.create_user(username="admin", password="pass12345", is_staff=True, is_superuser=True)


@pytest.fixture
def normal_user(db):
    User = get_user_model()
    return User.objects.create_user(username="user", password="pass12345")


@pytest.fixture
def other_user(db):
    User = get_user_model()
    return User.objects.create_user(username="other", password="pass12345")


@pytest.fixture
def report_type(db):
    report_type = ReportType.objects.create(
        name="Field Visit",
        slug="field-visit",
        description="test",
        template_file="field_visit_template.docx",
        fields_schema=FIELD_VISIT_FIELDS,
        is_active=True,
    )
    template_data = template_storage.read(report_type.template_file)
    ReportTemplateVersion.objects.create(
        report_type=report_type,
        version=1,
        template_file=report_type.template_file,
        fields_schema=report_type.fields_schema,
        checksum=hashlib.sha256(template_data).hexdigest(),
        status=ReportTemplateVersion.Status.ACTIVE,
    )
    return report_type


@pytest.fixture
def inactive_report_type(db):
    return ReportType.objects.create(
        name="Archived",
        slug="archived",
        template_file="field_visit_template.docx",
        fields_schema=[],
        is_active=False,
    )


@pytest.fixture
def login(api):
    def _login(user, password="pass12345"):
        # Cookie auth: APIClient persists the HttpOnly cookies across requests.
        return api.post(
            "/api/auth/login/",
            {"username": user.username, "password": password},
            format="json",
        )

    return _login
