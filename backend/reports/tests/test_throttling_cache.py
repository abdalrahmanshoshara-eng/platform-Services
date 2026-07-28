"""B1: throttling must use a shared cache and registration must be rate-limited."""

import pytest
from django.core.cache import cache

import config.settings as prod_settings
from reports.accounts.throttling import RegisterRateThrottle
from reports.accounts.views import RegisterView

pytestmark = pytest.mark.django_db


def test_production_cache_is_a_shared_store():
    # A per-process LocMemCache would multiply every throttle limit by the number
    # of gunicorn workers; the deployed cache must be a cross-process backend.
    backend = prod_settings.CACHES["default"]["BACKEND"].lower()
    assert "redis" in backend
    assert "locmem" not in backend


def test_register_view_has_dedicated_throttle():
    assert RegisterRateThrottle in RegisterView.throttle_classes


def test_registration_is_rate_limited(api, monkeypatch):
    cache.clear()
    # Pin a low rate on the register throttle (a truthy class `rate` is used
    # verbatim by SimpleRateThrottle, bypassing the settings lookup that tests
    # disable). This exercises the real throttle + cache path end to end.
    monkeypatch.setattr(RegisterRateThrottle, "rate", "1/min", raising=False)

    first = api.post(
        "/api/auth/register/",
        {"username": "reg1", "email": "reg1@example.com", "password": "strongPa55phrase"},
        format="json",
    )
    assert first.status_code == 201
    second = api.post(
        "/api/auth/register/",
        {"username": "reg2", "email": "reg2@example.com", "password": "strongPa55phrase"},
        format="json",
    )
    assert second.status_code == 429
    cache.clear()
