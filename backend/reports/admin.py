from django.contrib import admin

from .models import (
    AuditEvent,
    GeneratedReport,
    ReportTemplateVersion,
    ReportType,
    Service,
    UserServiceRestriction,
)


@admin.register(ReportType)
class ReportTypeAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "template_file", "is_active", "created_at")
    list_filter = ("is_active",)
    search_fields = ("name", "slug", "description")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(GeneratedReport)
class GeneratedReportAdmin(admin.ModelAdmin):
    list_display = ("title", "report_type", "created_by", "status", "created_at")
    list_filter = ("status", "report_type", "created_at")
    search_fields = ("title", "created_by__username", "created_by__email")
    readonly_fields = ("created_at", "updated_at", "error_message")


@admin.register(ReportTemplateVersion)
class ReportTemplateVersionAdmin(admin.ModelAdmin):
    list_display = ("report_type", "version", "status", "checksum", "created_at", "activated_at")
    list_filter = ("status", "report_type")
    search_fields = ("report_type__slug", "template_file")
    readonly_fields = ("checksum", "created_at", "activated_at")


@admin.register(AuditEvent)
class AuditEventAdmin(admin.ModelAdmin):
    list_display = ("action", "actor", "target_type", "target_id", "outcome", "created_at")
    list_filter = ("action", "outcome", "created_at")
    search_fields = ("action", "actor__username", "target_id", "request_id")
    readonly_fields = [f.name for f in AuditEvent._meta.fields]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "kind", "sort_order", "requires_staff", "is_active")
    list_filter = ("kind", "category", "requires_staff", "is_active")
    list_editable = ("sort_order", "is_active")
    search_fields = ("name", "slug", "description")
    prepopulated_fields = {"slug": ("name",)}


admin.site.register(UserServiceRestriction)
