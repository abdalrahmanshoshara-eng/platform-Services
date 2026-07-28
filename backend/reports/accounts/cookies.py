"""Helpers to set/clear auth cookies consistently."""

from django.conf import settings


def _common():
    return {
        "httponly": settings.AUTH_COOKIE_HTTPONLY,
        "secure": settings.AUTH_COOKIE_SECURE,
        "samesite": settings.AUTH_COOKIE_SAMESITE,
        "path": settings.AUTH_COOKIE_PATH,
    }


def set_auth_cookies(response, access: str, refresh: str) -> None:
    access_max = int(settings.SIMPLE_JWT["ACCESS_TOKEN_LIFETIME"].total_seconds())
    refresh_max = int(settings.SIMPLE_JWT["REFRESH_TOKEN_LIFETIME"].total_seconds())
    response.set_cookie(settings.AUTH_COOKIE_ACCESS, access, max_age=access_max, **_common())
    response.set_cookie(settings.AUTH_COOKIE_REFRESH, refresh, max_age=refresh_max, **_common())


def clear_auth_cookies(response) -> None:
    response.delete_cookie(settings.AUTH_COOKIE_ACCESS, path=settings.AUTH_COOKIE_PATH)
    response.delete_cookie(settings.AUTH_COOKIE_REFRESH, path=settings.AUTH_COOKIE_PATH)
