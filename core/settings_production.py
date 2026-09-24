"""Production settings for Library Management System."""

import os

from decouple import config

from core.production_config import (
    caches_from_redis_url,
    production_debug,
    require_production_secret_key,
)

from .settings import *  # noqa: F403

# Fail at startup when SECRET_KEY is missing or still a committed placeholder.
SECRET_KEY = require_production_secret_key(config("SECRET_KEY", default=""))
# Default off. Set DEBUG=True in the environment only for a short-lived debug.
DEBUG = production_debug(config("DEBUG", default=False, cast=bool))
allowed_hosts_str = config("ALLOWED_HOSTS", default="localhost 127.0.0.1")
ALLOWED_HOSTS = allowed_hosts_str.split()

# Always add the Cloud Run URL pattern
ALLOWED_HOSTS.extend([
    "*.europe-west1.run.app",
    "*.run.app",  # Fallback for other regions
])

# Debug: Print ALLOWED_HOSTS to logs
import logging
logger = logging.getLogger(__name__)
logger.info(f"ALLOWED_HOSTS configured as: {ALLOWED_HOSTS}")

# Database: inherited from core.settings. Set DATABASE_URL for Postgres
# (defaultdb / schema library). Unset DATABASE_URL keeps SQLite.

# Google Cloud Storage Configuration
GS_BUCKET_NAME = config("GS_BUCKET_NAME", default="django-library-static")
GS_PROJECT_ID = config("GS_PROJECT_ID", default="django-library-466514")

# Static files (CSS, JavaScript, Images)
STATIC_URL = f"https://storage.googleapis.com/{GS_BUCKET_NAME}/static/"
STATICFILES_STORAGE = "storages.backends.gcloud.GoogleCloudStorage"
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, "static"),
]

# Media files
MEDIA_URL = f"https://storage.googleapis.com/{GS_BUCKET_NAME}/media/"
DEFAULT_FILE_STORAGE = "storages.backends.gcloud.GoogleCloudStorage"

# GCS Settings
GS_DEFAULT_ACL = "publicRead"
GS_FILE_OVERWRITE = False
GS_CACHE_CONTROL = "max-age=86400"  # 1 day

# Fallback to WhiteNoise if GCS is not available (for local testing)
if not GS_BUCKET_NAME or GS_BUCKET_NAME == "your-bucket-name":
    STATIC_URL = "/static/"
    STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")
    STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"
    MEDIA_URL = "/media/"
    MEDIA_ROOT = os.path.join(BASE_DIR, "media")

# Security settings
SECURE_SSL_REDIRECT = config("SECURE_SSL_REDIRECT", default=True, cast=bool)
SECURE_HSTS_SECONDS = config("SECURE_HSTS_SECONDS", default=31536000, cast=int)
SECURE_HSTS_INCLUDE_SUBDOMAINS = config(
    "SECURE_HSTS_INCLUDE_SUBDOMAINS", default=True, cast=bool
)
SECURE_HSTS_PRELOAD = config("SECURE_HSTS_PRELOAD", default=True, cast=bool)
SECURE_CONTENT_TYPE_NOSNIFF = config(
    "SECURE_CONTENT_TYPE_NOSNIFF", default=True, cast=bool
)
SECURE_BROWSER_XSS_FILTER = config("SECURE_BROWSER_XSS_FILTER", default=True, cast=bool)
SECURE_REFERRER_POLICY = config(
    "SECURE_REFERRER_POLICY", default="strict-origin-when-cross-origin"
)

# Session security
SESSION_COOKIE_SECURE = config("SESSION_COOKIE_SECURE", default=True, cast=bool)
SESSION_COOKIE_HTTPONLY = config("SESSION_COOKIE_HTTPONLY", default=True, cast=bool)
SESSION_COOKIE_SAMESITE = config("SESSION_COOKIE_SAMESITE", default="Lax")

# CSRF protection
CSRF_COOKIE_SECURE = config("CSRF_COOKIE_SECURE", default=True, cast=bool)
CSRF_COOKIE_HTTPONLY = config("CSRF_COOKIE_HTTPONLY", default=True, cast=bool)
CSRF_COOKIE_SAMESITE = config("CSRF_COOKIE_SAMESITE", default="Lax")

# Logging configuration
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {process:d} {thread:d} {message}",
            "style": "{",
        },
        "simple": {
            "format": "{levelname} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
        "file": {
            "class": "logging.FileHandler",
            "filename": "/var/log/django/library.log",
            "formatter": "verbose",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
    "loggers": {
        "django": {
            "handlers": ["console", "file"],
            "level": "INFO",
            "propagate": False,
        },
        "book": {
            "handlers": ["console", "file"],
            "level": "INFO",
            "propagate": False,
        },
    },
}

# Email configuration
EMAIL_BACKEND = config(
    "EMAIL_BACKEND", default="django.core.mail.backends.smtp.EmailBackend"
)
EMAIL_HOST = config("EMAIL_HOST", default="localhost")
EMAIL_PORT = config("EMAIL_PORT", default=587, cast=int)
EMAIL_USE_TLS = config("EMAIL_USE_TLS", default=True, cast=bool)
EMAIL_HOST_USER = config("EMAIL_HOST_USER", default="")
EMAIL_HOST_PASSWORD = config("EMAIL_HOST_PASSWORD", default="")
DEFAULT_FROM_EMAIL = config("DEFAULT_FROM_EMAIL", default="noreply@library.com")

# Django 2.2 cannot load django.core.cache.backends.redis.RedisCache, and that
# backend rejects CLIENT_CLASS. Use django-redis 5.2 instead.
CACHES = caches_from_redis_url(config("REDIS_URL", default=""))

# Session configuration
SESSION_ENGINE = "django.contrib.sessions.backends.cache"
SESSION_CACHE_ALIAS = "default"

# Performance optimizations
CONN_MAX_AGE = config("CONN_MAX_AGE", default=60, cast=int)

# File upload settings
FILE_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10MB

# Internationalization
USE_TZ = True
TIME_ZONE = config("TIME_ZONE", default="UTC")

# Admin settings
ADMIN_URL = config("ADMIN_URL", default="admin/")

# Third-party integrations
SENTRY_DSN = config("SENTRY_DSN", default="")
if SENTRY_DSN:
    import sentry_sdk
    from sentry_sdk.integrations.django import DjangoIntegration
    from sentry_sdk.integrations.logging import LoggingIntegration

    sentry_logging = LoggingIntegration(level=logging.INFO, event_level=logging.ERROR)

    sentry_sdk.init(
        dsn=SENTRY_DSN,
        integrations=[DjangoIntegration(), sentry_logging],
        traces_sample_rate=0.1,
        send_default_pii=True,
        environment=config("ENVIRONMENT", default="production"),
    )
