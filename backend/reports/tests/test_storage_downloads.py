"""Phase 5: storage abstraction + permission-checked downloads."""

from pathlib import Path

import pytest

from reports.models import GeneratedReport
from reports.shared.storage import DocumentStorage, document_storage

pytestmark = pytest.mark.django_db


@pytest.fixture
def eager(settings):
    settings.CELERY_TASK_ALWAYS_EAGER = True
    return settings


@pytest.fixture
def fake_pdf(monkeypatch):
    def _convert(self, docx_path, output_dir):
        pdf = Path(output_dir) / f"{Path(docx_path).stem}.pdf"
        pdf.write_bytes(b"%PDF-1.4 test")
        return pdf

    monkeypatch.setattr("reports.services.report_generation.LibreOfficePDFConverter.convert", _convert)


def _make_report(api, login, user, report_type, capture):
    login(user)
    payload = {
        "report_type_id": report_type.id,
        "title": "My Report",
        "input_data": {"organization_name": "Org", "visit_date": "2026-01-01", "notes": "N"},
    }
    with capture(execute=True):
        resp = api.post("/api/reports/", payload, format="json")
    return resp.json()["id"]


def test_owner_can_download_docx_and_pdf(
    api, normal_user, login, report_type, eager, fake_pdf, django_capture_on_commit_callbacks
):
    rid = _make_report(api, login, normal_user, report_type, django_capture_on_commit_callbacks)
    for kind in ("docx", "pdf"):
        resp = api.get(f"/api/reports/{rid}/download-{kind}/")
        assert resp.status_code == 200
        assert resp["Content-Disposition"].startswith("attachment")


def test_missing_file_returns_404(
    api, normal_user, login, report_type, eager, fake_pdf, django_capture_on_commit_callbacks
):
    rid = _make_report(api, login, normal_user, report_type, django_capture_on_commit_callbacks)
    report = GeneratedReport.objects.get(id=rid)
    document_storage.delete(report.pdf_file.name)  # simulate lost file
    resp = api.get(f"/api/reports/{rid}/download-pdf/")
    assert resp.status_code == 404


def test_storage_roundtrip_and_checksum():
    storage = DocumentStorage()
    name = "generated_reports/_test/sample.bin"
    saved = storage.save(name, b"hello-world")
    try:
        assert storage.exists(saved)
        assert storage.get_size(saved) == 11
        assert len(storage.get_checksum(saved)) == 64
        assert storage.open(saved).read() == b"hello-world"
    finally:
        storage.delete(saved)
    assert not storage.exists(saved)
