from datetime import timedelta

from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import Count, Exists, OuterRef, Q
from django.db.models.functions import TruncDate
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from reports.audit.actions import (
    TEMPLATE_ACTIVATED,
    TEMPLATE_ARCHIVED,
    TEMPLATE_DEACTIVATED,
    TEMPLATE_UPLOADED,
    TEMPLATE_VALIDATED,
)
from reports.audit.service import record
from reports.catalog.application import (
    ActivateTemplateVersionUseCase,
    ArchiveTemplateVersionUseCase,
    CreateTemplateVersionUseCase,
    DeactivateTemplateVersionUseCase,
    ValidateTemplateVersionUseCase,
)
from reports.generation.application import RetryReportUseCase
from reports.generation.domain import transition
from reports.models import (
    AuditEvent,
    GeneratedReport,
    ReportTemplateVersion,
    ReportType,
    Service,
    ServiceCategory,
    UserAdministration,
    UserCategoryRestriction,
    UserServiceRestriction,
)

from .permissions import IsPlatformAdmin
from .serializers import (
    AdminJobSerializer,
    AdminReportTypeSerializer,
    AdminServiceSerializer,
    AdminTemplateVersionSerializer,
    AdminUserDetailSerializer,
    AdminUserSerializer,
    AuditEventSerializer,
    TemplateVersionUploadSerializer,
)

User = get_user_model()


def _reason(request):
    return str(request.data.get("reason", "")).strip()[:240]


class AdminDashboardView(APIView):
    permission_classes = [IsPlatformAdmin]

    def get(self, request):
        now = timezone.now()
        since = now - timedelta(hours=24)
        jobs = GeneratedReport.objects.all()
        return Response({
            "summary": {
                "users": User.objects.count(),
                "active_users": User.objects.filter(is_active=True).count(),
                "services": Service.objects.count(),
                "active_services": Service.objects.filter(is_active=True).count(),
                "reports": jobs.count(),
                "reports_last_24h": jobs.filter(created_at__gte=since).count(),
                "queued_jobs": jobs.filter(status__in=["pending", "queued", "processing"]).count(),
                "failed_jobs": jobs.filter(status="failed").count(),
            },
            "recent_activity": AuditEventSerializer(
                AuditEvent.objects.select_related("actor")[:8], many=True
            ).data,
            "job_statuses": list(jobs.values("status").annotate(count=Count("id")).order_by("status")),
        })


class AdminUserViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsPlatformAdmin]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ["username", "email", "first_name", "last_name", "administration__phone"]
    ordering_fields = ["date_joined", "last_login", "username", "email"]
    ordering = ["-date_joined"]

    def get_queryset(self):
        queryset = User.objects.select_related("administration").annotate(
            reports_count=Count("generated_reports", distinct=True),
            restrictions_count=Count("service_restrictions", distinct=True),
        )
        state = self.request.query_params.get("status")
        role = self.request.query_params.get("role")
        if state == "active":
            queryset = queryset.filter(is_active=True)
        elif state == "inactive":
            queryset = queryset.filter(is_active=False)
        if role == "admin":
            queryset = queryset.filter(Q(is_staff=True) | Q(is_superuser=True))
        elif role == "user":
            queryset = queryset.filter(is_staff=False, is_superuser=False)
        return queryset

    def get_serializer_class(self):
        return AdminUserDetailSerializer if self.action == "retrieve" else AdminUserSerializer

    @action(detail=True, methods=["post"])
    def deactivate(self, request, pk=None):
        reason = _reason(request)
        with transaction.atomic():
            user = User.objects.select_for_update().get(pk=pk)
            if user.pk == request.user.pk:
                return Response({"detail": "لا يمكنك تعطيل حسابك الحالي."}, status=409)
            if (user.is_staff or user.is_superuser) and User.objects.filter(
                is_active=True
            ).filter(Q(is_staff=True) | Q(is_superuser=True)).count() <= 1:
                return Response({"detail": "لا يمكن تعطيل آخر مدير نشط."}, status=409)
            user.is_active = False
            user.save(update_fields=["is_active"])
            UserAdministration.objects.update_or_create(
                user=user,
                defaults={"disabled_reason": reason, "disabled_at": timezone.now(), "disabled_by": request.user},
            )
            record("admin.user.deactivated", actor=request.user, request=request, target=user, metadata={"reason": reason})
        return Response(AdminUserDetailSerializer(user).data)

    @action(detail=True, methods=["post"])
    def activate(self, request, pk=None):
        with transaction.atomic():
            user = User.objects.select_for_update().get(pk=pk)
            user.is_active = True
            user.save(update_fields=["is_active"])
            UserAdministration.objects.update_or_create(
                user=user, defaults={"disabled_reason": "", "disabled_at": None, "disabled_by": None}
            )
            record("admin.user.activated", actor=request.user, request=request, target=user)
        return Response(AdminUserDetailSerializer(user).data)

    @action(detail=True, methods=["post"], url_path="restrictions")
    def restrictions(self, request, pk=None):
        user = self.get_object()
        mode = request.data.get("mode", "add")
        service_ids = sorted(set(request.data.get("service_ids") or []))
        starts_at = request.data.get("starts_at")
        expires_at = request.data.get("expires_at")
        reason = _reason(request) if mode == "add" else ""
        if mode not in {"add", "remove"}:
            return Response({"mode": ["القيمة يجب أن تكون add أو remove."]}, status=400)
        if not service_ids:
            return Response({"detail": "اختر خدمة واحدة على الأقل."}, status=400)
        services = list(Service.objects.filter(id__in=service_ids))
        if len(services) != len(service_ids):
            return Response({"detail": "إحدى الخدمات غير موجودة."}, status=400)
        from rest_framework.fields import DateTimeField
        parsed_start = None
        parsed_expiry = None
        if starts_at:
            field = DateTimeField()
            try:
                parsed_start = field.to_internal_value(starts_at)
            except Exception:
                return Response({"starts_at": ["تاريخ البداية غير صالح."]}, status=400)
        if expires_at:
            field = DateTimeField()
            try:
                parsed_expiry = field.to_internal_value(expires_at)
            except Exception:
                return Response({"expires_at": ["تاريخ الانتهاء غير صالح."]}, status=400)
        if parsed_start and parsed_expiry and parsed_expiry <= parsed_start:
            return Response({"expires_at": ["تاريخ الانتهاء يجب أن يكون بعد تاريخ البداية."]}, status=400)
        with transaction.atomic():
            if mode == "remove":
                UserServiceRestriction.objects.filter(user=user, service_id__in=service_ids).delete()
            else:
                for service in services:
                    UserServiceRestriction.objects.update_or_create(
                        user=user, service=service,
                        defaults={
                            "reason": reason,
                            "starts_at": parsed_start,
                            "expires_at": parsed_expiry,
                            "created_by": request.user,
                        },
                    )
            record(
                f"admin.restrictions.{mode}", actor=request.user, request=request, target=user,
                metadata={"service_ids": service_ids, "reason": reason},
            )
        return Response(AdminUserDetailSerializer(user).data)

    @action(detail=True, methods=["post"], url_path="category-restrictions")
    def category_restrictions(self, request, pk=None):
        user = self.get_object()
        mode = request.data.get("mode", "add")
        category_ids = sorted(set(request.data.get("category_ids") or []))
        expires_at = request.data.get("expires_at")
        reason = _reason(request) if mode == "add" else ""
        if mode not in {"add", "remove"}:
            return Response({"mode": ["القيمة يجب أن تكون add أو remove."]}, status=400)
        if not category_ids:
            return Response({"detail": "اختر فئة واحدة على الأقل."}, status=400)
        categories = list(ServiceCategory.objects.filter(id__in=category_ids))
        if len(categories) != len(category_ids):
            return Response({"detail": "إحدى الفئات غير موجودة."}, status=400)
        from rest_framework.fields import DateTimeField
        parsed_expiry = None
        if expires_at:
            try:
                parsed_expiry = DateTimeField().to_internal_value(expires_at)
            except Exception:
                return Response({"expires_at": ["تاريخ الانتهاء غير صالح."]}, status=400)
        with transaction.atomic():
            if mode == "remove":
                UserCategoryRestriction.objects.filter(user=user, category_id__in=category_ids).delete()
            else:
                for category in categories:
                    UserCategoryRestriction.objects.update_or_create(
                        user=user, category=category,
                        defaults={
                            "reason": reason,
                            "expires_at": parsed_expiry,
                            "created_by": request.user,
                        },
                    )
            record(
                f"admin.category_restrictions.{mode}", actor=request.user, request=request, target=user,
                metadata={"category_ids": category_ids, "reason": reason},
            )
        return Response(AdminUserDetailSerializer(user).data)


