"""Report creation + ASYNC generation (Phase 4).

Uses Celery eager mode + captured on_commit callbacks so the enqueued task runs
inline within tests. LibreOffice PDF conversion is patched; DOCX render is real.
"""

from pathlib import Path

import pytest

from reports.models import GeneratedReport

pytestmark = pytest.mark.django_db


@pytest.fixture
def eager(settings):
    settings.CELERY_TASK_ALWAYS_EAGER = True
    settings.CELERY_TASK_EAGER_PROPAGATES = False
    return settings


@pytest.fixture
def fake_pdf(monkeypatch):
    def _convert(self, docx_path, output_dir):
        pdf = Path(output_dir) / f"{Path(docx_path).stem}.pdf"
        pdf.write_bytes(b"%PDF-1.4 test")
        return pdf

    monkeypatch.setattr("reports.services.report_generation.LibreOfficePDFConverter.convert", _convert)


def _payload(report_type):
    return {
        "report_type_id": report_type.id,
        "title": "Test Report",
        "input_data": {"organization_name": "Org", "visit_date": "2026-01-01", "notes": "N"},
    }


def test_create_returns_202_queued_without_waiting(api, normal_user, login, report_type):
    login(normal_user)
    resp = api.post("/api/reports/", _payload(report_type), format="json")
    assert resp.status_code == 202, resp.content
    body = resp.json()
    assert body["status"] in {"pending", "queued"}
    assert body["docx_file"] is None and body["pdf_file"] is None


def test_generation_completes_when_task_runs(
    api, normal_user, login, report_type, eager, fake_pdf, django_capture_on_commit_callbacks
):
    login(normal_user)
    with django_capture_on_commit_callbacks(execute=True):
        resp = api.post("/api/reports/", _payload(report_type), format="json")
    report_id = resp.json()["id"]
    report = GeneratedReport.objects.get(id=report_id)
    assert report.status == "completed"
    assert report.docx_file and report.pdf_file
    assert report.attempts == 1


def test_polling_status_endpoint(
    api, normal_user, login, report_type, eager, fake_pdf, django_capture_on_commit_callbacks
):
    login(normal_user)
    with django_capture_on_commit_callbacks(execute=True):
        created = api.post("/api/reports/", _payload(report_type), format="json").json()
    resp = api.get(f"/api/reports/{created['id']}/status/")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "completed"
    assert body["download_pdf_url"]


def test_generation_marks_failed_after_max_attempts(
    api, normal_user, login, report_type, eager, fake_pdf, django_capture_on_commit_callbacks
):
    # Generation reads the immutable version snapshot, never ReportType.template_file.
    report_type.versions.filter(status="active").update(template_file="does_not_exist.docx")
    login(normal_user)
    with django_capture_on_commit_callbacks(execute=True):
        created = api.post("/api/reports/", _payload(report_type), format="json").json()
    report = GeneratedReport.objects.get(id=created["id"])
    assert report.status == "failed"
    assert report.attempts >= 1
    # user-facing message is safe (no path/traceback leak)
    assert "does_not_exist" not in report.error_message


def test_missing_required_field_rejected(api, normal_user, login, report_type):
    login(normal_user)
    payload = _payload(report_type)
    payload["input_data"].pop("notes")
    resp = api.post("/api/reports/", payload, format="json")
    assert resp.status_code == 400


def test_user_sees_only_own_reports(api, normal_user, other_user, login, report_type):
    login(normal_user)
    api.post("/api/reports/", _payload(report_type), format="json")
    login(other_user)
    resp = api.get("/api/reports/")
    assert resp.status_code == 200
    assert resp.json()["count"] == 0


def test_unauthorized_download_blocked(api, normal_user, other_user, login, report_type):
    login(normal_user)
    created = api.post("/api/reports/", _payload(report_type), format="json").json()
    login(other_user)
    resp = api.get(f"/api/reports/{created['id']}/download-docx/")
    assert resp.status_code in (403, 404)
