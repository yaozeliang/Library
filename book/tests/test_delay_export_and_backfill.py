"""Live borrow delay in the CSV export, and the closed-loan backfill."""

import csv
import importlib
import io
import os
from datetime import date, datetime, timezone as datetime_timezone
from unittest.mock import patch

from django.apps import apps
from django.conf import settings
from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from book.models import BorrowRecord
from book.views import TODAY


def _paris(wall_clock):
    """Aware instant for a Europe/Paris wall time."""
    return timezone.make_aware(wall_clock)


@override_settings(TIME_ZONE="Europe/Paris")
class BorrowRecordDelayExportTests(TestCase):
    """Open loans export the live delay. Closed loans export the stored one."""

    def setUp(self):
        self.admin = User.objects.create_superuser(
            username="admin", email="admin@example.com", password="admin-pass-1"
        )
        self.client.force_login(self.admin)
        # 15:30 in Paris, so the local calendar date is 27 September.
        frozen = _paris(datetime(2026, 9, 27, 15, 30))
        patcher = patch("django.utils.timezone.now", return_value=frozen)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.csv_path = os.path.join(
            settings.BASE_DIR, "datacenter", f"BorrowRecord_{TODAY}.csv"
        )

    def test_open_overdue_csv_writes_live_delay_and_closed_keeps_stored(self):
        # Due 19 September: eight local calendar days before the frozen today.
        # save() stores that live count; the row is then made stale (3).
        open_record = BorrowRecord.objects.create(
            borrower="OpenLate",
            book="Guide",
            end_day=_paris(datetime(2026, 9, 19, 23, 0)),
        )
        BorrowRecord.objects.filter(pk=open_record.pk).update(delay_days=3)
        open_record.refresh_from_db()
        self.assertEqual(open_record.delay_days, 3)
        self.assertEqual(open_record.get_delay_number_days, 8)

        # Closed long after the due date, but the stored delay is what was
        # saved at close time. The list helper returns that stored value.
        closed = BorrowRecord.objects.create(
            borrower="Shut",
            book="Guide",
            end_day=_paris(datetime(2026, 9, 1, 9, 0)),
            open_or_close=1,
            delay_days=4,
            closed_at=_paris(datetime(2026, 9, 10, 9, 0)),
        )
        self.assertEqual(closed.get_delay_number_days, 4)
        self.assertEqual(closed.delay_days, 4)

        existed = os.path.exists(self.csv_path)
        try:
            response = self.client.get(
                reverse("data_download", args=[BorrowRecord._meta.db_table])
            )
            self.assertEqual(response.status_code, 200)
            self.assertIn("text/csv", response["Content-Type"])
            rows = list(
                csv.DictReader(io.StringIO(response.content.decode("utf-8")))
            )
        finally:
            if not existed and os.path.exists(self.csv_path):
                os.remove(self.csv_path)

        expected_columns = [
            field.attname for field in BorrowRecord._meta.concrete_fields
        ]
        self.assertEqual(list(rows[0].keys()), expected_columns)
        by_borrower = {row["borrower"]: row for row in rows}
        self.assertEqual(by_borrower["OpenLate"]["delay_days"], "8")
        self.assertEqual(by_borrower["OpenLate"]["open_or_close"], "0")
        self.assertEqual(by_borrower["Shut"]["delay_days"], "4")
        self.assertEqual(by_borrower["Shut"]["open_or_close"], "1")

        open_record.refresh_from_db()
        closed.refresh_from_db()
        self.assertEqual(open_record.delay_days, 3)
        self.assertEqual(closed.delay_days, 4)


