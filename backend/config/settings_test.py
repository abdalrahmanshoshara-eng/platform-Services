"""Portable test settings.

SQLite is the local default; CI can opt into PostgreSQL with
TEST_USE_POSTGRES=true and the normal database environment variables.
"""

import os

# Set a deterministic posture BEFORE base settings load: DEBUG on (so the plain-HTTP
# test client is never redirected to HTTPS and cookies aren't Secure) and a real secret
# so the production secret guard never trips in a clean CI checkout that has no .env.
os.environ.setdefault("DJANGO_DEBUG", "True")
os.environ.setdefault("DJANGO_SECRET_KEY", "test-only-secret-key-with-at-least-thirty-two-bytes")

from .settings import *  # noqa
from .settings import BASE_DIR, REST_FRAMEWORK, env_bool

if not env_bool("TEST_USE_POSTGRES", False):
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "test.sqlite3",
        }
    }

REST_FRAMEWORK = {
    **REST_FRAMEWORK,
    "DEFAULT_THROTTLE_RATES": {k: None for k in REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"]},
}
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]
SECRET_KEY = "test-only-secret-key-with-at-least-thirty-two-bytes"

# Tests must not require a running Redis; use an in-process cache. Throttling is
# disabled by default above (rates=None) and re-enabled per-test where needed.
CACHES = {"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}}

# The test client speaks plain HTTP; never redirect to HTTPS or send HSTS here,
# regardless of how DEBUG resolves in the base settings.
SECURE_SSL_REDIRECT = False
SECURE_HSTS_SECONDS = 0
