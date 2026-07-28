import os
from datetime import timedelta
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR.parent / ".env")


def env_bool(name: str, default: bool = False) -> bool:
    return os.getenv(name, str(default)).lower() in {"1", "true", "yes", "on"}


def env_list(name: str, default: str = "") -> list[str]:
    return [item.strip() for item in os.getenv(name, default).split(",") if item.strip()]


SECRET_KEY = os.getenv(
    "DJANGO_SECRET_KEY",
    "unsafe-development-fallback-change-before-production-32chars",
)
DEBUG = env_bool("DJANGO_DEBUG", True)
ALLOWED_HOSTS = env_list("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1,backend")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "corsheaders",
    "rest_framework",
    "rest_framework_simplejwt.token_blacklist",
    "reports",
]

AUTHENTICATION_BACKENDS = [
    "reports.accounts.backends.UsernameOrEmailBackend",
]

MIDDLEWARE = [
    "reports.shared.correlation.CorrelationIdMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"


def _database_from_url(url: str) -> dict:
    """Parse a DATABASE_URL (postgres://user:pass@host:port/name) without extra deps."""
    from urllib.parse import unquote, urlparse

    parsed = urlparse(url)
    engines = {
        "postgres": "django.db.backends.postgresql",
        "postgresql": "django.db.backends.postgresql",
    }
    return {
        "ENGINE": engines.get(parsed.scheme, "django.db.backends.postgresql"),
        "NAME": unquote(parsed.path.lstrip("/")),
        "USER": unquote(parsed.username or ""),
        "PASSWORD": unquote(parsed.password or ""),
        "HOST": parsed.hostname or "",
        "PORT": str(parsed.port or ""),
    }


DATABASE_URL = os.getenv("DATABASE_URL", "")
if DATABASE_URL:
    _default_db = _database_from_url(DATABASE_URL)
else:
    _default_db = {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.getenv("POSTGRES_DB", "reports_db"),
        "USER": os.getenv("POSTGRES_USER", "reports_user"),
        "PASSWORD": os.getenv("POSTGRES_PASSWORD", "reports_password"),
        "HOST": os.getenv("POSTGRES_HOST", "db"),
        "PORT": os.getenv("POSTGRES_PORT", "5432"),
    }
# Reasonable dev/prod connection settings (persistent connections).
_default_db["CONN_MAX_AGE"] = int(os.getenv("DJANGO_DB_CONN_MAX_AGE", "60"))
DATABASES = {"default": _default_db}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "ar"
# Storage/config timezone is UTC (USE_TZ stores UTC in the DB regardless).
TIME_ZONE = os.getenv("DJANGO_TIME_ZONE", "UTC")
# Timezone used only for human-readable timestamps rendered into reports.
REPORT_DISPLAY_TIMEZONE = os.getenv("REPORT_DISPLAY_TIMEZONE", "Asia/Damascus")
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

CORS_ALLOWED_ORIGINS = env_list("DJANGO_CORS_ALLOWED_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000")
CSRF_TRUSTED_ORIGINS = CORS_ALLOWED_ORIGINS

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "reports.accounts.authentication.CookieJWTAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 20,
    "EXCEPTION_HANDLER": "reports.shared.exception_handler.custom_exception_handler",
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.UserRateThrottle",
        "rest_framework.throttling.AnonRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "user": os.getenv("THROTTLE_USER", "1000/min"),
        "anon": os.getenv("THROTTLE_ANON", "100/min"),
        "login": os.getenv("THROTTLE_LOGIN", "10/min"),
        "refresh": os.getenv("THROTTLE_REFRESH", "20/min"),
        "report_create": os.getenv("THROTTLE_REPORT_CREATE", "30/min"),
        "download": os.getenv("THROTTLE_DOWNLOAD", "120/min"),
    },
}

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=int(os.getenv("ACCESS_TOKEN_MINUTES", "15"))),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=int(os.getenv("REFRESH_TOKEN_DAYS", "7"))),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "AUTH_HEADER_TYPES": ("Bearer",),
}

# ---- Auth cookies (HttpOnly; JS never reads tokens) ----
AUTH_COOKIE_ACCESS = "access_token"
AUTH_COOKIE_REFRESH = "refresh_token"
AUTH_COOKIE_HTTPONLY = True
AUTH_COOKIE_SECURE = env_bool("AUTH_COOKIE_SECURE", not DEBUG)
AUTH_COOKIE_SAMESITE = os.getenv("AUTH_COOKIE_SAMESITE", "Lax")
AUTH_COOKIE_PATH = "/"

# ---- CSRF (cookie auth requires CSRF protection for unsafe methods) ----
CSRF_COOKIE_HTTPONLY = False  # frontend reads it to echo X-CSRFToken
CSRF_COOKIE_SAMESITE = AUTH_COOKIE_SAMESITE
CSRF_COOKIE_SECURE = AUTH_COOKIE_SECURE
SESSION_COOKIE_SECURE = AUTH_COOKIE_SECURE
CORS_ALLOW_CREDENTIALS = True


# ---- Celery ----
CELERY_BROKER_URL = REDIS_URL
CELERY_RESULT_BACKEND = None  # PostgreSQL is the source of truth for report state.
CELERY_TASK_IGNORE_RESULT = True
CELERY_TASK_ACKS_LATE = True
CELERY_TASK_REJECT_ON_WORKER_LOST = True
CELERY_WORKER_PREFETCH_MULTIPLIER = 1
CELERY_TASK_SOFT_TIME_LIMIT = int(os.getenv("CELERY_TASK_SOFT_TIME_LIMIT", "180"))
CELERY_TASK_TIME_LIMIT = int(os.getenv("CELERY_TASK_TIME_LIMIT", "240"))
CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP = True
CELERY_TASK_ALWAYS_EAGER = env_bool("CELERY_TASK_ALWAYS_EAGER", False)
CELERY_TASK_EAGER_PROPAGATES = False
# Max generation retries (report is marked "failed" after this many attempts).
REPORT_MAX_ATTEMPTS = int(os.getenv("REPORT_MAX_ATTEMPTS", "3"))


# ---- Structured logging ----
LOG_LEVEL = os.getenv("DJANGO_LOG_LEVEL", "INFO")
LOG_FORMAT = os.getenv("DJANGO_LOG_FORMAT", "json")  # "json" or "plain"
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "filters": {
        "correlation": {"()": "reports.shared.logging.CorrelationIdFilter"},
    },
    "formatters": {
        "json": {"()": "reports.shared.logging.JsonFormatter"},
        "plain": {"format": "%(asctime)s %(levelname)s %(name)s [%(correlation_id)s] %(message)s"},
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "filters": ["correlation"],
            "formatter": LOG_FORMAT,
        },
    },
    "root": {"handlers": ["console"], "level": LOG_LEVEL},
    "loggers": {
        "django.request": {"handlers": ["console"], "level": "ERROR", "propagate": False},
        "reports": {"handlers": ["console"], "level": LOG_LEVEL, "propagate": False},
    },
}
