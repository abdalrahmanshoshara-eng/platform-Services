"""Backfill: create an active v1 template version per report type and link reports."""
import hashlib
from pathlib import Path

from django.conf import settings
from django.db import migrations
from django.utils import timezone


def _checksum(template_file: str) -> str:
    if not template_file:
        return ""
    path = Path(settings.BASE_DIR) / "reports" / "templates" / "reports" / template_file
    if not path.exists():
        return ""
    sha = hashlib.sha256()
    sha.update(path.read_bytes())
    return sha.hexdigest()


def forwards(apps, schema_editor):
    ReportType = apps.get_model("reports", "ReportType")
    ReportTemplateVersion = apps.get_model("reports", "ReportTemplateVersion")
    GeneratedReport = apps.get_model("reports", "GeneratedReport")

    for report_type in ReportType.objects.all():
        version, _ = ReportTemplateVersion.objects.get_or_create(
            report_type=report_type,
            version=1,
            defaults={
                "template_file": report_type.template_file,
                "fields_schema": report_type.fields_schema or [],
                "checksum": _checksum(report_type.template_file),
                "status": "active",
                "activated_at": timezone.now(),
            },
        )
        GeneratedReport.objects.filter(
            report_type=report_type, template_version__isnull=True
        ).update(template_version=version)


def backwards(apps, schema_editor):
    GeneratedReport = apps.get_model("reports", "GeneratedReport")
    ReportTemplateVersion = apps.get_model("reports", "ReportTemplateVersion")
    GeneratedReport.objects.update(template_version=None)
    ReportTemplateVersion.objects.filter(version=1).delete()


class Migration(migrations.Migration):
    dependencies = [("reports", "0003_template_versioning")]
    operations = [migrations.RunPython(forwards, backwards)]
