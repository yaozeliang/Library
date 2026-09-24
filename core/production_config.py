"""Guards used by production settings.

Django 2.2 has no ``django.core.cache.backends.redis.RedisCache`` (that backend
arrived in Django 4.0). The ``CLIENT_CLASS`` option belongs to django-redis,
which on Django 2.2 must stay at 5.2.x.
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

# django-redis 5.2. The built-in Redis cache backend does not exist on Django 2.2.
DJANGO_22_REDIS_BACKEND = "django_redis.cache.RedisCache"


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
    """Cache settings that import on Django 2.2.

    An empty URL still points at local Redis, matching the previous default.
    The backend is django-redis, not Django 4's RedisCache, because Django 2.2
    cannot load ``django.core.cache.backends.redis`` and that backend does not
    accept ``CLIENT_CLASS``.
    """
    location = (redis_url or "").strip() or "redis://localhost:6379/1"
    return {
        "default": {
            "BACKEND": DJANGO_22_REDIS_BACKEND,
            "LOCATION": location,
            "OPTIONS": {
                "CLIENT_CLASS": "django_redis.client.DefaultClient",
            },
            "KEY_PREFIX": key_prefix,
            "TIMEOUT": timeout,
        }
    }
