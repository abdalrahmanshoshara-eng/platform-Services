"""Application use cases for the report-template version lifecycle."""

import hashlib

from django.db import transaction
from django.db.models import Max
from django.utils import timezone

from reports.models import ReportTemplateVersion, ReportType
from reports.services.template_storage import template_storage
from reports.shared.exceptions import DomainError
from reports.shared.storage import StorageError

from .placeholders import (
    extract_template_placeholders_from_bytes,
    validate_template_against_schema,
)
from .security import TemplateSecurityError, template_security_scanner
from .validation import validate_fields_schema


def _missing_file_error():
    return DomainError(
        "ملف القالب غير متاح.",
        code="TEMPLATE_FILE_MISSING",
        status_code=400,
    )


def _read_and_scan(version: ReportTemplateVersion) -> bytes:
    try:
        data = template_storage.read(version.template_file)
    except StorageError as exc:
        raise _missing_file_error() from exc
    _scan_safely(filename="template.docx", data=data)
    return data


def _scan_safely(*, filename: str, data: bytes) -> None:
    try:
        template_security_scanner.scan(filename=filename, data=data)
    except DomainError:
        raise
    except Exception as exc:
        raise TemplateSecurityError() from exc


def _validate_content(version: ReportTemplateVersion, data: bytes) -> str:
    validate_fields_schema(version.fields_schema)
    placeholders = extract_template_placeholders_from_bytes(data)
    validate_template_against_schema(placeholders, version.fields_schema)
    return hashlib.sha256(data).hexdigest()


class CreateTemplateVersionUseCase:
    def execute(
        self,
        *,
        report_type: ReportType,
        actor,
        filename: str,
        data: bytes,
    ) -> ReportTemplateVersion:
        _scan_safely(filename=filename, data=data)
        storage_key = ""
        try:
            with transaction.atomic():
                locked_type = ReportType.objects.select_for_update().get(pk=report_type.pk)
                latest = (
                    ReportTemplateVersion.objects.filter(report_type=locked_type).aggregate(latest=Max("version"))[
                        "latest"
                    ]
                    or 0
                )
                storage_key = template_storage.save_upload(
                    report_type_id=locked_type.pk,
                    data=data,
                )
                return ReportTemplateVersion.objects.create(
                    report_type=locked_type,
                    version=latest + 1,
                    template_file=storage_key,
                    fields_schema=locked_type.fields_schema,
                    status=ReportTemplateVersion.Status.DRAFT,
                    created_by=actor,
                )
        except Exception:
            if storage_key:
                template_storage.delete_upload(storage_key)
            raise


class ValidateTemplateVersionUseCase:
    def execute(self, *, version: ReportTemplateVersion) -> ReportTemplateVersion:
        with transaction.atomic():
            version = ReportTemplateVersion.objects.select_for_update().get(pk=version.pk)
            if version.status == ReportTemplateVersion.Status.VALIDATED:
                return version
            if version.status != ReportTemplateVersion.Status.DRAFT:
                raise DomainError(
                    "لا يمكن التحقق من نسخة القالب في حالتها الحالية.",
                    code="INVALID_TEMPLATE_VERSION_STATE",
                    status_code=409,
                )
            data = _read_and_scan(version)
            version.checksum = _validate_content(version, data)
            version.status = ReportTemplateVersion.Status.VALIDATED
            version.save(update_fields=["checksum", "status"])
            return version


class ActivateTemplateVersionUseCase:
    """Atomically activate one validated version and retire the previous one."""

    def execute(self, *, version: ReportTemplateVersion) -> ReportTemplateVersion:
        with transaction.atomic():
            ReportType.objects.select_for_update().get(pk=version.report_type_id)
            locked = list(
                ReportTemplateVersion.objects.select_for_update()
                .filter(report_type_id=version.report_type_id)
                .order_by("pk")
            )
            version = next(item for item in locked if item.pk == version.pk)
            if version.status == ReportTemplateVersion.Status.ACTIVE:
                return version
            if version.status not in {
                ReportTemplateVersion.Status.VALIDATED,
                ReportTemplateVersion.Status.INACTIVE,
            }:
                raise DomainError(
                    "يجب التحقق من نسخة القالب قبل تفعيلها.",
                    code="TEMPLATE_VERSION_NOT_VALIDATED",
                    status_code=409,
                )

            data = _read_and_scan(version)
            checksum = _validate_content(version, data)
            if not version.checksum or checksum != version.checksum:
                raise DomainError(
                    "تغير ملف القالب بعد التحقق منه.",
                    code="TEMPLATE_CHECKSUM_MISMATCH",
                    status_code=409,
                )

            ReportTemplateVersion.objects.filter(
                report_type_id=version.report_type_id,
                status=ReportTemplateVersion.Status.ACTIVE,
            ).exclude(pk=version.pk).update(status=ReportTemplateVersion.Status.INACTIVE)
            version.status = ReportTemplateVersion.Status.ACTIVE
            version.activated_at = timezone.now()
            version.save(update_fields=["status", "activated_at"])
            return version


class DeactivateTemplateVersionUseCase:
    def execute(self, *, version: ReportTemplateVersion) -> ReportTemplateVersion:
        with transaction.atomic():
            version = ReportTemplateVersion.objects.select_for_update().get(pk=version.pk)
            if version.status == ReportTemplateVersion.Status.INACTIVE:
                return version
            if version.status != ReportTemplateVersion.Status.ACTIVE:
                raise DomainError(
                    "يمكن تعطيل نسخة القالب النشطة فقط.",
                    code="INVALID_TEMPLATE_VERSION_STATE",
                    status_code=409,
                )
            version.status = ReportTemplateVersion.Status.INACTIVE
            version.save(update_fields=["status"])
            return version


class ArchiveTemplateVersionUseCase:
    def execute(self, *, version: ReportTemplateVersion) -> ReportTemplateVersion:
        with transaction.atomic():
            version = ReportTemplateVersion.objects.select_for_update().get(pk=version.pk)
            if version.status == ReportTemplateVersion.Status.ARCHIVED:
                return version
            if version.status == ReportTemplateVersion.Status.ACTIVE:
                raise DomainError(
                    "عطّل نسخة القالب النشطة قبل أرشفتها.",
                    code="ACTIVE_TEMPLATE_CANNOT_BE_ARCHIVED",
                    status_code=409,
                )
            version.status = ReportTemplateVersion.Status.ARCHIVED
            version.save(update_fields=["status"])
            return version
