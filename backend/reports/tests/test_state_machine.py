"""Phase 4: report generation state machine."""

import pytest

from reports.generation.domain import can_transition
from reports.models import GeneratedReport
from reports.shared.exceptions import InvalidStateTransition

S = GeneratedReport.Status


def test_allowed_and_forbidden_transitions():
    assert can_transition(S.PENDING, S.QUEUED)
    assert can_transition(S.QUEUED, S.PROCESSING)
    assert can_transition(S.PROCESSING, S.COMPLETED)
    assert can_transition(S.PROCESSING, S.QUEUED)  # retry
    assert not can_transition(S.COMPLETED, S.PROCESSING)
    assert not can_transition(S.FAILED, S.COMPLETED)


@pytest.mark.django_db
def test_transition_raises_on_invalid(report_type, normal_user):
    report = GeneratedReport.objects.create(
        report_type=report_type,
        created_by=normal_user,
        title="t",
        status=S.COMPLETED,
        input_data={},
    )
    from reports.generation.domain import transition

    with pytest.raises(InvalidStateTransition):
        transition(report, S.PROCESSING)
