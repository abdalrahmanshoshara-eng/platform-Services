"""B5: admin ReportType create/update must validate fields_schema."""

import pytest

from reports.models import ReportType

pytestmark = pytest.mark.django_db

URL = "/api/v1/admin/report-types/"


def test_patch_rejects_field_missing_name(api, admin_user, login, report_type):
    login(admin_user)
    resp = api.patch(
        f"{URL}{report_type.id}/",
        {"fields_schema": [{"type": "text"}]},
        format="json",
    )
    assert resp.status_code == 400
    assert resp.data["code"] == "INVALID_FIELDS_SCHEMA"


def test_patch_rejects_select_without_options(api, admin_user, login, report_type):
    login(admin_user)
    resp = api.patch(
        f"{URL}{report_type.id}/",
        {"fields_schema": [{"name": "choice", "type": "select"}]},
        format="json",
    )
    assert resp.status_code == 400
    assert resp.data["code"] == "INVALID_FIELDS_SCHEMA"


def test_patch_rejects_duplicate_field_names(api, admin_user, login, report_type):
    login(admin_user)
    resp = api.patch(
        f"{URL}{report_type.id}/",
        {"fields_schema": [{"name": "a", "type": "text"}, {"name": "a", "type": "text"}]},
        format="json",
    )
    assert resp.status_code == 400
    assert resp.data["code"] == "INVALID_FIELDS_SCHEMA"


def test_patch_accepts_valid_schema(api, admin_user, login, report_type):
    login(admin_user)
    schema = [
        {"name": "org", "label_ar": "الجهة", "type": "text", "required": True},
        {"name": "kind", "label_ar": "النوع", "type": "select", "options": ["a", "b"]},
    ]
    resp = api.patch(f"{URL}{report_type.id}/", {"fields_schema": schema}, format="json")
    assert resp.status_code == 200
    report_type.refresh_from_db()
    assert report_type.fields_schema == schema


def test_create_rejects_invalid_schema_and_persists_nothing(api, admin_user, login):
    login(admin_user)
    resp = api.post(
        URL,
        {
            "name": "New RT",
            "slug": "new-rt",
            "template_file": "t.docx",
            "fields_schema": [{"name": "dup"}, {"name": "dup"}],
        },
        format="json",
    )
    assert resp.status_code == 400
    assert resp.data["code"] == "INVALID_FIELDS_SCHEMA"
    assert not ReportType.objects.filter(slug="new-rt").exists()
