from rest_framework import serializers

from reports.models import ReportType


class ReportTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReportType
        fields = [
            "id",
            "name",
            "slug",
            "description",
            "template_file",
            "fields_schema",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]
