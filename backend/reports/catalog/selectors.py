"""Read queries for the report catalog module."""

from reports.models import ReportType


def visible_report_types(user):
    queryset = ReportType.objects.all()
    if not user.is_staff:
        queryset = queryset.filter(is_active=True)
    return queryset.order_by("name")


def active_version(report_type):
    """Return the active template version for a report type, or None."""
    from reports.models import ReportTemplateVersion

    return (
        report_type.versions.filter(
            status=ReportTemplateVersion.Status.ACTIVE,
        )
        .exclude(checksum="")
        .order_by("-version")
        .first()
    )