class AdminServiceViewSet(viewsets.ModelViewSet):
    permission_classes = [IsPlatformAdmin]
    serializer_class = AdminServiceSerializer
    http_method_names = ["get", "patch", "head", "options", "post"]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ["name", "slug", "description"]
    ordering_fields = ["name", "sort_order", "created_at", "updated_at"]
    ordering = ["sort_order", "name"]

    def get_queryset(self):
        queryset = Service.objects.select_related("category").annotate(
            restrictions_count=Count("user_restrictions", distinct=True),
        )
        state = self.request.query_params.get("status")
        category = self.request.query_params.get("category")
        kind = self.request.query_params.get("kind")
        if state in {"active", "inactive"}:
            queryset = queryset.filter(is_active=state == "active")
        if category:
            queryset = queryset.filter(category_id=category)
        if kind:
            queryset = queryset.filter(kind=kind)
        return queryset

    @action(detail=True, methods=["post"])
    def deactivate(self, request, pk=None):
        reason = _reason(request)
        with transaction.atomic():
            service = Service.objects.select_for_update().get(pk=pk)
            service.is_active = False
            service.disabled_reason = reason
            service.disabled_at = timezone.now()
            service.disabled_by = request.user
            service.save(update_fields=["is_active", "disabled_reason", "disabled_at", "disabled_by", "updated_at"])
            record("admin.service.deactivated", actor=request.user, request=request, target=service, metadata={"reason": reason})
        return Response(self.get_serializer(service).data)

    @action(detail=True, methods=["post"])
    def activate(self, request, pk=None):
        with transaction.atomic():
            service = Service.objects.select_for_update().get(pk=pk)
            service.is_active = True
            service.disabled_reason = ""
            service.disabled_at = None
            service.disabled_by = None
            service.save(update_fields=["is_active", "disabled_reason", "disabled_at", "disabled_by", "updated_at"])
            record("admin.service.activated", actor=request.user, request=request, target=service)
        return Response(self.get_serializer(service).data)


class AdminJobViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsPlatformAdmin]
    serializer_class = AdminJobSerializer
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ["title", "created_by__username", "report_type__name", "task_id"]
    ordering_fields = ["created_at", "updated_at", "attempts", "status"]
    ordering = ["-created_at"]

    def get_queryset(self):
        queryset = GeneratedReport.objects.select_related("created_by", "report_type")
        state = self.request.query_params.get("status")
        if state:
            queryset = queryset.filter(status=state)
        return queryset

    @action(detail=True, methods=["post"])
    def retry(self, request, pk=None):
        report = self.get_object()
        if report.status != GeneratedReport.Status.FAILED:
            return Response({"detail": "يمكن إعادة تشغيل الوظائف الفاشلة فقط."}, status=409)
        with transaction.atomic():
            RetryReportUseCase().execute(report=report)
            record("admin.job.retried", actor=request.user, request=request, target=report)
        return Response(self.get_serializer(report).data, status=status.HTTP_202_ACCEPTED)

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        report = self.get_object()
        with transaction.atomic():
            transition(report, GeneratedReport.Status.CANCELLED)
            record("admin.job.cancelled", actor=request.user, request=request, target=report)
        return Response(self.get_serializer(report).data)


class AdminAuditViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    permission_classes = [IsPlatformAdmin]
    serializer_class = AuditEventSerializer
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ["action", "actor__username", "target_type", "target_id", "request_id", "ip_address"]
    ordering = ["-created_at"]

    def get_queryset(self):
        queryset = AuditEvent.objects.select_related("actor")
        outcome = self.request.query_params.get("outcome")
        action_name = self.request.query_params.get("action")
        if outcome:
            queryset = queryset.filter(outcome=outcome)
        if action_name:
            queryset = queryset.filter(action=action_name)
        return queryset


class AdminReportTypeViewSet(viewsets.ModelViewSet):
    permission_classes = [IsPlatformAdmin]
    serializer_class = AdminReportTypeSerializer
    http_method_names = ["get", "post", "patch", "head", "options"]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ["name", "slug", "description"]
    ordering = ["name"]

    def get_queryset(self):
        return ReportType.objects.annotate(
            versions_count=Count("versions", distinct=True),
            reports_count=Count("generated_reports", distinct=True),
        )

    def perform_create(self, serializer):
        report_type = serializer.save()
        record("admin.report_type.created", actor=self.request.user, request=self.request, target=report_type)

    def perform_update(self, serializer):
        report_type = serializer.save()
        record(
            "admin.report_type.updated",
            actor=self.request.user,
            request=self.request,
            target=report_type,
            metadata={"is_active": report_type.is_active},
        )


