"""Phase 2: liveness/readiness probes."""

import pytest

pytestmark = pytest.mark.django_db


def test_liveness_ok(api):
    resp = api.get("/health/live")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_readiness_ok_when_db_reachable(api):
    resp = api.get("/health/ready")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ready"
    assert body["checks"]["database"] == "ok"


def test_health_endpoints_need_no_auth(api):
    # No credentials set; must still succeed.
    assert api.get("/health/live").status_code == 200
