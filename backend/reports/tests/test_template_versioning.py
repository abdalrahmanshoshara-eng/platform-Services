"""Phase 6: template versioning, validation, placeholders, and DOCX security."""

import io
import zipfile

import pytest

from reports.catalog.application import ActivateTemplateVersionUseCase
from reports.catalog.security import TemplateSecurityError, template_security_scanner
from reports.catalog.validation import (
    InputError,
    SchemaError,
    validate_fields_schema,
    validate_report_input,
)
from reports.models import ReportTemplateVersion
from reports.shared.exceptions import DomainError

pytestmark = pytest.mark.django_db

FIELD_VISIT_SCHEMA = [
    {"name": n, "type": "text"}
    for n in [
        "organization_name",
        "visit_date",
        "official_name",
        "location",
        "visit_goal",
        "notes",
        "recommendations",
        "prepared_by",
    ]
]

VALID_SCHEMA = [
    {"name": "organization_name", "type": "text", "required": True},
    {"name": "overall_rating", "type": "select", "required": True, "options": ["A", "B"]},
]


# ---- schema validation ----
def test_valid_schema_passes():
    assert validate_fields_schema(VALID_SCHEMA)


def test_duplicate_identifier_rejected():
    with pytest.raises(SchemaError):
        validate_fields_schema([{"name": "x", "type": "text"}, {"name": "x", "type": "text"}])


def test_select_without_options_rejected():
    with pytest.raises(SchemaError):
        validate_fields_schema([{"name": "x", "type": "select"}])


def test_unsupported_type_rejected():
    with pytest.raises(SchemaError):
        validate_fields_schema([{"name": "x", "type": "wizard"}])


# ---- input validation ----
def test_required_missing_rejected():
    with pytest.raises(InputError):
        validate_report_input(VALID_SCHEMA, {"overall_rating": "A"})


def test_unknown_field_rejected():
    with pytest.raises(InputError):
        validate_report_input(VALID_SCHEMA, {"organization_name": "O", "overall_rating": "A", "ghost": "1"})


def test_bad_select_value_rejected():
    with pytest.raises(InputError):
        validate_report_input(VALID_SCHEMA, {"organization_name": "O", "overall_rating": "Z"})


def test_valid_input_passes():
    assert validate_report_input(VALID_SCHEMA, {"organization_name": "O", "overall_rating": "A"})


# ---- versioning + activation ----
def test_activation_validates_and_makes_immutable(report_type):
    version = ReportTemplateVersion.objects.create(
        report_type=report_type,
        version=1,
        template_file="field_visit_template.docx",
        fields_schema=FIELD_VISIT_SCHEMA,
        status="draft",
    )
    ActivateTemplateVersionUseCase().execute(version=version)
    version.refresh_from_db()
    assert version.status == "active"
    assert len(version.checksum) == 64
    # impactful fields are now immutable
    version.template_file = "employee_evaluation_template.docx"
    with pytest.raises(DomainError):
        version.save()


def test_only_one_active_version(report_type):
    v1 = ReportTemplateVersion.objects.create(
        report_type=report_type,
        version=1,
        template_file="field_visit_template.docx",
        fields_schema=FIELD_VISIT_SCHEMA,
        status="draft",
    )
    ActivateTemplateVersionUseCase().execute(version=v1)
    v2 = ReportTemplateVersion.objects.create(
        report_type=report_type,
        version=2,
        template_file="field_visit_template.docx",
        fields_schema=FIELD_VISIT_SCHEMA,
        status="draft",
    )
    ActivateTemplateVersionUseCase().execute(version=v2)
    v1.refresh_from_db()
    assert v1.status == "inactive"


# ---- DOCX security scanner ----
def _docx_bytes(entries):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        for name, content in entries.items():
            z.writestr(name, content)
    return buf.getvalue()


def test_valid_docx_structure_passes():
    data = _docx_bytes({"[Content_Types].xml": "<x/>", "word/document.xml": "<x/>"})
    template_security_scanner.scan(filename="ok.docx", data=data)


def test_missing_required_entry_rejected():
    data = _docx_bytes({"word/document.xml": "<x/>"})
    with pytest.raises(TemplateSecurityError):
        template_security_scanner.scan(filename="bad.docx", data=data)


def test_macro_enabled_rejected():
    data = _docx_bytes({"[Content_Types].xml": "<x/>", "word/document.xml": "<x/>", "word/vbaProject.bin": "MZ"})
    with pytest.raises(TemplateSecurityError):
        template_security_scanner.scan(filename="macro.docx", data=data)


def test_bad_signature_rejected():
    with pytest.raises(TemplateSecurityError):
        template_security_scanner.scan(filename="fake.docx", data=b"not a zip at all")


def test_unsafe_filename_rejected():
    data = _docx_bytes({"[Content_Types].xml": "<x/>", "word/document.xml": "<x/>"})
    with pytest.raises(TemplateSecurityError):
        template_security_scanner.scan(filename="../evil.docx", data=data)
