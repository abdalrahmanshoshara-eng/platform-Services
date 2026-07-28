"""User-facing application API routes shared by v1 and legacy aliases."""

from django.urls import include, path

from reports.accounts.views import LoginView, LogoutView, MeView, RefreshView, RegisterView

urlpatterns = [
    path("auth/login/", LoginView.as_view(), name="auth-login"),
    path("auth/register/", RegisterView.as_view(), name="auth-register"),
    path("auth/refresh/", RefreshView.as_view(), name="auth-refresh"),
    path("auth/logout/", LogoutView.as_view(), name="auth-logout"),
    path("auth/me/", MeView.as_view(), name="auth-me"),
    path("", include("reports.urls")),
]