@override_settings(TIME_ZONE="Europe/Paris")
class ClosedBorrowDelayBackfillTests(TestCase):
    """Backfill delay_days from Paris calendar dates, without save()."""

    def _migration(self):
        return importlib.import_module(
            "book.migrations.0039_backfill_closed_borrowrecord_delay_days"
        )

    def test_naive_datetimes_use_their_wall_clock_date(self):
        migration = self._migration()
        self.assertEqual(
            migration._europe_paris_date(datetime(2026, 9, 28, 0, 30)),
            date(2026, 9, 28),
        )
        self.assertEqual(
            migration._europe_paris_date(datetime(2026, 9, 22, 23, 0)),
            date(2026, 9, 22),
        )
        self.assertIsNone(migration._europe_paris_date(None))

    def test_backfill_uses_paris_dates_and_leaves_other_rows_alone(self):
        migration = self._migration()
        due = date(2026, 9, 21)
        closed_on = date(2026, 9, 27)
        self.assertEqual((closed_on - due).days, 6)

        # Due at noon Paris (same UTC day). Closed at 00:30 Paris on D+6,
        # which is 22:30 UTC on the previous day.
        overdue = BorrowRecord.objects.create(
            borrower="Late",
            book="Guide",
            end_day=_paris(datetime(2026, 9, 21, 12, 0)),
            open_or_close=1,
            delay_days=0,
            closed_at=_paris(datetime(2026, 9, 27, 0, 30)),
        )
        overdue.refresh_from_db()
        self.assertEqual(timezone.localtime(overdue.closed_at).date(), closed_on)
        self.assertEqual(
            overdue.closed_at.astimezone(datetime_timezone.utc).date(),
            date(2026, 9, 26),
        )
        self.assertEqual(timezone.localtime(overdue.end_day).date(), due)
        self.assertEqual(overdue.closed_at.utcoffset().total_seconds(), 0)
        overdue_closed_at = overdue.closed_at
        overdue_end_day = overdue.end_day
        overdue_created_at = overdue.created_at

        on_time = BorrowRecord.objects.create(
            borrower="Prompt",
            book="Guide",
            end_day=_paris(datetime(2026, 9, 20, 10, 0)),
            open_or_close=1,
            delay_days=0,
            closed_at=_paris(datetime(2026, 9, 20, 18, 0)),
        )
        already = BorrowRecord.objects.create(
            borrower="Stored",
            book="Guide",
            end_day=_paris(datetime(2026, 9, 1, 10, 0)),
            open_or_close=1,
            delay_days=3,
            closed_at=_paris(datetime(2026, 9, 20, 10, 0)),
        )
        missing_stamp = BorrowRecord.objects.create(
            borrower="NoStamp",
            book="Guide",
            end_day=_paris(datetime(2026, 9, 1, 10, 0)),
            open_or_close=1,
            delay_days=0,
            closed_at=_paris(datetime(2026, 9, 20, 10, 0)),
        )
        BorrowRecord.objects.filter(pk=missing_stamp.pk).update(closed_at=None)

        open_record = BorrowRecord.objects.create(
            borrower="StillOpen",
            book="Guide",
            end_day=_paris(datetime(2026, 9, 1, 10, 0)),
        )
        open_closed_at = _paris(datetime(2026, 9, 20, 10, 0))
        BorrowRecord.objects.filter(pk=open_record.pk).update(
            delay_days=0,
            closed_at=open_closed_at,
        )

        migration.backfill_closed_borrow_delay_days(apps, None)

        overdue.refresh_from_db()
        on_time.refresh_from_db()
        already.refresh_from_db()
        missing_stamp.refresh_from_db()
        open_record.refresh_from_db()

        self.assertEqual(overdue.delay_days, 6)
        self.assertEqual(overdue.closed_at, overdue_closed_at)
        self.assertEqual(overdue.end_day, overdue_end_day)
        self.assertEqual(overdue.created_at, overdue_created_at)
        self.assertEqual(overdue.open_or_close, 1)
        self.assertEqual(overdue.borrower, "Late")

        self.assertEqual(on_time.delay_days, 0)
        self.assertEqual(already.delay_days, 3)
        self.assertEqual(missing_stamp.delay_days, 0)
        self.assertIsNone(missing_stamp.closed_at)

        self.assertEqual(open_record.delay_days, 0)
        self.assertEqual(open_record.open_or_close, 0)
        self.assertEqual(open_record.closed_at, open_closed_at)
