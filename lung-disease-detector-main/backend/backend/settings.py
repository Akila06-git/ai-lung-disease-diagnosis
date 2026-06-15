from __future__ import annotations

import os
from pathlib import Path
from urllib.parse import urlparse

from decouple import config, Csv
import sentry_sdk


BASE_DIR = Path(__file__).resolve().parent.parent


# -----------------------------------------------------------------------------
# Core settings
# -----------------------------------------------------------------------------

SECRET_KEY = config("DJANGO_SECRET_KEY", default="changeme-in-development")
DEBUG = config("DEBUG", default=True, cast=bool)

ALLOWED_HOSTS: list[str] = config(
    "ALLOWED_HOSTS", default="localhost,127.0.0.1", cast=Csv()
)

# Trust Nginx proxy headers
USE_X_FORWARDED_HOST = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")


# -----------------------------------------------------------------------------
# Applications
# -----------------------------------------------------------------------------

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Third-party
    "rest_framework",
    "corsheaders",
    "django_filters",
    "django_prometheus",
    # Local
    "api",
]

MIDDLEWARE = [
    "django_prometheus.middleware.PrometheusBeforeMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "django_prometheus.middleware.PrometheusAfterMiddleware",
]

ROOT_URLCONF = "backend.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
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

WSGI_APPLICATION = "backend.wsgi.application"


# -----------------------------------------------------------------------------
# Database (PostgreSQL via DATABASE_URL)
# -----------------------------------------------------------------------------

def _parse_database_url(url: str) -> dict:
    """Parse a PostgreSQL-style DATABASE_URL into Django DATABASES dict."""
    parsed = urlparse(url)
    return {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": parsed.path.lstrip("/") or "postgres",
        "USER": parsed.username or "",
        "PASSWORD": parsed.password or "",
        "HOST": parsed.hostname or "localhost",
        "PORT": parsed.port or "",
    }


DATABASE_URL = config(
    "DATABASE_URL", default=""
)

if DATABASE_URL:
    DATABASES = {
        "default": _parse_database_url(DATABASE_URL),
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }


# -----------------------------------------------------------------------------
# Password validation
# -----------------------------------------------------------------------------

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# -----------------------------------------------------------------------------
# Internationalization
# -----------------------------------------------------------------------------

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True


# -----------------------------------------------------------------------------
# Static & media files
# -----------------------------------------------------------------------------

STATIC_URL = config("STATIC_URL", default="/static/")
STATIC_ROOT = config("STATIC_ROOT", default=str(BASE_DIR / "staticfiles"))
STATICFILES_DIRS: list[Path] = [BASE_DIR / "static"] if (BASE_DIR / "static").exists() else []

MEDIA_URL = config("MEDIA_URL", default="/media/")
MEDIA_ROOT = config("MEDIA_ROOT", default=str(BASE_DIR / "media"))


# -----------------------------------------------------------------------------
# File upload & security validation settings
# -----------------------------------------------------------------------------

MAX_UPLOAD_SIZE_BYTES: int = 10 * 1024 * 1024  # 10 MB
MIN_IMAGE_WIDTH: int = 224
MIN_IMAGE_HEIGHT: int = 224
ALLOWED_IMAGE_EXTENSIONS: tuple[str, ...] = (".jpg", ".jpeg", ".png", ".dcm", ".dicom")


# -----------------------------------------------------------------------------
# Django REST Framework
# -----------------------------------------------------------------------------

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
        "rest_framework.authentication.SessionAuthentication",
        "rest_framework.authentication.BasicAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.AllowAny",
    ],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 10,
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ],
}

from datetime import timedelta

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=60),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=1),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "AUTH_HEADER_TYPES": ("Bearer",),
}


# -----------------------------------------------------------------------------
# CORS
# -----------------------------------------------------------------------------

CORS_ALLOWED_ORIGINS: list[str] = config(
    "CORS_ALLOWED_ORIGINS",
    default="http://localhost:5173",
    cast=Csv(),
)

CORS_ALLOW_CREDENTIALS = True


# -----------------------------------------------------------------------------
# Celery / Redis
# -----------------------------------------------------------------------------

REDIS_URL = config("REDIS_URL", default="redis://localhost:6379/0")

CELERY_BROKER_URL = config("CELERY_BROKER_URL", default=REDIS_URL)
CELERY_RESULT_BACKEND = config("CELERY_RESULT_BACKEND", default="redis://localhost:6379/1")
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = TIME_ZONE
CELERY_TASK_ACKS_LATE = True
CELERY_TASK_SOFT_TIME_LIMIT = 60  # seconds
CELERY_TASK_TIME_LIMIT = 120

