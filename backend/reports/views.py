"""Deprecated module location (Phase 3). Views moved to feature packages:
- reports.accounts.views, reports.catalog.views,
- reports.generation.views, reports.dashboard.views
Kept as re-exports for backward compatibility only."""

from reports.accounts.views import LoginView, LogoutView, MeView  # noqa: F401
from reports.catalog.views import ReportTypeViewSet  # noqa: F401
from reports.dashboard.views import DashboardStatsView  # noqa: F401
from reports.generation.views import GeneratedReportViewSet  # noqa: F401
