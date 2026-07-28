"""Deprecated module location (Phase 3). Serializers moved to feature packages.
Kept as re-exports for backward compatibility only."""

from reports.accounts.serializers import LoginSerializer, UserSummarySerializer  # noqa: F401
from reports.catalog.serializers import ReportTypeSerializer  # noqa: F401
from reports.generation.serializers import (  # noqa: F401
    GeneratedReportCreateSerializer,
    GeneratedReportSerializer,
)
