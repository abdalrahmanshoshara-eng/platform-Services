"""Phase 3: unified API error model + correlation id."""

import pytest

pytestmark = pytest.mark.django_db


def test_unauthenticated_error_uses_unified_model(api):
    resp = api.get("/api/reports/")
    assert resp.status_code == 401
    body = resp.json()
    assert set(body) >= {"code", "message", "request_id"}
    assert body["code"] == "NOT_AUTHENTICATED"


def test_validation_error_uses_unified_model(api, admin_user, login):
    login(admin_user)
    resp = api.post("/api/report-types/", {"slug": "x"}, format="json")  # missing name/template
    assert resp.status_code == 400
    body = resp.json()
    assert body["code"] == "VALIDATION_ERROR"
    assert "request_id" in body


def test_correlation_id_header_present(api):
    resp = api.get("/health/live")
    assert resp.headers.get("X-Request-ID")


def test_incoming_request_id_is_echoed(api):
    resp = api.get("/health/live", HTTP_X_REQUEST_ID="abc123")
    assert resp.headers.get("X-Request-ID") == "abc123"