# Run tasks synchronously locally if worker is disabled
USE_WORKER = config("USE_WORKER", default=False, cast=bool)
CELERY_TASK_ALWAYS_EAGER = not USE_WORKER
CELERY_TASK_EAGER_PROPAGATES = True

# Celery Beat – periodic task schedule
CELERY_BEAT_SCHEDULE = {
    "monthly-model-retrain": {
        "task": "api.tasks.scheduled_retrain_task",
        "schedule": 30 * 24 * 60 * 60,  # every 30 days (in seconds)
    },
    "weekly-cleanup-old-predictions": {
        "task": "api.tasks.cleanup_old_predictions",
        "schedule": 7 * 24 * 60 * 60,  # every 7 days
        "args": (30,),
    },
}


# -----------------------------------------------------------------------------
# Observability (LGTM Stack)
# -----------------------------------------------------------------------------

LOKI_URL = config("LOKI_URL", default="http://localhost:3100/loki/api/v1/push")
ENABLE_LOKI = config("ENABLE_LOKI", default=False, cast=bool)
OTEL_EXPORTER_OTLP_ENDPOINT = config(
    "OTEL_EXPORTER_OTLP_ENDPOINT", default="http://localhost:4317"
)


# -----------------------------------------------------------------------------
# Logging
# -----------------------------------------------------------------------------

LOGS_DIR = BASE_DIR / "logs"
LOGS_DIR.mkdir(parents=True, exist_ok=True)

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "[{levelname}] {asctime} {name} {message}",
            "style": "{",
        },
        "simple": {
            "format": "[{levelname}] {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
        "file_info": {
            "level": "INFO",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": LOGS_DIR / "app.log",
            "maxBytes": 10 * 1024 * 1024,  # 10 MB
            "backupCount": 5,
            "formatter": "verbose",
            "encoding": "utf-8",
        },
        "file_error": {
            "level": "ERROR",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": LOGS_DIR / "error.log",
            "maxBytes": 10 * 1024 * 1024,  # 10 MB
            "backupCount": 5,
            "formatter": "verbose",
            "encoding": "utf-8",
        },
    },
    "loggers": {
        "django": {
            "handlers": ["console", "file_error"],
            "level": "INFO",
            "propagate": False,
        },
        "django.request": {
            "handlers": ["file_error", "console"],
            "level": "ERROR",
            "propagate": False,
        },
        "api": {
            "handlers": ["console", "file_info", "file_error"],
            "level": "INFO",
            "propagate": False,
        },
        "ml_model": {
            "handlers": ["console", "file_info", "file_error"],
            "level": "INFO",
            "propagate": False,
        },
        "celery": {
            "handlers": ["console", "file_info", "file_error"],
            "level": "INFO",
            "propagate": False,
        },
    },
    "root": {
        "handlers": ["console", "file_info", "file_error"],
        "level": "INFO",
    },
}

if ENABLE_LOKI:
    LOGGING["handlers"]["loki"] = {
        "level": "INFO",
        "class": "logging_loki.LokiHandler",
        "url": LOKI_URL,
        "tags": {"app": config("LOKI_APP_LABEL", default="backend")},
        "version": "1",
    }
    # Add loki handler to relevant loggers
    for logger_name in ["django", "api", "ml_model", "celery", "root"]:
        if logger_name in LOGGING["loggers"]:
            LOGGING["loggers"][logger_name]["handlers"].append("loki")
        elif logger_name == "root":
             LOGGING["root"]["handlers"].append("loki")


# -----------------------------------------------------------------------------
# Sentry (optional)
# -----------------------------------------------------------------------------

SENTRY_DSN = config("SENTRY_DSN", default="")
if SENTRY_DSN:
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        traces_sample_rate=0.1,
        send_default_pii=False,
    )


# -----------------------------------------------------------------------------
# Default auto field
# -----------------------------------------------------------------------------

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# -----------------------------------------------------------------------------
# Ollama LLM (local AI for symptom analysis)
# -----------------------------------------------------------------------------

OLLAMA_BASE_URL = config("OLLAMA_BASE_URL", default="http://localhost:11434")
USE_MEDLLAMA = config("USE_MEDLLAMA", default=False, cast=bool)
OLLAMA_MODEL = "medllama2" if USE_MEDLLAMA else config("OLLAMA_MODEL", default="tinyllama")
OLLAMA_TIMEOUT = config("OLLAMA_TIMEOUT", default=120, cast=int)
# -----------------------------------------------------------------------------
# Prediction Caching
# -----------------------------------------------------------------------------
# If False, every image upload will trigger a new prediction even if it was 
# previously processed. Useful for model testing.
ENABLE_IMAGE_CACHING = config("ENABLE_IMAGE_CACHING", default=False, cast=bool)

