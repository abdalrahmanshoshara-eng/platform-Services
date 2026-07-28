"""Template version lifecycle use cases (draft -> validated -> active)."""

import hashlib
from pathlib import Path

from django.conf import settings
from django.utils import timezone

from reports.models import ReportTemplateVersion
from reports.shared.exceptions import DomainError

from .placeholders import extract_template_placeholders, validate_template_against_schema
from .validation import validate_fields_schema


def _template_path(template_file: str) -> Path:
    return Path(settings.BASE_DIR) / "reports" / "templates" / "reports" / template_file


class ActivateTemplateVersionUseCase:
    """Validate schema + placeholders, compute checksum, and activate a version.

    Activation makes impactful fields immutable; editing requires a new version.
    Only one active version per report type.
    """

    def execute(self, *, version: ReportTemplateVersion) -> ReportTemplateVersion:
        S = ReportTemplateVersion.Status
        if version.status == S.ACTIVE:
            return version

        validate_fields_schema(version.fields_schema)
        path = _template_path(version.template_file)
        if not path.exists():
            raise DomainError("ملف القالب غير موجود.", code="TEMPLATE_FILE_MISSING", status_code=400)
        placeholders = extract_template_placeholders(path)
        validate_template_against_schema(placeholders, version.fields_schema)

        version.checksum = hashlib.sha256(path.read_bytes()).hexdigest()
        version.status = S.ACTIVE
        version.activated_at = timezone.now()
        version.save()

        ReportTemplateVersion.objects.filter(report_type=version.report_type, status=S.ACTIVE).exclude(
            pk=version.pk
        ).update(status=S.INACTIVE)
        return version
