"""Bounded structural security scanning for uploaded DOCX templates."""

import io
import zipfile

from defusedxml import ElementTree
from django.conf import settings

from reports.shared.exceptions import DomainError

DOCX_SIGNATURE = b"PK\x03\x04"
MAX_UPLOAD_BYTES = 10 * 1024 * 1024
MAX_UNCOMPRESSED_BYTES = 100 * 1024 * 1024
MAX_COMPRESSION_RATIO = 100
MAX_ARCHIVE_ENTRIES = 2000
MAX_XML_PART_BYTES = 10 * 1024 * 1024
REQUIRED_ENTRIES = {"[Content_Types].xml", "_rels/.rels", "word/document.xml"}
EXECUTABLE_SUFFIXES = (".exe", ".dll", ".bat", ".cmd", ".js", ".vbs", ".ps1", ".com")
EMBEDDED_PREFIXES = ("word/embeddings/", "word/activex/")


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

    def _reject(self, message: str):
        raise TemplateSecurityError(message)

    def _check_filename(self, filename: str):
        if not filename or "/" in filename or "\\" in filename or ".." in filename:
            self._reject("اسم ملف القالب غير آمن.")
        if not filename.lower().endswith(".docx"):
            self._reject("امتداد الملف غير مدعوم؛ المطلوب DOCX.")

    def _check_size(self, data: bytes):
        if not data:
            self._reject("ملف القالب فارغ.")
        limit = getattr(settings, "TEMPLATE_MAX_UPLOAD_BYTES", MAX_UPLOAD_BYTES)
        if len(data) > limit:
            self._reject("حجم ملف القالب يتجاوز الحد المسموح.")

    def _check_signature(self, data: bytes):
        if not data.startswith(DOCX_SIGNATURE):
            self._reject("الملف ليس مستند DOCX صالحاً.")

    def _check_zip(self, data: bytes):
        try:
            with zipfile.ZipFile(io.BytesIO(data)) as archive:
                names = archive.namelist()
                if not REQUIRED_ENTRIES.issubset(set(names)):
                    self._reject("بنية ملف DOCX غير مكتملة.")
                if len(names) != len(set(names)):
                    self._reject("يحتوي القالب على عناصر مضغوطة مكررة.")
                if len(names) > getattr(settings, "TEMPLATE_MAX_ARCHIVE_ENTRIES", MAX_ARCHIVE_ENTRIES):
                    self._reject("عدد عناصر القالب يتجاوز الحد المسموح.")

                total_uncompressed = 0
                for info in archive.infolist():
                    name = info.filename.replace("\\", "/")
                    lower_name = name.lower()
                    if name.startswith("/") or ".." in name.split("/") or ":" in name.split("/")[0]:
                        self._reject("يحتوي القالب على مسار مضغوط غير آمن.")
                    if info.flag_bits & 0x1:
                        self._reject("القوالب المشفرة غير مدعومة.")
                    if (
                        "vbaproject" in lower_name
                        or lower_name.endswith(EXECUTABLE_SUFFIXES)
                        or lower_name.startswith(EMBEDDED_PREFIXES)
                        or "oleobject" in lower_name
                    ):
                        self._reject("يحتوي القالب على محتوى تنفيذي أو مضمّن غير مسموح.")
                    total_uncompressed += info.file_size
                    if info.compress_size > 0:
                        ratio = info.file_size / info.compress_size
                        if ratio > MAX_COMPRESSION_RATIO and info.file_size > 1024 * 1024:
                            self._reject("نسبة ضغط القالب مرتفعة بشكل غير آمن.")

                if total_uncompressed > MAX_UNCOMPRESSED_BYTES:
                    self._reject("حجم القالب بعد فك الضغط يتجاوز الحد المسموح.")
                self._check_xml_parts(archive, names)
        except zipfile.BadZipFile:
            self._reject("الملف ليس أرشيف DOCX صالحاً.")
        except TemplateSecurityError:
            raise
        except Exception:
            self._reject("تعذر التحقق من بنية ملف DOCX.")

    def _check_xml_parts(self, archive, names):
        content_types = archive.read("[Content_Types].xml")
        if b"macroenabled" in content_types.lower():
            self._reject("قوالب الماكرو غير مسموحة.")

        for name in names:
            lower_name = name.lower()
            if not lower_name.endswith((".xml", ".rels")):
                continue
            info = archive.getinfo(name)
            if info.file_size > getattr(settings, "TEMPLATE_MAX_XML_PART_BYTES", MAX_XML_PART_BYTES):
                self._reject("حجم جزء XML في القالب يتجاوز الحد المسموح.")
            xml = archive.read(name)
            lowered = xml.lower()
            if b"<!doctype" in lowered or b"<!entity" in lowered:
                self._reject("كيانات XML الخارجية غير مسموحة.")
            root = ElementTree.fromstring(xml)
            if lower_name.endswith(".rels"):
                for relationship in root.iter():
                    if relationship.attrib.get("TargetMode", "").lower() == "external":
                        self._reject("الروابط الخارجية في القوالب غير مسموحة.")


template_security_scanner = TemplateSecurityScanner()
