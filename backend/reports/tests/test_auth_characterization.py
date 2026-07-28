"""Auth behavior after Phase 7 (HttpOnly cookie JWT + rotation + logout)."""

import pytest

pytestmark = pytest.mark.django_db


def test_login_sets_httponly_cookies_and_returns_user(api, normal_user):
    resp = api.post("/api/auth/login/", {"username": "user", "password": "pass12345"}, format="json")
    assert resp.status_code == 200
    body = resp.json()
    assert body["user"]["username"] == "user"
    # tokens are NOT in the body
    assert "access" not in body and "refresh" not in body
    access = resp.cookies.get("access_token")
    assert access is not None and access["httponly"]
    assert resp.cookies.get("refresh_token") is not None


def test_login_failure_wrong_password(api, normal_user):
    resp = api.post("/api/auth/login/", {"username": "user", "password": "wrong"}, format="json")
    assert resp.status_code == 400


def test_me_requires_auth(api):
    assert api.get("/api/auth/me/").status_code == 401


def test_me_returns_current_user_via_cookie(api, normal_user, login):
    login(normal_user)
    resp = api.get("/api/auth/me/")
    assert resp.status_code == 200
    assert resp.json()["username"] == "user"


def test_refresh_rotates_session(api, normal_user, login):
    login(normal_user)
    resp = api.post("/api/auth/refresh/")
    assert resp.status_code == 200
    assert resp.cookies.get("access_token") is not None


def test_logout_clears_cookies(api, normal_user, login):
    login(normal_user)
    resp = api.post("/api/auth/logout/")
    assert resp.status_code == 200
    # deleted cookies come back with an empty value / expiry in the past
    assert resp.cookies["access_token"].value == ""


def test_unauthorized_reports_list(api):
    assert api.get("/api/reports/").status_code == 401
