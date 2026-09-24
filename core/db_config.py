"""Database settings from DATABASE_URL, with SQLite for local development."""

import dj_database_url

SQLITE_CONFIG = {
    "ENGINE": "django.db.backends.sqlite3",
    "NAME": "db.sqlite3",
}

# Wrapper so constraint checks follow search_path (schema library).
# Django 5.2 already uses pg_table_is_visible; the backend still rewrites
# any leftover public-only SQL.
POSTGRES_ENGINES = {
    "django.db.backends.postgresql_psycopg2",
    "django.db.backends.postgresql",
}
SCHEMA_AWARE_ENGINE = "core.postgresql_backend"


def databases_from_url(database_url, conn_max_age=0):
    """Build Django's DATABASES setting.

    A non-empty ``database_url`` is parsed with dj-database-url. DigitalOcean
    Managed Postgres URLs should name database ``defaultdb`` and pass
    ``sslmode=require`` plus URL-encoded ``options=-csearch_path=library`` so
    connections use the ``library`` schema.

    An empty URL keeps the local SQLite database for offline development.
    """
    database_url = (database_url or "").strip()
    if not database_url:
        return {"default": dict(SQLITE_CONFIG)}
    database = dj_database_url.parse(database_url, conn_max_age=conn_max_age)
    if database.get("ENGINE") in POSTGRES_ENGINES:
        database["ENGINE"] = SCHEMA_AWARE_ENGINE
    return {"default": database}
