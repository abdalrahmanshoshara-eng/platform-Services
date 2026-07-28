from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import (
    AdminAnalyticsView,
    AdminAuditViewSet,
    AdminDashboardView,
    AdminJobViewSet,
    AdminReportTypeViewSet,
    AdminServiceViewSet,
    AdminTemplateVersionViewSet,
    AdminUserViewSet,
)

router = DefaultRouter()
router.register("users", AdminUserViewSet, basename="admin-user")
router.register("services", AdminServiceViewSet, basename="admin-service")
router.register("jobs", AdminJobViewSet, basename="admin-job")
router.register("audit-logs", AdminAuditViewSet, basename="admin-audit")
router.register("report-types", AdminReportTypeViewSet, basename="admin-report-type")

urlpatterns = [
    path("dashboard/", AdminDashboardView.as_view(), name="admin-dashboard"),
    path("analytics/", AdminAnalyticsView.as_view(), name="admin-analytics"),
    path(
        "report-types/<int:report_type_pk>/template-versions/",
        AdminTemplateVersionViewSet.as_view({"get": "list", "post": "create"}),
        name="admin-template-version-list",
    ),
    path(
        "report-types/<int:report_type_pk>/template-versions/<int:pk>/",
        AdminTemplateVersionViewSet.as_view({"get": "retrieve"}),
        name="admin-template-version-detail",
    ),
    path(
        "report-types/<int:report_type_pk>/template-versions/<int:pk>/validate/",
        AdminTemplateVersionViewSet.as_view({"post": "validate_version"}),
        name="admin-template-version-validate",
    ),
    path(
        "report-types/<int:report_type_pk>/template-versions/<int:pk>/activate/",
        AdminTemplateVersionViewSet.as_view({"post": "activate"}),
        name="admin-template-version-activate",
    ),
    path(
        "report-types/<int:report_type_pk>/template-versions/<int:pk>/deactivate/",
        AdminTemplateVersionViewSet.as_view({"post": "deactivate"}),
        name="admin-template-version-deactivate",
    ),
    path(
        "report-types/<int:report_type_pk>/template-versions/<int:pk>/archive/",
        AdminTemplateVersionViewSet.as_view({"post": "archive"}),
        name="admin-template-version-archive",
    ),
] + router.urls
