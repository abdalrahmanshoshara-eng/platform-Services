from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone
from rest_framework import serializers

from reports.catalog.validation import validate_fields_schema
from reports.models import (
    AuditEvent,
    GeneratedReport,
    ReportType,
    Service,
)

User = get_user_model()


class AdminUserSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    phone = serializers.SerializerMethodField()
    disabled_reason = serializers.SerializerMethodField()
    reports_count = serializers.IntegerField(read_only=True, default=0)
    restrictions_count = serializers.IntegerField(read_only=True, default=0)

    class Meta:
        model = User
        fields = [
            "id", "username", "email", "first_name", "last_name", "full_name", "phone",
            "is_active", "is_staff", "is_superuser", "date_joined", "last_login",
            "disabled_reason", "reports_count", "restrictions_count",
        ]
        read_only_fields = fields

    def get_full_name(self, obj):
        return obj.get_full_name() or obj.username

    def _administration(self, obj):
        try:
            return obj.administration
        except ObjectDoesNotExist:
            return None

    def get_phone(self, obj):
        administration = self._administration(obj)
        return administration.phone if administration else ""

    def get_disabled_reason(self, obj):
        administration = self._administration(obj)
        return administration.disabled_reason if administration else ""


class RestrictionSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    target_id = serializers.IntegerField()
    target_name = serializers.CharField()
    target_type = serializers.CharField()
    reason = serializers.CharField()
    starts_at = serializers.DateTimeField(allow_null=True)
    expires_at = serializers.DateTimeField(allow_null=True)
    created_at = serializers.DateTimeField()
    is_expired = serializers.BooleanField()


class AdminUserDetailSerializer(AdminUserSerializer):
    restrictions = serializers.SerializerMethodField()

    class Meta(AdminUserSerializer.Meta):
        fields = AdminUserSerializer.Meta.fields + ["restrictions"]

    def get_restrictions(self, obj):
        now = timezone.now()
        items = []
        for item in obj.service_restrictions.select_related("service").all():
            items.append({
                "id": item.id, "target_id": item.service_id, "target_name": item.service.name,
                "target_type": "service", "reason": item.reason, "expires_at": item.expires_at,
                "starts_at": item.starts_at, "created_at": item.created_at,
                "is_expired": bool(item.expires_at and item.expires_at <= now),
            })
        return RestrictionSerializer(items, many=True).data


class AdminServiceSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source="category.name", read_only=True)
    restrictions_count = serializers.IntegerField(read_only=True, default=0)
    launches_count = serializers.SerializerMethodField()

    class Meta:
        model = Service
        fields = [
            "id", "name", "slug", "description", "kind", "launch_target", "icon", "accent",
            "sort_order", "requires_staff", "is_active", "category", "category_name",
            "disabled_reason", "disabled_at", "settings", "restrictions_count", "launches_count",
            "created_at", "updated_at",
        ]
        # is_active is state, not a plain attribute: it must change only through
        # the audited activate/deactivate actions (which set disabled_by/at and
        # write an AuditEvent), never via a generic PATCH.
        read_only_fields = ["is_active", "disabled_reason", "disabled_at", "created_at", "updated_at"]

    def validate(self, attrs):
        instance = self.instance or Service(**attrs)
        for key, value in attrs.items():
            setattr(instance, key, value)
        instance.clean()
        return attrs

    def get_launches_count(self, obj):
        return AuditEvent.objects.filter(
            action="service.launch",
            target_type="Service",
            target_id=str(obj.id),
            outcome="success",
        ).count()


class AdminJobSerializer(serializers.ModelSerializer):
    user = serializers.CharField(source="created_by.username", read_only=True)
    report_type_name = serializers.CharField(source="report_type.name", read_only=True)
    duration_seconds = serializers.SerializerMethodField()

    class Meta:
        model = GeneratedReport
        fields = [
            "id", "title", "user", "report_type_name", "status", "attempts", "task_id",
            "error_message", "queued_at", "started_at", "finished_at", "created_at",
            "updated_at", "duration_seconds",
        ]
        read_only_fields = fields

    def get_duration_seconds(self, obj):
        if not obj.started_at:
            return None
        end = obj.finished_at or timezone.now()
        return max(0, round((end - obj.started_at).total_seconds(), 2))


class AuditEventSerializer(serializers.ModelSerializer):
    actor_name = serializers.SerializerMethodField()

    class Meta:
        model = AuditEvent
        fields = [
            "id", "actor", "actor_name", "action", "target_type", "target_id", "outcome",
            "request_id", "ip_address", "user_agent", "metadata", "created_at",
        ]
        read_only_fields = fields

    def get_actor_name(self, obj):
        return obj.actor.username if obj.actor else "النظام"


class AdminReportTypeSerializer(serializers.ModelSerializer):
    versions_count = serializers.IntegerField(read_only=True, default=0)
    reports_count = serializers.IntegerField(read_only=True, default=0)

    class Meta:
        model = ReportType
        fields = [
            "id", "name", "slug", "description", "template_file", "fields_schema",
            "is_active", "versions_count", "reports_count", "created_at", "updated_at",
        ]

    def validate(self, attrs):
        # The backend is the single source of truth for schema validity; reject
        # malformed fields_schema (dup names, bad type, select without options, …)
        # instead of persisting it via a generic create/PATCH. Raises a DomainError
        # (INVALID_FIELDS_SCHEMA) handled by the unified error renderer.
        if "fields_schema" in attrs:
            validate_fields_schema(attrs["fields_schema"])
        return attrs
