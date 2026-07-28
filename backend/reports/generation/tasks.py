"""Background report generation. PostgreSQL is the source of truth for state."""

import logging

from celery import shared_task
from django.conf import settings
from django.db import transaction
from django.utils import timezone

from reports.audit import actions
from reports.audit.service import record
from reports.models import GeneratedReport
from reports.services.report_generation import ReportGenerationService
from reports.shared.correlation import set_correlation_id

from .domain import transition

logger = logging.getLogger("reports.generation")

S = GeneratedReport.Status


@shared_task(bind=True, acks_late=True)
def generate_report_task(self, report_id: int, correlation_id: str | None = None):
    if correlation_id:
        set_correlation_id(correlation_id)

    # Lock the row; enforce idempotency + duplicate-execution protection.
    with transaction.atomic():
        report = GeneratedReport.objects.select_for_update().filter(pk=report_id).first()
        if report is None:
            logger.warning("generate_report_task: report %s missing", report_id)
            return "missing"
        if report.status == S.COMPLETED:
            return "already_completed"
        if report.status == S.PROCESSING:
            return "already_processing"
        report.attempts = (report.attempts or 0) + 1
        report.started_at = timezone.now()
        report.task_id = getattr(self.request, "id", "") or ""
        transition(report, S.PROCESSING, extra_fields=["attempts", "started_at", "task_id"])

    try:
        docx_rel, pdf_rel = ReportGenerationService(report).produce()
    except Exception:  # noqa: BLE001
        logger.exception("report generation failed for report_id=%s", report_id)
        max_attempts = getattr(settings, "REPORT_MAX_ATTEMPTS", 3)
        if report.attempts < max_attempts:
            # Re-queue with exponential backoff (state machine allows PROCESSING->QUEUED).
            report.error_message = ""
            transition(report, S.QUEUED, extra_fields=["error_message"])
            countdown = min(2**report.attempts, 60)
            generate_report_task.apply_async(args=[report_id, correlation_id], countdown=countdown)
            return "retry_scheduled"
        report.error_message = "تعذّر إنشاء التقرير. يرجى المحاولة لاحقاً."
        report.finished_at = timezone.now()
        transition(report, S.FAILED, extra_fields=["error_message", "finished_at"])
        return "failed"

    report.docx_file.name = docx_rel
    report.pdf_file.name = pdf_rel
    report.error_message = ""
    report.finished_at = timezone.now()
    transition(
        report,
        S.COMPLETED,
        extra_fields=["docx_file", "pdf_file", "error_message", "finished_at"],
    )
    record(actions.GENERATION_COMPLETED, actor=report.created_by, target=report)
    return "completed"
