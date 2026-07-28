"""Local structural security scanning for uploaded DOCX templates.

No external antivirus is used (documented deferred item). This performs structural
checks only. A future TemplateSecurityScanner backend can add AV integration
without changing callers.
"""

import zipfile

from reports.shared.exceptions import DomainError

DOCX_SIGNATURE = b"PK\x03\x04"
MAX_UPLOAD_BYTES = 10 * 1024 * 1024  # 10 MB
MAX_UNCOMPRESSED_BYTES = 100 * 1024 * 1024  # 100 MB
MAX_COMPRESSION_RATIO = 100
REQUIRED_ENTRIES = {"[Content_Types].xml", "word/document.xml"}
MACRO_MARKERS = ("word/vbaProject.bin",)


class TemplateSecurityError(DomainError):
    code = "TEMPLATE_REJECTED"
    status_code = 400
    message = "تم رفض ملف القالب."


class TemplateSecurityScanner:
    def scan(self, *, filename: str, data: bytes) -> None:
        self._check_filename(filename)
        self._check_size(data)
        self._check_signature(data)
        self._check_zip(data)

    def _reject(self, msg: str):
        raise TemplateSecurityError(msg)

    def _check_filename(self, filename: str):
        if not filename or "/" in filename or "\\" in filename or ".." in filename:
            self._reject("اسم ملف غير آمن.")
        if not filename.lower().endswith(".docx"):
            self._reject("امتداد غير مدعوم (المطلوب .docx).")

    def _check_size(self, data: bytes):
        if len(data) == 0:
            self._reject("ملف فارغ.")
        if len(data) > MAX_UPLOAD_BYTES:
            self._reject("حجم الملف يتجاوز الحد المسموح.")

    def _check_signature(self, data: bytes):
        if not data.startswith(DOCX_SIGNATURE):
            self._reject("توقيع الملف لا يطابق مستند DOCX صالح.")

    def _check_zip(self, data: bytes):
        import io

        try:
            with zipfile.ZipFile(io.BytesIO(data)) as archive:
                names = archive.namelist()
                if not REQUIRED_ENTRIES.issubset(set(names)):
                    self._reject("بنية DOCX غير صالحة (مدخلات مفقودة).")
                total_uncompressed = 0
                for info in archive.infolist():
                    name = info.filename
                    if name.startswith("/") or ".." in name.replace("\\", "/").split("/"):
                        self._reject("مسار مضغوط غير آمن (zip-slip).")
                    if name in MACRO_MARKERS or name.lower().endswith((".exe", ".dll", ".bat", ".js", ".vbs")):
                        self._reject("الملف يحتوي عناصر تنفيذية/ماكرو غير مسموحة.")
                    total_uncompressed += info.file_size
                    if info.compress_size > 0:
                        ratio = info.file_size / info.compress_size
                        if ratio > MAX_COMPRESSION_RATIO and info.file_size > 1024 * 1024:
                            self._reject("نسبة ضغط مرتفعة بشكل مريب (zip-bomb).")
                if total_uncompressed > MAX_UNCOMPRESSED_BYTES:
                    self._reject("الحجم غير المضغوط يتجاوز الحد المسموح.")
        except zipfile.BadZipFile:
            self._reject("الملف ليس أرشيف ZIP صالحاً.")


template_security_scanner = TemplateSecurityScanner()
