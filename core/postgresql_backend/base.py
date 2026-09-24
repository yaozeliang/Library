"""Database wrapper that introspects the active search_path schema.

Django 5.2 looks up tables with ``pg_table_is_visible``, which follows
``search_path``. The introspection subclass still rewrites any leftover
``public``-only constraint SQL so schema ``library`` stays visible.
"""

from django.db.backends.postgresql.base import (
    DatabaseWrapper as PostgresDatabaseWrapper,
)

from .introspection import DatabaseIntrospection


class DatabaseWrapper(PostgresDatabaseWrapper):
    introspection_class = DatabaseIntrospection
