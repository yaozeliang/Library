"""Database wrapper that introspects the active search_path schema."""

from datetime import timedelta

import django.db.backends.postgresql.base as postgresql_base
import django.db.backends.postgresql.utils as postgresql_utils
from django.db.backends.postgresql.base import (
    DatabaseWrapper as PostgresDatabaseWrapper,
)
from django.utils.timezone import utc

from .introspection import DatabaseIntrospection


def _utc_tzinfo_factory(offset):
    """Accept psycopg2 2.9's timedelta(0) as well as the older integer 0.

    Django 2.2.10 only treats a bare ``0`` as UTC, so timestamptz reads raise
    AssertionError on psycopg2 2.9+.
    """
    if offset != 0 and offset != timedelta(0):
        raise AssertionError("database connection isn't set to UTC")
    return utc


postgresql_utils.utc_tzinfo_factory = _utc_tzinfo_factory
postgresql_base.utc_tzinfo_factory = _utc_tzinfo_factory


class DatabaseWrapper(PostgresDatabaseWrapper):
    introspection_class = DatabaseIntrospection
