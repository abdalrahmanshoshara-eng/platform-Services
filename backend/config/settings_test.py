"""Portable test settings.

SQLite is the local default; CI can opt into PostgreSQL with
TEST_USE_POSTGRES=true and the normal database environment variables.
"""

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
