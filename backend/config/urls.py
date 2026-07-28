from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from config.health import liveness, readiness
from reports.accounts.views import LoginView, LogoutView, MeView, RefreshView, RegisterView

urlpatterns = [
    path("health/live", liveness, name="health-live"),
    path("health/ready", readiness, name="health-ready"),
    path("admin/", admin.site.urls),
    path("api/auth/login/", LoginView.as_view(), name="auth-login"),
    path("api/auth/register/", RegisterView.as_view(), name="auth-register"),
    path("api/auth/refresh/", RefreshView.as_view(), name="auth-refresh"),
    path("api/auth/logout/", LogoutView.as_view(), name="auth-logout"),
    path("api/auth/me/", MeView.as_view(), name="auth-me"),
    path("api/v1/admin/", include("reports.admin_api.urls")),
    path("api/", include("reports.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
