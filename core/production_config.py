"""Guards used by production settings.

Django 4.0+ provides ``django.core.cache.backends.redis.RedisCache``. That
backend does not accept django-redis' ``CLIENT_CLASS`` option, so production
uses the built-in backend and the ``redis`` package.
"""

from django.core.exceptions import ImproperlyConfigured

# Local ``core.settings`` may use this when SECRET_KEY is unset. Production
# settings reject it.
LOCAL_DEV_SECRET_KEY = "local-dev-only-not-for-production"

# Placeholders that have shipped in this repo or in env.example. None of them
# is acceptable once production settings are loaded.
INSECURE_SECRET_KEYS = frozenset(
    {
        "",
        "S#perS3crEt_1122",
        "your-secret-key-here-change-this-in-production",
        "build-secret-key",
        LOCAL_DEV_SECRET_KEY,
        "change-me",
    }
)

REDIS_CACHE_BACKEND = "django.core.cache.backends.redis.RedisCache"


def require_production_secret_key(secret_key):
    """Return a production SECRET_KEY or raise if it is missing or a placeholder."""
    cleaned = (secret_key or "").strip()
    if cleaned in INSECURE_SECRET_KEYS:
        raise ImproperlyConfigured(
            "SECRET_KEY must be set to a unique value in the environment when "
            "DJANGO_SETTINGS_MODULE=core.settings_production."
        )
    return cleaned


def production_debug(value=None):
    """Production DEBUG defaults to False. An explicit value is kept."""
    if value is None:
        return False
    return bool(value)


def caches_from_redis_url(redis_url, key_prefix="library", timeout=300):
    """Cache settings for Django's built-in Redis backend.

    An empty URL still points at local Redis. ``CLIENT_CLASS`` is omitted
    because the built-in backend rejects django-redis options.
    """
    location = (redis_url or "").strip() or "redis://localhost:6379/1"
    return {
        "default": {
            "BACKEND": REDIS_CACHE_BACKEND,
            "LOCATION": location,
            "KEY_PREFIX": key_prefix,
            "TIMEOUT": timeout,
        }
    }
