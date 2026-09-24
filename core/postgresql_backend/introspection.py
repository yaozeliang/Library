"""Postgres introspection that uses the connection search_path.

Django 2.2 looks up constraints and sequences in schema ``public`` only.
DigitalOcean connections set ``search_path`` to ``library``.
"""

from contextlib import contextmanager

from django.db.backends.postgresql.introspection import (
    DatabaseIntrospection as PostgresIntrospection,
)


class DatabaseIntrospection(PostgresIntrospection):
    def get_sequences(self, cursor, table_name, table_fields=()):
        with self._on_current_schema(cursor):
            return super().get_sequences(cursor, table_name, table_fields)

    def get_constraints(self, cursor, table_name):
        with self._on_current_schema(cursor):
            return super().get_constraints(cursor, table_name)

    @contextmanager
    def _on_current_schema(self, cursor):
        original_execute = cursor.execute

        def execute(sql, params=None):
            if isinstance(sql, str):
                sql = sql.replace(
                    "n.nspname = 'public'", "n.nspname = current_schema()"
                )
                if (
                    "ns.nspname = %s" in sql
                    and params
                    and params[0] == "public"
                ):
                    sql = sql.replace(
                        "ns.nspname = %s", "ns.nspname = current_schema()"
                    )
                    params = list(params)[1:]
            if params is None:
                return original_execute(sql)
            return original_execute(sql, params)

        cursor.execute = execute
        try:
            yield
        finally:
            cursor.execute = original_execute
