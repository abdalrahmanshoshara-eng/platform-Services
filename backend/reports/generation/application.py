"""Application use cases for report generation.

Write path: API View -> Input Serializer -> Use Case -> ORM + enqueue Celery task.
The HTTP request never waits for DOCX/PDF generation.
"""

from django.db import transaction
from django.utils import timezone

from reports.catalog.selectors import active_version
from reports.catalog.validation import validate_report_input
from reports.models import GeneratedReport
from reports.shared.correlation import get_correlation_id
from reports.shared.exceptions import DomainError

from .domain import transition
from .tasks import generate_report_task


class CreateReportUseCase:
    def execute(self, *, user, data) -> GeneratedReport:
        report_type = data["report_type"]
        version = active_version(report_type)
        if version is None:
            raise DomainError(
                "لا يوجد قالب نشط وصالح لهذا النوع من التقارير.",
                code="NO_ACTIVE_TEMPLATE",
                status_code=409,
            )
        schema = version.fields_schema
        input_data = validate_report_input(schema, data.get("input_data") or {})
        report = GeneratedReport.objects.create(
            created_by=user,
            report_type=report_type,
            template_version=version,
            title=(data.get("title") or "").strip() or report_type.name,
            input_data=input_data,
            status=GeneratedReport.Status.PENDING,
        )
        report.queued_at = timezone.now()
        transition(report, GeneratedReport.Status.QUEUED, extra_fields=["queued_at"])

        correlation_id = get_correlation_id()
        # Enqueue only after the DB row is committed (avoids race with the worker).
        transaction.on_commit(lambda: generate_report_task.delay(report.id, correlation_id))
        return report


class RetryReportUseCase:
    """Re-queue a failed report (idempotent, guarded by the state machine)."""

    def execute(self, *, report: GeneratedReport) -> GeneratedReport:
        report.queued_at = timezone.now()
        transition(report, GeneratedReport.Status.QUEUED, extra_fields=["queued_at"])
        correlation_id = get_correlation_id()
        transaction.on_commit(lambda: generate_report_task.delay(report.id, correlation_id))
        return report
