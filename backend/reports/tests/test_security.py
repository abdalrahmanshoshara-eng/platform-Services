"""Phase 7: audit log, login throttling, and production safety checks."""

import pytest
from django.core.cache import cache

from reports.accounts.throttling import LoginRateThrottle
from reports.audit import actions
from reports.models import AuditEvent

pytestmark = pytest.mark.django_db


def test_login_success_is_audited(api, normal_user, login):
    login(normal_user)
    assert AuditEvent.objects.filter(action=actions.LOGIN_SUCCESS, actor=normal_user).exists()


def test_login_failure_is_audited(api, normal_user):
    api.post("/api/auth/login/", {"username": "user", "password": "nope"}, format="json")
    event = AuditEvent.objects.filter(action=actions.LOGIN_FAILURE).first()
    assert event is not None and event.outcome == "failure"
    # no password stored anywhere in the audit record
    assert "nope" not in str(event.metadata)


def test_audit_record_never_stores_tokens(api, normal_user, login):
    login(normal_user)
    for event in AuditEvent.objects.all():
        blob = f"{event.metadata}"
        assert "access_token" not in blob and "refresh" not in blob


def test_login_throttle_blocks_after_limit(rf):
    cache.clear()
    throttle = LoginRateThrottle()
    throttle.rate = "2/min"
    throttle.num_requests, throttle.duration = throttle.parse_rate(throttle.rate)
    request = rf.post("/api/auth/login/")
    request.META["REMOTE_ADDR"] = "10.0.0.9"
    assert throttle.allow_request(request, None) is True
    assert throttle.allow_request(request, None) is True
    assert throttle.allow_request(request, None) is False  # 3rd blocked


def test_production_checks_flag_insecure_config(settings):
    settings.DEBUG = False
    settings.SECRET_KEY = "change-me"
    from reports.checks import production_safety_checks

    ids = {e.id for e in production_safety_checks(None)}
    assert "reports.E001" in ids
