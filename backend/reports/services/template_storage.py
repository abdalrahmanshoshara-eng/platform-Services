"""Storage boundary for managed and legacy report templates."""

from pathlib import Path, PurePosixPath
from uuid import uuid4

from django.conf import settings

from reports.shared.storage import StorageError, document_storage

MANAGED_PREFIX = "report_templates/"


class TemplateStorage:
    def __init__(self, storage=document_storage):
        self.storage = storage

    def save_upload(self, *, report_type_id: int, data: bytes) -> str:
        key = f"{MANAGED_PREFIX}{report_type_id}/{uuid4().hex}.docx"
        return self.storage.save(key, data)

    def read(self, key: str) -> bytes:
        if self.storage.exists(key):
            with self.storage.open(key) as handle:
                return handle.read()

        legacy_name = PurePosixPath(key)
        if legacy_name.name != key or legacy_name.suffix.lower() != ".docx":
            raise StorageError("template not found")
        legacy_path = Path(settings.BASE_DIR) / "reports" / "templates" / "reports" / legacy_name.name
        if not legacy_path.is_file():
            raise StorageError("template not found")
        return legacy_path.read_bytes()

    def delete_upload(self, key: str) -> None:
        if key.startswith(MANAGED_PREFIX):
            self.storage.delete(key)


template_storage = TemplateStorage()
