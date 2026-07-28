from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import (
    AdminAnalyticsView,
    AdminAuditViewSet,
    AdminDashboardView,
    AdminJobViewSet,
    AdminReportTypeViewSet,
    AdminServiceViewSet,
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
] + router.urls
