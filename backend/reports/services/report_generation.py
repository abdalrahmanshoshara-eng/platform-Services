import tempfile
from pathlib import Path
from zoneinfo import ZoneInfo

from django.conf import settings
from django.utils import timezone
from docxtpl import DocxTemplate

from reports.models import GeneratedReport
from reports.shared.storage import document_storage

from .pdf_converter import LibreOfficePDFConverter


class ReportGenerationService:
    """Produces the DOCX + PDF for a report and persists them via DocumentStorage.

    `produce()` does the work and RAISES on failure; the Celery task owns status and
    sanitizes any error before persisting it (see generation/tasks.py), so raw
    exception text is never stored or returned to clients. LibreOffice needs real
    filesystem paths, so rendering happens in a temp dir; final persistence goes
    through the storage abstraction (no MEDIA_ROOT coupling in the persistence decision).
    """

    def __init__(self, report: GeneratedReport, storage=document_storage):
        self.report = report
        self.storage = storage

    def produce(self) -> tuple[str, str]:
        slug = self.report.report_type.slug
        rid = self.report.id
        with tempfile.TemporaryDirectory(prefix=f"report-{rid}-") as workdir:
            work = Path(workdir)
            docx_local = work / f"{slug}-{rid}.docx"

            document = DocxTemplate(str(self._template_path()))
            document.render(self._context(), autoescape=True)
            document.save(str(docx_local))

            pdf_local = LibreOfficePDFConverter().convert(docx_local, work)

            docx_name = self.storage.save(f"generated_reports/{rid}/{slug}-{rid}.docx", docx_local.read_bytes())
            pdf_name = self.storage.save(f"generated_reports/{rid}/{slug}-{rid}.pdf", pdf_local.read_bytes())
        return docx_name, pdf_name

    def _template_file_name(self) -> str:
        version = self.report.template_version
        return version.template_file if version else self.report.report_type.template_file

    def _template_path(self) -> Path:
        template_name = self._template_file_name()
        template_path = Path(settings.BASE_DIR) / "reports" / "templates" / "reports" / template_name
        if not template_path.exists():
            raise FileNotFoundError(f"Template file not found: {template_path}")
        return template_path

    def _context(self) -> dict:
        input_data = self.report.input_data or {}
        display_tz = ZoneInfo(getattr(settings, "REPORT_DISPLAY_TIMEZONE", "UTC"))
        context = {
            **input_data,
            "report_title": self.report.title,
            "report_type_name": self.report.report_type.name,
            "created_by": self.report.created_by.get_full_name() or self.report.created_by.username,
            "generated_at": timezone.localtime(timezone=display_tz).strftime("%Y-%m-%d %H:%M"),
        }
        return {key: "" if value is None else value for key, value in context.items()}
