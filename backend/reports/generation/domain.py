"""Report generation state machine. The ONLY place status transitions are decided."""

from reports.models import GeneratedReport
from reports.shared.exceptions import InvalidStateTransition

S = GeneratedReport.Status

ALLOWED_TRANSITIONS = {
    S.PENDING: {S.QUEUED, S.PROCESSING, S.CANCELLED},
    S.QUEUED: {S.PROCESSING, S.CANCELLED, S.FAILED},
    S.PROCESSING: {S.COMPLETED, S.FAILED, S.CANCELLED, S.QUEUED},  # QUEUED = retry
    S.FAILED: {S.QUEUED, S.PROCESSING, S.CANCELLED},  # allow retry
    S.COMPLETED: set(),
    S.CANCELLED: set(),
}


def can_transition(current: str, target: str) -> bool:
    return target in ALLOWED_TRANSITIONS.get(current, set())


def transition(report: GeneratedReport, target: str, *, save: bool = True, extra_fields=None) -> None:
    if not can_transition(report.status, target):
        raise InvalidStateTransition(f"لا يمكن الانتقال من الحالة '{report.status}' إلى '{target}'.")
    report.status = target
    fields = ["status", "updated_at"]
    if extra_fields:
        fields += list(extra_fields)
    if save:
        report.save(update_fields=fields)
