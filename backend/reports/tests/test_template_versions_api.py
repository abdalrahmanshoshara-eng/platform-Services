from io import BytesIO
from zipfile import ZIP_DEFLATED, ZipFile

import pytest
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import IntegrityError, transaction
from django.test import override_settings
from docx import Document
from rest_framework.test import APIClient

from reports.catalog.application import CreateTemplateVersionUseCase
from reports.catalog.security import template_security_scanner
from reports.generation.application import CreateReportUseCase
from reports.models import AuditEvent, GeneratedReport, ReportTemplateVersion, ReportType
from reports.shared.exceptions import DomainError

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def isolated_template_storage(settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path


@pytest.fixture
def user():
    return get_user_model().objects.create_user(
        username="template-user",
        password="pass12345",
    )


@pytest.fixture
def report_type():
    return ReportType.objects.create(
        name="Template API report",
        slug="template-api-report",
        template_file="field_visit_template.docx",
        fields_schema=[
            {
                "name": "organization_name",
                "label_ar": "الجهة",
                "type": "text",
                "required": True,
            }
        ],
        is_active=True,
    )


def _docx_bytes(*paragraphs: str) -> bytes:
    document = Document()
    for paragraph in paragraphs:
        document.add_paragraph(paragraph)
    output = BytesIO()
    document.save(output)
    return output.getvalue()


def _unsafe_docx_bytes() -> bytes:
    output = BytesIO()
    with ZipFile(output, "w", ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", "<Types/>")
        archive.writestr("_rels/.rels", "<Relationships/>")
        archive.writestr("word/document.xml", "<document/>")
        archive.writestr("word/vbaProject.bin", b"macro")
    return output.getvalue()


def _upload(client: APIClient, report_type_id: int, content: bytes, name="template.docx"):
    return client.post(
        f"/api/v1/admin/report-types/{report_type_id}/template-versions/",
        {
            "template_file": SimpleUploadedFile(
                name,
                content,
                content_type=("application/vnd.openxmlformats-officedocument." "wordprocessingml.document"),
            )
        },
        format="multipart",
    )


def _action(client, report_type_id, version_id, action, reason="B6 test"):
    return client.post(
        (f"/api/v1/admin/report-types/{report_type_id}/template-versions/" f"{version_id}/{action}/"),
        {"reason": reason},
        format="json",
    )


def test_ordinary_user_cannot_list_template_versions(user, report_type):
    client = APIClient()
    client.force_authenticate(user)

    response = client.get(f"/api/v1/admin/report-types/{report_type.id}/template-versions/")

    assert response.status_code == 403


def test_ordinary_user_cannot_create_retrieve_or_change_template_versions(user, report_type):
    version = ReportTemplateVersion.objects.create(
        report_type=report_type,
        version=1,
        template_file="field_visit_template.docx",
        fields_schema=report_type.fields_schema,
    )
    client = APIClient()
    client.force_authenticate(user)
    base = f"/api/v1/admin/report-types/{report_type.id}/template-versions/"

    responses = [
        _upload(client, report_type.id, _docx_bytes("{{ organization_name }}")),
        client.get(f"{base}{version.id}/"),
        client.post(f"{base}{version.id}/validate/", {}, format="json"),
        client.post(f"{base}{version.id}/activate/", {}, format="json"),
        client.post(f"{base}{version.id}/deactivate/", {}, format="json"),
        client.post(f"{base}{version.id}/archive/", {}, format="json"),
    ]

    assert {response.status_code for response in responses} == {403}


def test_admin_can_upload_valid_template_as_non_active_version(admin_user, report_type):
    client = APIClient()
    client.force_authenticate(admin_user)

    response = _upload(
        client,
        report_type.id,
        _docx_bytes("{{ organization_name }}"),
    )

    assert response.status_code == 201
    assert response.data["status"] == "draft"
    assert response.data["version"] == 1
    assert "template_file" not in response.data


@pytest.mark.parametrize(
    "kind",
    [
        "corrupt",
        "wrong-extension",
        "macro",
    ],
)
def test_admin_upload_rejects_invalid_or_unsafe_files_safely(admin_user, report_type, kind):
    client = APIClient()
    client.force_authenticate(admin_user)
    cases = {
        "corrupt": ("template.docx", b"not a zip"),
        "wrong-extension": (
            "template.txt",
            _docx_bytes("{{ organization_name }}"),
        ),
        "macro": ("template.docx", _unsafe_docx_bytes()),
    }
    name, content = cases[kind]

    response = _upload(client, report_type.id, content, name)

    assert response.status_code == 400
    assert "traceback" not in str(response.data).lower()
    assert "exception" not in str(response.data).lower()


@override_settings(TEMPLATE_MAX_UPLOAD_BYTES=128)
def test_admin_upload_rejects_oversized_template(admin_user, report_type):
    client = APIClient()
    client.force_authenticate(admin_user)

    response = _upload(client, report_type.id, _docx_bytes("x" * 2048))

    assert response.status_code == 400


def test_validate_activate_deactivate_archive_lifecycle_is_audited(admin_user, report_type):
    client = APIClient()
    client.force_authenticate(admin_user)
    uploaded = _upload(
        client,
        report_type.id,
        _docx_bytes("{{ organization_name }}"),
    )
    version_id = uploaded.data["id"]

    validated = _action(client, report_type.id, version_id, "validate")
    assert validated.status_code == 200
    assert validated.data["status"] == "validated"
    assert len(validated.data["checksum"]) == 64

    activated = _action(client, report_type.id, version_id, "activate")
    assert activated.status_code == 200
    assert activated.data["status"] == "active"
    assert activated.data["activated_at"]

    repeated = _action(client, report_type.id, version_id, "activate")
    assert repeated.status_code == 200
    assert repeated.data["status"] == "active"

    blocked_archive = _action(client, report_type.id, version_id, "archive")
    assert blocked_archive.status_code == 409

    deactivated = _action(client, report_type.id, version_id, "deactivate")
    assert deactivated.status_code == 200
    assert deactivated.data["status"] == "inactive"

    archived = _action(client, report_type.id, version_id, "archive")
    assert archived.status_code == 200
    assert archived.data["status"] == "archived"

    actions = set(AuditEvent.objects.filter(target_id=str(version_id)).values_list("action", flat=True))
    assert {
        "template.uploaded",
        "template.validated",
        "template.activated",
        "template.deactivated",
        "template.archived",
    }.issubset(actions)


def test_unvalidated_or_mismatched_template_cannot_be_activated(admin_user, report_type):
    client = APIClient()
    client.force_authenticate(admin_user)
    uploaded = _upload(
        client,
        report_type.id,
        _docx_bytes("{{ unknown_placeholder }}"),
    )
    version_id = uploaded.data["id"]

    activation = _action(client, report_type.id, version_id, "activate")
    validation = _action(client, report_type.id, version_id, "validate")

    assert activation.status_code == 409
    assert validation.status_code == 400
    assert "unknown_placeholder" in str(validation.data)
    assert ReportTemplateVersion.objects.get(pk=version_id).status == "draft"


def test_activation_retires_previous_version_and_preserves_report_link(admin_user, report_type):
    client = APIClient()
    client.force_authenticate(admin_user)

    first = _upload(
        client,
        report_type.id,
        _docx_bytes("{{ organization_name }}"),
    ).data
    _action(client, report_type.id, first["id"], "validate")
    _action(client, report_type.id, first["id"], "activate")
    historical_report = GeneratedReport.objects.create(
        report_type=report_type,
        template_version_id=first["id"],
        created_by=admin_user,
        title="Historical",
        input_data={"organization_name": "A"},
    )

    second = _upload(
        client,
        report_type.id,
        _docx_bytes("{{ organization_name }}"),
    ).data
    _action(client, report_type.id, second["id"], "validate")
    response = _action(client, report_type.id, second["id"], "activate")

    assert response.status_code == 200
    assert ReportTemplateVersion.objects.get(pk=first["id"]).status == "inactive"
    assert (
        ReportTemplateVersion.objects.filter(
            report_type=report_type,
            status="active",
        ).count()
        == 1
    )
    historical_report.refresh_from_db()
    assert historical_report.template_version_id == first["id"]

    reactivated = _action(client, report_type.id, first["id"], "activate")
    assert reactivated.status_code == 200
    assert reactivated.data["status"] == "active"
    assert ReportTemplateVersion.objects.get(pk=second["id"]).status == "inactive"


def test_database_constraint_prevents_two_active_versions(report_type):
    ReportTemplateVersion.objects.create(
        report_type=report_type,
        version=1,
        template_file="field_visit_template.docx",
        fields_schema=report_type.fields_schema,
        checksum="a" * 64,
        status="active",
    )

    with pytest.raises(IntegrityError), transaction.atomic():
        ReportTemplateVersion.objects.create(
            report_type=report_type,
            version=2,
            template_file="field_visit_template.docx",
            fields_schema=report_type.fields_schema,
            checksum="b" * 64,
            status="active",
        )


def test_generic_patch_cannot_bypass_version_state_or_template_file(admin_user, report_type):
    client = APIClient()
    client.force_authenticate(admin_user)
    version = ReportTemplateVersion.objects.create(
        report_type=report_type,
        version=1,
        template_file="field_visit_template.docx",
        fields_schema=report_type.fields_schema,
    )

    version_response = client.patch(
        (f"/api/v1/admin/report-types/{report_type.id}/template-versions/" f"{version.id}/"),
        {"status": "active"},
        format="json",
    )
    type_response = client.patch(
        f"/api/v1/admin/report-types/{report_type.id}/",
        {"template_file": "attacker.docx"},
        format="json",
    )

    assert version_response.status_code == 405
    assert type_response.status_code == 200
    report_type.refresh_from_db()
    assert report_type.template_file == "field_visit_template.docx"


def test_no_active_template_returns_stable_error_and_creates_nothing(admin_user, report_type):
    with pytest.raises(DomainError) as caught:
        CreateReportUseCase().execute(
            user=admin_user,
            data={
                "report_type": report_type,
                "title": "No template",
                "input_data": {"organization_name": "A"},
            },
        )

    assert caught.value.code == "NO_ACTIVE_TEMPLATE"
    assert caught.value.status_code == 409
    assert GeneratedReport.objects.count() == 0


def test_archived_or_deactivated_versions_are_not_used_for_new_reports(admin_user, report_type):
    version = ReportTemplateVersion.objects.create(
        report_type=report_type,
        version=1,
        template_file="field_visit_template.docx",
        fields_schema=report_type.fields_schema,
        checksum="a" * 64,
        status="inactive",
    )

    with pytest.raises(DomainError) as inactive:
        CreateReportUseCase().execute(
            user=admin_user,
            data={
                "report_type": report_type,
                "input_data": {"organization_name": "A"},
            },
        )
    version.status = "archived"
    version.save(update_fields=["status"])
    with pytest.raises(DomainError) as archived:
        CreateReportUseCase().execute(
            user=admin_user,
            data={
                "report_type": report_type,
                "input_data": {"organization_name": "A"},
            },
        )

    assert inactive.value.code == archived.value.code == "NO_ACTIVE_TEMPLATE"


def test_new_report_snapshots_the_active_validated_version(admin_user, report_type):
    version = ReportTemplateVersion.objects.create(
        report_type=report_type,
        version=1,
        template_file="field_visit_template.docx",
        fields_schema=report_type.fields_schema,
        checksum="a" * 64,
        status="active",
    )

    report = CreateReportUseCase().execute(
        user=admin_user,
        data={
            "report_type": report_type,
            "title": "Snapshot",
            "input_data": {"organization_name": "A"},
        },
    )

    assert report.template_version_id == version.id


def test_failed_database_write_cleans_up_uploaded_blob(admin_user, report_type, monkeypatch, tmp_path):
    def fail_create(**kwargs):
        raise RuntimeError("database unavailable")

    monkeypatch.setattr(ReportTemplateVersion.objects, "create", fail_create)

    with pytest.raises(RuntimeError):
        CreateTemplateVersionUseCase().execute(
            report_type=report_type,
            actor=admin_user,
            filename="template.docx",
            data=_docx_bytes("{{ organization_name }}"),
        )

    assert list(tmp_path.rglob("*.docx")) == []


def test_unexpected_scanner_error_is_sanitized(admin_user, report_type, monkeypatch):
    client = APIClient()
    client.force_authenticate(admin_user)

    def fail_scan(**kwargs):
        raise RuntimeError("secret scanner internals")

    monkeypatch.setattr(template_security_scanner, "scan", fail_scan)
    response = _upload(
        client,
        report_type.id,
        _docx_bytes("{{ organization_name }}"),
    )

    assert response.status_code == 400
    assert response.data["code"] == "TEMPLATE_REJECTED"
    assert "secret scanner internals" not in str(response.data)
