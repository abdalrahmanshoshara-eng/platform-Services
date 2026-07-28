"""Read queries for generated reports."""

from reports.models import GeneratedReport


def reports_for(user):
    queryset = GeneratedReport.objects.select_related("report_type", "created_by")
    if not user.is_staff:
        queryset = queryset.filter(created_by=user)
    return queryset.order_by("-created_at")
