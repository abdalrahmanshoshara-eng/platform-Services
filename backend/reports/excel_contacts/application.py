"""Excel Contacts processing use case and security boundary."""

import logging
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import PurePath

from reports.audit import actions
from reports.audit.service import record
from reports.models import Service
from reports.services_catalog.policy import service_access_for
from reports.shared.exceptions import DomainError

from .domain import normalize_country_code
from .processor import WorkbookValidationError, process_workbook

logger = logging.getLogger("reports.excel_contacts")

SERVICE_SLUG = "whatsapp-contacts"
MAX_FILE_SIZE = 10 * 1024 * 1024
ALLOWED_EXTENSIONS = {".xlsx", ".xls"}
XLSX_SIGNATURES = (b"PK\x03\x04", b"PK\x05\x06", b"PK\x07\x08")
XLS_SIGNATURE = b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1"


@dataclass(frozen=True)
class ExcelContactsOutput:
    file_name: str
    zip_buffer: bytes
    summary: dict
    source_sheet_name: str
    previews: dict


def _error(message: str, code: str, status_code: int) -> DomainError:
    return DomainError(message, code=code, status_code=status_code)


class ProcessExcelContactsUseCase:
    def execute(self, *, user, uploaded_file, country_code: str, request=None) -> ExcelContactsOutput:
        service = self._service()
        decision = service_access_for(user, service)
        if not decision.allowed:
            record(
                actions.SERVICE_EXECUTED,
                actor=user,
                request=request,
                target=service,
                outcome="denied",
                metadata={"service": service.slug, "reason_code": decision.code},
            )
            raise _error(decision.reason, "SERVICE_ACCESS_DENIED", 403)

        try:
            extension, data = self._validated_upload(uploaded_file)
            normalized_country_code = normalize_country_code(country_code)
            result = process_workbook(data, extension, uploaded_file.name, normalized_country_code)
        except ValueError as exc:
            self._record_failure(user, request, service, "INVALID_COUNTRY_CODE")
            raise _error(str(exc), "INVALID_COUNTRY_CODE", 400) from exc
        except WorkbookValidationError as exc:
            self._record_failure(user, request, service, "INVALID_WORKBOOK")
            raise _error(str(exc), "INVALID_WORKBOOK", 400) from exc
        except DomainError as exc:
            self._record_failure(user, request, service, exc.code)
            raise
        except Exception as exc:
            self._record_failure(user, request, service, "PROCESSING_FAILED")
            logger.exception("excel contacts processing failed")
            raise _error("تعذّرت معالجة ملف Excel.", "EXCEL_CONTACTS_PROCESSING_FAILED", 500) from exc

        record(
            actions.SERVICE_EXECUTED,
            actor=user,
            request=request,
            target=service,
            metadata={"service": service.slug, **result["summary"]},
        )
        timestamp = datetime.now(UTC).strftime("%Y-%m-%dT%H-%M-%S")
        return ExcelContactsOutput(
            file_name=f"contacts-output-{timestamp}.zip",
            zip_buffer=result["zip_buffer"],
            summary=result["summary"],
            source_sheet_name=result["source_sheet_name"],
            previews={
                "valid": result["valid_rows"][:10],
                "duplicate": result["duplicate_rows"][:10],
                "invalid": result["invalid_rows"][:10],
            },
        )

    @staticmethod
    def _service() -> Service:
        try:
            return Service.objects.select_related("category").get(slug=SERVICE_SLUG)
        except Service.DoesNotExist as exc:
            raise _error("الخدمة غير مهيأة حاليًا.", "SERVICE_NOT_CONFIGURED", 503) from exc

    @staticmethod
    def _validated_upload(uploaded_file) -> tuple[str, bytes]:
        filename = str(getattr(uploaded_file, "name", "") or "")
        extension = PurePath(filename).suffix.lower()
        if extension not in ALLOWED_EXTENSIONS:
            raise _error("الصيغ المدعومة هي .xlsx و .xls فقط.", "INVALID_FILE_EXTENSION", 400)
        size = int(getattr(uploaded_file, "size", 0) or 0)
        if size == 0:
            raise _error("الملف المرفوع فارغ.", "EMPTY_FILE", 400)
        if size > MAX_FILE_SIZE:
            raise _error("حجم الملف أكبر من الحد المسموح وهو 10 ميغابايت.", "FILE_TOO_LARGE", 413)

        data = uploaded_file.read(MAX_FILE_SIZE + 1)
        if not data:
            raise _error("الملف المرفوع فارغ.", "EMPTY_FILE", 400)
        if len(data) > MAX_FILE_SIZE:
            raise _error("حجم الملف أكبر من الحد المسموح وهو 10 ميغابايت.", "FILE_TOO_LARGE", 413)
        valid_signature = data.startswith(XLSX_SIGNATURES) if extension == ".xlsx" else data.startswith(XLS_SIGNATURE)
        if not valid_signature:
            raise _error("محتوى الملف لا يطابق صيغة Excel المحددة.", "INVALID_FILE_SIGNATURE", 400)
        return extension, data

    @staticmethod
    def _record_failure(user, request, service, reason_code):
        record(
            actions.SERVICE_EXECUTED,
            actor=user,
            request=request,
            target=service,
            outcome="failure",
            metadata={"service": service.slug, "reason_code": reason_code},
        )
