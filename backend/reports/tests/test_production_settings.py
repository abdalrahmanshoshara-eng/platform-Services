"""B3: production settings must fail closed and harden transport."""

import pytest
from django.core.exceptions import ImproperlyConfigured

import config.settings as base_settings


def test_debug_defaults_to_false_fail_closed():
    # A forgotten DJANGO_DEBUG must not silently enable debug mode.
    assert base_settings.env_bool("DJANGO_DEBUG_UNSET_PROBE") is False


def test_secret_guard_rejects_dev_secret_in_production():
    with pytest.raises(ImproperlyConfigured):
        base_settings.require_secure_secret(False, base_settings.INSECURE_SECRET_KEY)


def test_secret_guard_allows_dev_secret_in_debug():
    # Should not raise: dev/debug may use the shared fallback secret.
    base_settings.require_secure_secret(True, base_settings.INSECURE_SECRET_KEY)


def test_secret_guard_allows_real_secret_in_production():
    base_settings.require_secure_secret(False, "a-strong-unique-production-secret-key-value")


def test_security_headers_are_defined():
    assert base_settings.SECURE_CONTENT_TYPE_NOSNIFF is True
    assert base_settings.SECURE_REFERRER_POLICY == "same-origin"
    # Cookies follow the secure flag, which itself follows DEBUG.
    assert base_settings.CSRF_COOKIE_SECURE == base_settings.AUTH_COOKIE_SECURE
    assert base_settings.SESSION_COOKIE_SECURE == base_settings.AUTH_COOKIE_SECURE


def test_proxy_ssl_header_requires_explicit_trust():
    assert base_settings.proxy_ssl_header(False) is None
    assert base_settings.proxy_ssl_header(True) == ("HTTP_X_FORWARDED_PROTO", "https")


@pytest.mark.django_db
def test_login_still_works_under_test_settings(api, normal_user, login):
    # Guard against SSL-redirect breaking plain-HTTP test requests.
    resp = login(normal_user)
    assert resp.status_code == 200
