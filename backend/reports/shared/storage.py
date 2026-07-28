"""Storage abstraction for generated documents.

Business logic depends on this interface, never on FileField.path or MEDIA_ROOT.
The default backend is Django's storage (local filesystem in development). A new
backend (e.g. S3) can be added later WITHOUT touching the generation use case.
"""

import hashlib

from django.core.files.base import ContentFile
from django.core.files.storage import default_storage


class StorageError(RuntimeError):
    pass


class DocumentStorage:
    def __init__(self, backend=None):
        self._backend = backend or default_storage

    def save(self, name: str, content: bytes) -> str:
        try:
            if self._backend.exists(name):
                self._backend.delete(name)
            return self._backend.save(name, ContentFile(content))
        except Exception as exc:  # noqa: BLE001
            raise StorageError(str(exc)) from exc

    def open(self, name: str):
        try:
            return self._backend.open(name, "rb")
        except FileNotFoundError as exc:
            raise StorageError("file not found") from exc

    def exists(self, name: str) -> bool:
        return bool(name) and self._backend.exists(name)

    def delete(self, name: str) -> None:
        if name and self._backend.exists(name):
            self._backend.delete(name)

    def get_size(self, name: str) -> int:
        return self._backend.size(name)

    def get_checksum(self, name: str) -> str:
        sha = hashlib.sha256()
        with self._backend.open(name, "rb") as fh:
            for chunk in iter(lambda: fh.read(65536), b""):
                sha.update(chunk)
        return sha.hexdigest()


document_storage = DocumentStorage()
