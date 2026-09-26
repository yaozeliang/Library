"""BorrowRecord book/borrower stay varchar names on Postgres."""

import importlib

from django.db import connection, models
from django.test import SimpleTestCase, TestCase

from book.forms import BorrowRecordCreateForm
from book.models import Book, BorrowRecord


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


class BorrowRecordBookLengthTests(TestCase):
    def test_book_matches_book_title_max_length(self):
        book_field = BorrowRecord._meta.get_field("book")
        title_field = Book._meta.get_field("title")
        self.assertEqual(book_field.max_length, title_field.max_length)
        self.assertEqual(book_field.max_length, 100)
        self.assertEqual(
            BorrowRecordCreateForm.base_fields["book"].max_length,
            book_field.max_length,
        )

    def test_form_accepts_a_full_title_and_rejects_a_longer_one(self):
        full_title = BorrowRecordCreateForm(
            data={"borrower": "Sam", "book": "T" * 100, "quantity": 1}
        )
        self.assertNotIn("book", full_title.errors)

        too_long = BorrowRecordCreateForm(
            data={"borrower": "Sam", "book": "T" * 101, "quantity": 1}
        )
        self.assertIn("book", too_long.errors)

        record = BorrowRecord.objects.create(borrower="Sam", book="T" * 100)
        record.refresh_from_db()
        self.assertEqual(record.book, "T" * 100)

    def test_postgres_widen_preserves_existing_titles(self):
        if connection.vendor != "postgresql":
            self.skipTest("varchar widen is exercised on Postgres")

        existing = "A" * 20
        record = BorrowRecord.objects.create(borrower="Sam", book=existing)
        with connection.cursor() as cursor:
            cursor.execute(
                "ALTER TABLE book_borrowrecord "
                "ALTER COLUMN book TYPE varchar(20)"
            )

        narrow = models.CharField(max_length=20)
        narrow.set_attributes_from_name("book")
        wide = models.CharField(max_length=100)
        wide.set_attributes_from_name("book")
        with connection.schema_editor() as editor:
            editor.alter_field(BorrowRecord, narrow, wide)

        record.refresh_from_db()
        self.assertEqual(record.book, existing)

        full_title = "B" * 100
        record.book = full_title
        record.save(update_fields=["book"])
        record.refresh_from_db()
        self.assertEqual(record.book, full_title)

        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT character_maximum_length
                FROM information_schema.columns
                WHERE table_schema = current_schema()
                  AND table_name = 'book_borrowrecord'
                  AND column_name = 'book'
                """
            )
            self.assertEqual(cursor.fetchone()[0], 100)
