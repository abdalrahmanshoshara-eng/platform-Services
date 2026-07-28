from urllib.parse import urlparse

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


class ReportType(models.Model):
    name = models.CharField(max_length=180)
    slug = models.SlugField(max_length=180, unique=True)
    description = models.TextField(blank=True)
    template_file = models.CharField(max_length=255, help_text="DOCX filename inside reports/templates/reports/")
    fields_schema = models.JSONField(default=list, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class ReportTemplateVersion(models.Model):
    """Immutable-after-activation snapshot of a report template + its schema."""

    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        VALIDATED = "validated", "Validated"
        ACTIVE = "active", "Active"
        INACTIVE = "inactive", "Inactive"
        REJECTED = "rejected", "Rejected"

    report_type = models.ForeignKey(ReportType, on_delete=models.CASCADE, related_name="versions")
    version = models.PositiveIntegerField()
    template_file = models.CharField(max_length=255)
    fields_schema = models.JSONField(default=list, blank=True)
    checksum = models.CharField(max_length=64, blank=True, default="")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_template_versions",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    activated_at = models.DateTimeField(null=True, blank=True)

    IMMUTABLE_FIELDS = ("template_file", "fields_schema", "checksum")

    class Meta:
        ordering = ["report_type", "-version"]
        unique_together = [("report_type", "version")]
        indexes = [models.Index(fields=["report_type", "status"])]

    def __str__(self):
        return f"{self.report_type.slug} v{self.version} ({self.status})"

    def save(self, *args, **kwargs):
        # Enforce immutability of impactful fields once a version is activated.
        if self.pk:
            previous = ReportTemplateVersion.objects.filter(pk=self.pk).first()
            if previous and previous.status == self.Status.ACTIVE:
                for field in self.IMMUTABLE_FIELDS:
                    if getattr(previous, field) != getattr(self, field):
                        from reports.shared.exceptions import DomainError

                        raise DomainError(
                            "لا يمكن تعديل إصدار قالب مفعّل. أنشئ إصداراً جديداً.",
                            code="TEMPLATE_VERSION_IMMUTABLE",
                            status_code=409,
                        )
        super().save(*args, **kwargs)


class GeneratedReport(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        QUEUED = "queued", "Queued"
        PROCESSING = "processing", "Processing"
        COMPLETED = "completed", "Completed"
        FAILED = "failed", "Failed"
        CANCELLED = "cancelled", "Cancelled"

    report_type = models.ForeignKey(ReportType, on_delete=models.PROTECT, related_name="generated_reports")
    template_version = models.ForeignKey(
        "ReportTemplateVersion",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="generated_reports",
    )
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="generated_reports")
    title = models.CharField(max_length=255)
    input_data = models.JSONField(default=dict)
    docx_file = models.FileField(upload_to="generated_reports/docx/", blank=True, null=True)
    pdf_file = models.FileField(upload_to="generated_reports/pdf/", blank=True, null=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    error_message = models.TextField(blank=True)
    task_id = models.CharField(max_length=255, blank=True, default="")
    attempts = models.PositiveSmallIntegerField(default=0)
    queued_at = models.DateTimeField(null=True, blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["created_by", "-created_at"]),
            models.Index(fields=["status"]),
        ]

    def __str__(self):
        return self.title


class AuditEvent(models.Model):
    """Append-only record of security/administrative actions.

    Never stores passwords, tokens, secrets, full input data, or raw tracebacks.
    """

    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_events",
    )
    action = models.CharField(max_length=80)
    target_type = models.CharField(max_length=80, blank=True, default="")
    target_id = models.CharField(max_length=64, blank=True, default="")
    outcome = models.CharField(max_length=20, default="success")
    request_id = models.CharField(max_length=64, blank=True, default="")
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=400, blank=True, default="")
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["action"]),
            models.Index(fields=["actor", "-created_at"]),
            # Backs per-target analytics lookups (e.g. service.launch counts by service).
            models.Index(fields=["action", "target_type", "target_id"]),
        ]

    def __str__(self):
        return f"{self.action} by {self.actor_id} ({self.outcome})"


class ServiceCategory(models.Model):
    name = models.CharField(max_length=120)
    slug = models.SlugField(max_length=120, unique=True)
    description = models.CharField(max_length=240, blank=True)
    icon = models.CharField(max_length=40, blank=True)
    sort_order = models.PositiveSmallIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["sort_order", "name"]
        verbose_name_plural = "service categories"

    def __str__(self):
        return self.name


class Service(models.Model):
    class Kind(models.TextChoices):
        INTERNAL = "internal", "Internal"
        EXTERNAL = "external", "External"

    category = models.ForeignKey(ServiceCategory, on_delete=models.PROTECT, related_name="services")
    name = models.CharField(max_length=140)
    slug = models.SlugField(max_length=140, unique=True)
    description = models.CharField(max_length=320)
    kind = models.CharField(max_length=16, choices=Kind.choices)
    launch_target = models.CharField(
        max_length=500,
        help_text="Internal route beginning with / or an HTTPS external URL.",
    )
    icon = models.CharField(max_length=40, blank=True)
    accent = models.CharField(max_length=20, default="green")
    sort_order = models.PositiveSmallIntegerField(default=0)
    requires_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    disabled_reason = models.CharField(max_length=240, blank=True)
    disabled_at = models.DateTimeField(null=True, blank=True)
    disabled_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="disabled_services",
    )
    settings = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["category__sort_order", "sort_order", "name"]

    def __str__(self):
        return self.name

    def clean(self):
        if self.kind == self.Kind.INTERNAL and not self.launch_target.startswith("/"):
            raise ValidationError({"launch_target": "Internal service targets must start with /."})
        if self.kind == self.Kind.EXTERNAL:
            parsed = urlparse(self.launch_target)
            if parsed.scheme != "https" or not parsed.netloc:
                raise ValidationError({"launch_target": "External service targets must use HTTPS."})


class UserServiceRestriction(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="service_restrictions")
    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name="user_restrictions")
    reason = models.CharField(max_length=240, blank=True)
    starts_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_service_restrictions",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [("user", "service")]

    def __str__(self):
        return f"{self.user_id} blocked from {self.service_id}"


class UserCategoryRestriction(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="category_restrictions")
    category = models.ForeignKey(ServiceCategory, on_delete=models.CASCADE, related_name="user_restrictions")
    reason = models.CharField(max_length=240, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_category_restrictions",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [("user", "category")]

    def __str__(self):
        return f"{self.user_id} blocked from category {self.category_id}"


class UserAdministration(models.Model):
    """Administrative metadata kept separate from Django's authentication user."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="administration",
    )
    phone = models.CharField(max_length=40, blank=True)
    disabled_reason = models.CharField(max_length=240, blank=True)
    disabled_at = models.DateTimeField(null=True, blank=True)
    disabled_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="disabled_users",
    )
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Administration metadata for {self.user_id}"
