from django.urls import reverse
from rest_framework import serializers

from reports.accounts.serializers import UserSummarySerializer
from reports.catalog.serializers import ReportTypeSerializer
from reports.models import GeneratedReport, ReportType


class GeneratedReportSerializer(serializers.ModelSerializer):
    report_type = ReportTypeSerializer(read_only=True)
    created_by = UserSummarySerializer(read_only=True)
    download_docx_url = serializers.SerializerMethodField()
    download_pdf_url = serializers.SerializerMethodField()

    class Meta:
        model = GeneratedReport
        fields = [
            "id",
            "report_type",
            "created_by",
            "title",
            "input_data",
            "docx_file",
            "pdf_file",
            "status",
            "error_message",
            "download_docx_url",
            "download_pdf_url",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields

    def _absolute_action_url(self, obj, action_name):
        request = self.context.get("request")
        path = reverse(f"generatedreport-{action_name}", args=[obj.pk])
        return request.build_absolute_uri(path) if request else path

    def get_download_docx_url(self, obj):
        if not obj.docx_file:
            return None
        return self._absolute_action_url(obj, "download-docx")

    def get_download_pdf_url(self, obj):
        if not obj.pdf_file:
            return None
        return self._absolute_action_url(obj, "download-pdf")


class GeneratedReportCreateSerializer(serializers.Serializer):
    """Input validation only. Persistence happens in the CreateReportUseCase."""

    report_type_id = serializers.PrimaryKeyRelatedField(
        queryset=ReportType.objects.filter(is_active=True), source="report_type"
    )
    title = serializers.CharField(required=False, allow_blank=True, default="")
    input_data = serializers.JSONField(required=False, default=dict)

    def validate_input_data(self, value):
        if not isinstance(value, dict):
            raise serializers.ValidationError("input_data يجب أن يكون كائناً JSON.")
        return value


class GeneratedReportStatusSerializer(serializers.ModelSerializer):
    """Lightweight payload for polling report generation status."""

    download_docx_url = serializers.SerializerMethodField()
    download_pdf_url = serializers.SerializerMethodField()

    class Meta:
        model = GeneratedReport
        fields = [
            "id",
            "status",
            "error_message",
            "attempts",
            "download_docx_url",
            "download_pdf_url",
            "updated_at",
        ]
        read_only_fields = fields

    def _url(self, obj, name):
        request = self.context.get("request")
        from django.urls import reverse

        path = reverse(f"generatedreport-{name}", args=[obj.pk])
        return request.build_absolute_uri(path) if request else path

    def get_download_docx_url(self, obj):
        return self._url(obj, "download-docx") if obj.docx_file else None

    def get_download_pdf_url(self, obj):
        return self._url(obj, "download-pdf") if obj.pdf_file else None