class AdminTemplateVersionViewSet(viewsets.GenericViewSet):
    permission_classes = [IsPlatformAdmin]
    serializer_class = AdminTemplateVersionSerializer
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    http_method_names = ["get", "post", "head", "options"]

    def get_queryset(self):
        return (
            ReportTemplateVersion.objects.filter(report_type_id=self.kwargs["report_type_pk"])
            .annotate(_has_reports=Exists(GeneratedReport.objects.filter(template_version_id=OuterRef("pk"))))
            .select_related("report_type", "created_by")
            .order_by("-version")
        )

    def list(self, request, *args, **kwargs):
        return Response(self.get_serializer(self.get_queryset(), many=True).data)

    def retrieve(self, request, *args, **kwargs):
        return Response(self.get_serializer(self.get_object()).data)

    def create(self, request, *args, **kwargs):
        upload_serializer = TemplateVersionUploadSerializer(data=request.data)
        upload_serializer.is_valid(raise_exception=True)
        report_type = get_object_or_404(ReportType, pk=self.kwargs["report_type_pk"])
        uploaded = upload_serializer.validated_data["template_file"]
        version = CreateTemplateVersionUseCase().execute(
            report_type=report_type,
            actor=request.user,
            filename=uploaded.name,
            data=uploaded.read(),
        )
        version._has_reports = False
        record(
            TEMPLATE_UPLOADED,
            actor=request.user,
            request=request,
            target=version,
            metadata={"report_type_id": report_type.pk},
        )
        return Response(
            self.get_serializer(version).data,
            status=status.HTTP_201_CREATED,
        )

    def validate_version(self, request, *args, **kwargs):
        version = ValidateTemplateVersionUseCase().execute(version=self.get_object())
        record(
            TEMPLATE_VALIDATED,
            actor=request.user,
            request=request,
            target=version,
            metadata={"reason": _reason(request)},
        )
        return Response(self.get_serializer(version).data)

    def activate(self, request, *args, **kwargs):
        version = ActivateTemplateVersionUseCase().execute(version=self.get_object())
        record(
            TEMPLATE_ACTIVATED,
            actor=request.user,
            request=request,
            target=version,
            metadata={"reason": _reason(request)},
        )
        return Response(self.get_serializer(version).data)

    def deactivate(self, request, *args, **kwargs):
        version = DeactivateTemplateVersionUseCase().execute(version=self.get_object())
        record(
            TEMPLATE_DEACTIVATED,
            actor=request.user,
            request=request,
            target=version,
            metadata={"reason": _reason(request)},
        )
        return Response(self.get_serializer(version).data)

    def archive(self, request, *args, **kwargs):
        version = ArchiveTemplateVersionUseCase().execute(version=self.get_object())
        record(
            TEMPLATE_ARCHIVED,
            actor=request.user,
            request=request,
            target=version,
            metadata={"reason": _reason(request)},
        )
        return Response(self.get_serializer(version).data)


class AdminAnalyticsView(APIView):
    permission_classes = [IsPlatformAdmin]

    def get(self, request):
        days = min(max(int(request.query_params.get("days", 30)), 7), 90)
        since = timezone.now() - timedelta(days=days)
        daily_reports = (
            GeneratedReport.objects.filter(created_at__gte=since)
            .annotate(day=TruncDate("created_at"))
            .values("day")
            .annotate(total=Count("id"), completed=Count("id", filter=Q(status="completed")), failed=Count("id", filter=Q(status="failed")))
            .order_by("day")
        )
        # Aggregate once per metric instead of 3 queries per service (avoids N+1).
        launch_counts: dict[str, dict[str, int]] = {}
        for row in (
            AuditEvent.objects.filter(
                action="service.launch", target_type="Service", created_at__gte=since
            )
            .values("target_id", "outcome")
            .annotate(count=Count("id"))
        ):
            launch_counts.setdefault(row["target_id"], {})[row["outcome"]] = row["count"]

        restricted_counts: dict[int, int] = {
            row["service_id"]: row["count"]
            for row in (
                UserServiceRestriction.objects.filter(
                    Q(expires_at__isnull=True) | Q(expires_at__gt=timezone.now())
                )
                .values("service_id")
                .annotate(count=Count("id"))
            )
        }

        services = []
        for service in Service.objects.select_related("category"):
            outcomes = launch_counts.get(str(service.id), {})
            services.append({
                "id": service.id, "name": service.name, "category": service.category.name,
                "launches": outcomes.get("success", 0),
                "denied": outcomes.get("denied", 0),
                "restricted_users": restricted_counts.get(service.id, 0),
            })
        return Response({
            "period_days": days,
            "daily_reports": list(daily_reports),
            "services": sorted(services, key=lambda item: item["launches"], reverse=True),
            "top_report_types": list(
                ReportType.objects.filter(generated_reports__created_at__gte=since)
                .values("id", "name").annotate(count=Count("generated_reports")).order_by("-count")[:10]
            ),
        })
