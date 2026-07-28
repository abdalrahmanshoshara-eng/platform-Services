"""Fail-fast configuration checks for production mode (DEBUG=False)."""

from django.conf import settings
from django.core.checks import Error, register

INSECURE_SECRETS = {"change-me", "change-me-please", ""}
DEFAULT_DB_PASSWORDS = {"reports_password"}


@register()
def production_safety_checks(app_configs, **kwargs):
    errors = []
    if settings.DEBUG:
        return errors  # only enforced in production mode

    if settings.SECRET_KEY in INSECURE_SECRETS:
        errors.append(Error("DJANGO_SECRET_KEY is default/empty in production.", id="reports.E001"))
    db_password = settings.DATABASES["default"].get("PASSWORD", "")
    if db_password in DEFAULT_DB_PASSWORDS:
        errors.append(Error("Default PostgreSQL password used in production.", id="reports.E002"))
    if not settings.AUTH_COOKIE_SECURE:
        errors.append(Error("AUTH_COOKIE_SECURE must be true in production.", id="reports.E003"))
    return errors
