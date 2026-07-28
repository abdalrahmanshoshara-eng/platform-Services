"""Read-only aggregated statistics for the dashboard."""

from django.db.models import Count
from django.utils import timezone

from reports.generation.selectors import reports_for
from reports.models import GeneratedReport, ReportType


def dashboard_statistics(user):
    reports = reports_for(user)
    today = timezone.localdate()
    status_counts = dict(reports.values_list("status").annotate(count=Count("id")))
    return {
        "total_reports": reports.count(),
        "today_reports": reports.filter(created_at__date=today).count(),
        "report_types": ReportType.objects.filter(is_active=True).count(),
        "completed_reports": status_counts.get(GeneratedReport.Status.COMPLETED, 0),
        "failed_reports": status_counts.get(GeneratedReport.Status.FAILED, 0),
        "latest_reports": reports.order_by("-created_at")[:5],
    }
