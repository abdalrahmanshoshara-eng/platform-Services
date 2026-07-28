"""B22: stuck-report recovery goes through the state machine.
B14: the dead, unsafe ReportGenerationService.generate() is removed."""

from datetime import timedelta

import pytest
from django.core.management import call_command
from django.utils import timezone

from reports.models import GeneratedReport
from reports.services.report_generation import ReportGenerationService

pytestmark = pytest.mark.django_db


def _stuck_report(report_type, user, minutes_ago=60):
    return GeneratedReport.objects.create(
        created_by=user,
        report_type=report_type,
        title="stuck",
        input_data={},
        status=GeneratedReport.Status.PROCESSING,
        started_at=timezone.now() - timedelta(minutes=minutes_ago),
    )


def test_recover_requeues_stuck_report_via_state_machine(report_type, normal_user):
    report = _stuck_report(report_type, normal_user)
    call_command("recover_stuck_reports", "--minutes", "30")
    report.refresh_from_db()
    # processing -> failed -> queued, all through domain.transition()
    assert report.status == GeneratedReport.Status.QUEUED
    assert report.queued_at is not None


def test_recover_ignores_recent_processing_reports(report_type, normal_user):
    report = _stuck_report(report_type, normal_user, minutes_ago=5)
    call_command("recover_stuck_reports", "--minutes", "30")
    report.refresh_from_db()
    assert report.status == GeneratedReport.Status.PROCESSING


def test_unsafe_generate_wrapper_is_removed():
    # B14: only the raising producer remains; no status-managing wrapper that could
    # store raw exception text into a client-visible field.
    assert hasattr(ReportGenerationService, "produce")
    assert not hasattr(ReportGenerationService, "generate")
    assert not hasattr(ReportGenerationService, "_set_status")
