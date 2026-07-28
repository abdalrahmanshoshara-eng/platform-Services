from django.urls import path
from rest_framework.routers import DefaultRouter

from reports.catalog.views import ReportTypeViewSet
from reports.dashboard.views import DashboardStatsView
from reports.excel_contacts.views import ExcelContactsProcessView
from reports.generation.views import GeneratedReportViewSet
from reports.services_catalog.views import ServiceViewSet

router = DefaultRouter()
router.register(r"report-types", ReportTypeViewSet, basename="reporttype")
router.register(r"reports", GeneratedReportViewSet, basename="generatedreport")
router.register(r"services", ServiceViewSet, basename="service")

urlpatterns = [
    path("dashboard/stats/", DashboardStatsView.as_view(), name="dashboard-stats"),
    path(
        "tools/excel-contacts/process/",
        ExcelContactsProcessView.as_view(),
        name="excel-contacts-process",
    ),
]
urlpatterns += router.urls
