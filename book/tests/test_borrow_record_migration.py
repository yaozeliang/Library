"""BorrowRecord book/borrower stay varchar names on Postgres."""

import importlib

from django.db import connection, models
from django.test import SimpleTestCase, TestCase


class BorrowRecordMigrationDefinitionTests(SimpleTestCase):
    def test_create_stores_names_not_foreign_keys(self):
        migration = importlib.import_module(
            "book.migrations.0002_borrowrecord"
        )
        fields = dict(migration.Migration.operations[0].fields)
        self.assertIsInstance(fields["book_name"], models.CharField)
        self.assertIsInstance(fields["borrower"], models.CharField)
        self.assertEqual(fields["book_name"].max_length, 20)
        self.assertEqual(fields["borrower"].max_length, 20)
        self.assertFalse(fields["book_name"].remote_field)
        self.assertFalse(fields["borrower"].remote_field)


class BorrowRecordNameColumnRepairTests(TestCase):
    def test_postgres_repairs_integer_foreign_key_columns(self):
        if connection.vendor != "postgresql":
            self.skipTest("integer FK repair is exercised on Postgres")

        repair = importlib.import_module(
            "book.migrations.0005_auto_20210803_2010"
        )
        convert = repair.convert_borrow_record_name_columns

        with connection.cursor() as cursor:
            cursor.execute('ALTER TABLE book_borrowrecord DROP COLUMN "book"')
            cursor.execute(
                'ALTER TABLE book_borrowrecord DROP COLUMN "borrower"'
            )
            cursor.execute(
                "ALTER TABLE book_borrowrecord "
                "ADD COLUMN book_id integer NOT NULL DEFAULT 0"
            )
            cursor.execute(
                "ALTER TABLE book_borrowrecord "
                "ADD COLUMN borrower_id integer NOT NULL DEFAULT 0"
            )
            cursor.execute(
                """
                ALTER TABLE book_borrowrecord
                ADD CONSTRAINT book_borrowrecord_book_id_test_fk
                FOREIGN KEY (book_id) REFERENCES book_book (id)
                DEFERRABLE INITIALLY DEFERRED
                """
            )
            cursor.execute(
                """
                ALTER TABLE book_borrowrecord
                ADD CONSTRAINT book_borrowrecord_borrower_id_test_fk
                FOREIGN KEY (borrower_id) REFERENCES book_member (id)
                DEFERRABLE INITIALLY DEFERRED
                """
            )

        with connection.schema_editor() as schema_editor:
            convert(None, schema_editor)

        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT column_name, data_type
                FROM information_schema.columns
                WHERE table_schema = current_schema()
                  AND table_name = 'book_borrowrecord'
                  AND column_name = ANY(%s)
                """,
                [["book", "borrower", "book_id", "borrower_id"]],
            )
            columns = dict(cursor.fetchall())
            cursor.execute(
                """
                SELECT c.conname
                FROM pg_constraint c
                JOIN pg_class t ON c.conrelid = t.oid
                JOIN pg_namespace n ON t.relnamespace = n.oid
                WHERE c.contype = 'f'
                  AND n.nspname = current_schema()
                  AND t.relname = 'book_borrowrecord'
                """
            )
            foreign_keys = [row[0] for row in cursor.fetchall()]

        self.assertEqual(columns["book"], "character varying")
        self.assertEqual(columns["borrower"], "character varying")
        self.assertNotIn("book_id", columns)
        self.assertNotIn("borrower_id", columns)
        self.assertEqual(foreign_keys, [])

    def test_postgres_repair_leaves_varchar_columns_alone(self):
        if connection.vendor != "postgresql":
            self.skipTest("integer FK repair is exercised on Postgres")

        repair = importlib.import_module(
            "book.migrations.0005_auto_20210803_2010"
        )
        convert = repair.convert_borrow_record_name_columns

        with connection.schema_editor() as schema_editor:
            convert(None, schema_editor)

        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT column_name, data_type
                FROM information_schema.columns
                WHERE table_schema = current_schema()
                  AND table_name = 'book_borrowrecord'
                  AND column_name = ANY(%s)
                """,
                [["book", "borrower"]],
            )
            columns = dict(cursor.fetchall())
        self.assertEqual(columns["book"], "character varying")
        self.assertEqual(columns["borrower"], "character varying")
