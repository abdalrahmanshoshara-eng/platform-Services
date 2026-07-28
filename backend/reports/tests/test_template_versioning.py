"""Phase 6: template versioning, validation, placeholders, and DOCX security."""

import io
import zipfile

import pytest
from django.test import override_settings

from reports.catalog.application import (
    ActivateTemplateVersionUseCase,
    ValidateTemplateVersionUseCase,
)
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
        version=2,
        template_file="field_visit_template.docx",
        fields_schema=FIELD_VISIT_SCHEMA,
        status="draft",
    )
    ValidateTemplateVersionUseCase().execute(version=version)
    ActivateTemplateVersionUseCase().execute(version=version)
    version.refresh_from_db()
    assert version.status == "active"
    assert len(version.checksum) == 64
    # impactful fields are now immutable
    version.template_file = "employee_evaluation_template.docx"
    with pytest.raises(DomainError):
        version.save()


def test_only_one_active_version(report_type):
    v1 = report_type.versions.get(version=1)
    v2 = ReportTemplateVersion.objects.create(
        report_type=report_type,
        version=2,
        template_file="field_visit_template.docx",
        fields_schema=FIELD_VISIT_SCHEMA,
        status="draft",
    )
    ValidateTemplateVersionUseCase().execute(version=v2)
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
    data = _docx_bytes(
        {
            "[Content_Types].xml": "<x/>",
            "_rels/.rels": "<Relationships/>",
            "word/document.xml": "<x/>",
        }
    )
    template_security_scanner.scan(filename="ok.docx", data=data)


def test_missing_required_entry_rejected():
    data = _docx_bytes({"word/document.xml": "<x/>"})
    with pytest.raises(TemplateSecurityError):
        template_security_scanner.scan(filename="bad.docx", data=data)


def test_macro_enabled_rejected():
    data = _docx_bytes(
        {
            "[Content_Types].xml": "<x/>",
            "_rels/.rels": "<Relationships/>",
            "word/document.xml": "<x/>",
            "word/vbaProject.bin": "MZ",
        }
    )
    with pytest.raises(TemplateSecurityError):
        template_security_scanner.scan(filename="macro.docx", data=data)


def test_bad_signature_rejected():
    with pytest.raises(TemplateSecurityError):
        template_security_scanner.scan(filename="fake.docx", data=b"not a zip at all")


def test_unsafe_filename_rejected():
    data = _docx_bytes(
        {
            "[Content_Types].xml": "<x/>",
            "_rels/.rels": "<Relationships/>",
            "word/document.xml": "<x/>",
        }
    )
    with pytest.raises(TemplateSecurityError):
        template_security_scanner.scan(filename="../evil.docx", data=data)


def test_zip_traversal_entry_rejected():
    data = _docx_bytes(
        {
            "[Content_Types].xml": "<Types/>",
            "_rels/.rels": "<Relationships/>",
            "word/document.xml": "<document/>",
            "../escape.xml": "<x/>",
        }
    )
    with pytest.raises(TemplateSecurityError):
        template_security_scanner.scan(filename="traversal.docx", data=data)


def test_high_compression_zip_bomb_rejected():
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", "<Types/>")
        archive.writestr("_rels/.rels", "<Relationships/>")
        archive.writestr("word/document.xml", "<document/>")
        archive.writestr("word/media/bomb.txt", b"0" * (2 * 1024 * 1024))

    with pytest.raises(TemplateSecurityError):
        template_security_scanner.scan(filename="bomb.docx", data=buffer.getvalue())


@pytest.mark.parametrize(
    "extra_name",
    ["word/embeddings/object1.bin", "word/activeX/activeX1.xml", "payload.exe"],
)
def test_embedded_or_executable_content_rejected(extra_name):
    data = _docx_bytes(
        {
            "[Content_Types].xml": "<Types/>",
            "_rels/.rels": "<Relationships/>",
            "word/document.xml": "<document/>",
            extra_name: "payload",
        }
    )
    with pytest.raises(TemplateSecurityError):
        template_security_scanner.scan(filename="embedded.docx", data=data)


def test_external_relationship_rejected():
    data = _docx_bytes(
        {
            "[Content_Types].xml": "<Types/>",
            "_rels/.rels": (
                '<Relationships><Relationship TargetMode="External" ' 'Target="https://example.com"/></Relationships>'
            ),
            "word/document.xml": "<document/>",
        }
    )
    with pytest.raises(TemplateSecurityError):
        template_security_scanner.scan(filename="external.docx", data=data)


def test_xml_entity_rejected():
    data = _docx_bytes(
        {
            "[Content_Types].xml": "<Types/>",
            "_rels/.rels": "<Relationships/>",
            "word/document.xml": '<!DOCTYPE x [<!ENTITY e SYSTEM "file:///x">]><x/>',
        }
    )
    with pytest.raises(TemplateSecurityError):
        template_security_scanner.scan(filename="entity.docx", data=data)


@override_settings(TEMPLATE_MAX_ARCHIVE_ENTRIES=3)
def test_too_many_archive_entries_rejected():
    data = _docx_bytes(
        {
            "[Content_Types].xml": "<Types/>",
            "_rels/.rels": "<Relationships/>",
            "word/document.xml": "<document/>",
            "word/styles.xml": "<styles/>",
        }
    )
    with pytest.raises(TemplateSecurityError):
        template_security_scanner.scan(filename="many.docx", data=data)


@override_settings(TEMPLATE_MAX_XML_PART_BYTES=16)
def test_oversized_xml_part_rejected():
    data = _docx_bytes(
        {
            "[Content_Types].xml": "<Types/>",
            "_rels/.rels": "<Relationships/>",
            "word/document.xml": f"<document>{'x' * 128}</document>",
        }
    )
    with pytest.raises(TemplateSecurityError):
        template_security_scanner.scan(filename="large-xml.docx", data=data)
