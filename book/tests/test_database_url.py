"""DATABASE_URL selects Postgres; an unset URL keeps SQLite."""

from decouple import config
from django.conf import settings
from django.test import SimpleTestCase

from core.db_config import databases_from_url

DO_DATABASE_URL = (
    "postgres://doadmin:not-a-real-password@example.db.ondigitalocean.com:25060"
    "/defaultdb?sslmode=require&options=-csearch_path%3Dlibrary"
)


class DatabaseUrlTests(SimpleTestCase):
    def test_unset_url_uses_sqlite(self):
        databases = databases_from_url("")
        self.assertEqual(
            databases["default"]["ENGINE"], "django.db.backends.sqlite3"
        )
        self.assertEqual(databases["default"]["NAME"], "db.sqlite3")

    def test_blank_url_uses_sqlite(self):
        databases = databases_from_url("   ")
        self.assertEqual(
            databases["default"]["ENGINE"], "django.db.backends.sqlite3"
        )

    def test_digitalocean_url_uses_defaultdb_and_library_schema(self):
        database = databases_from_url(DO_DATABASE_URL)["default"]
        self.assertEqual(database["ENGINE"], "core.postgresql_backend")
        self.assertEqual(database["NAME"], "defaultdb")
        self.assertEqual(database["USER"], "doadmin")
        self.assertEqual(database["HOST"], "example.db.ondigitalocean.com")
        self.assertEqual(database["PORT"], 25060)
        self.assertEqual(database["OPTIONS"]["sslmode"], "require")
        self.assertEqual(database["OPTIONS"]["options"], "-csearch_path=library")

    def test_settings_engine_matches_database_url(self):
        # The test runner rewrites NAME for the test database; ENGINE stays.
        database_url = config("DATABASE_URL", default="")
        expected = databases_from_url(database_url)["default"]["ENGINE"]
        self.assertEqual(settings.DATABASES["default"]["ENGINE"], expected)
