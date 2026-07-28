from django.http import FileResponse
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle

from reports.audit import actions
from reports.audit.service import record
from reports.shared.permissions import IsOwnerOrAdmin
from reports.shared.storage import StorageError, document_storage

from .application import CreateReportUseCase, RetryReportUseCase
from .selectors import reports_for
from .serializers import (
    GeneratedReportCreateSerializer,
    GeneratedReportSerializer,
    GeneratedReportStatusSerializer,
)


class GeneratedReportViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, IsOwnerOrAdmin]
    http_method_names = ["get", "post", "head", "options"]

    def get_queryset(self):
        return reports_for(self.request.user)

    def get_throttles(self):
        if self.action == "create":
            self.throttle_scope = "report_create"
            return [ScopedRateThrottle()]
        if self.action in {"download_docx", "download_pdf"}:
            self.throttle_scope = "download"
            return [ScopedRateThrottle()]
        return super().get_throttles()

    def get_serializer_class(self):
        if self.action == "create":
            return GeneratedReportCreateSerializer
        return GeneratedReportSerializer

    def create(self, request, *args, **kwargs):
        serializer = GeneratedReportCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        report = CreateReportUseCase().execute(user=request.user, data=serializer.validated_data)
        record(actions.REPORT_CREATED, actor=request.user, request=request, target=report)
        output = GeneratedReportSerializer(report, context={"request": request})
        return Response(output.data, status=status.HTTP_202_ACCEPTED)

    @action(detail=True, methods=["get"], url_path="status")
    def poll_status(self, request, pk=None):
        report = self.get_object()
        return Response(GeneratedReportStatusSerializer(report, context={"request": request}).data)

    @action(detail=True, methods=["post"], url_path="retry")
    def retry(self, request, pk=None):
        report = self.get_object()
        report = RetryReportUseCase().execute(report=report)
        return Response(
            GeneratedReportStatusSerializer(report, context={"request": request}).data,
            status=status.HTTP_202_ACCEPTED,
        )

    @action(detail=True, methods=["get"], url_path="download-docx")
    def download_docx(self, request, pk=None):
        return self._download_file(self.get_object(), "docx_file")

    @action(detail=True, methods=["get"], url_path="download-pdf")
    def download_pdf(self, request, pk=None):
        return self._download_file(self.get_object(), "pdf_file")

    def _download_file(self, report, field_name):
        file_field = getattr(report, field_name)
        name = getattr(file_field, "name", "") or ""
        if not name or not document_storage.exists(name):
            return Response({"detail": "الملف غير متوفر."}, status=status.HTTP_404_NOT_FOUND)
        try:
            handle = document_storage.open(name)
        except StorageError:
            return Response({"detail": "تعذّر الوصول إلى الملف."}, status=status.HTTP_404_NOT_FOUND)
        extension = name.rsplit(".", 1)[-1]
        download_name = f"{self._safe_filename(report.title)}.{extension}"
        record(
            actions.REPORT_DOWNLOADED,
            actor=report.created_by,
            request=self.request,
            target=report,
            metadata={"kind": extension},
        )
        return FileResponse(handle, as_attachment=True, filename=download_name)

    @staticmethod
    def _safe_filename(title: str) -> str:
        cleaned = "".join(c for c in (title or "report") if c.isalnum() or c in " _-").strip()
        return (cleaned or "report")[:80]
