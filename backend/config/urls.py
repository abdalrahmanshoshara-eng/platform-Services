from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from config.health import liveness, readiness

infrastructure_urlpatterns = [
    path("health/live", liveness, name="health-live"),
    path("health/ready", readiness, name="health-ready"),
    path("admin/", admin.site.urls),
]

# Schema generators should receive this canonical-only list. The compatibility
# resolver below is deliberately excluded so paths and operation IDs are not duplicated.
canonical_api_urlpatterns = [
    path("api/v1/admin/", include("reports.admin_api.urls")),
    path("api/v1/", include("config.api_urls")),
]

legacy_api_urlpatterns = [
    path(
        "api/",
        include(("config.api_urls", "legacy_api"), namespace="legacy_api"),
    ),
]

urlpatterns = infrastructure_urlpatterns + canonical_api_urlpatterns + legacy_api_urlpatterns

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
