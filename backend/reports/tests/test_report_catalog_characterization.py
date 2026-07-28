"""Characterization tests: report-type catalog behavior."""

import pytest

pytestmark = pytest.mark.django_db


def test_normal_user_sees_only_active_types(api, normal_user, login, report_type, inactive_report_type):
    login(normal_user)
    resp = api.get("/api/report-types/")
    assert resp.status_code == 200
    slugs = {rt["slug"] for rt in resp.json()}
    assert "field-visit" in slugs
    assert "archived" not in slugs


def test_admin_sees_all_types(api, admin_user, login, report_type, inactive_report_type):
    login(admin_user)
    resp = api.get("/api/report-types/")
    slugs = {rt["slug"] for rt in resp.json()}
    assert {"field-visit", "archived"} <= slugs


def test_normal_user_cannot_create_type(api, normal_user, login):
    login(normal_user)
    resp = api.post("/api/report-types/", {"name": "X", "slug": "x", "template_file": "t.docx"}, format="json")
    assert resp.status_code == 403


def test_admin_can_create_type(api, admin_user, login):
    login(admin_user)
    resp = api.post(
        "/api/report-types/",
        {"name": "New", "slug": "new", "template_file": "field_visit_template.docx", "fields_schema": []},
        format="json",
    )
    assert resp.status_code == 201
