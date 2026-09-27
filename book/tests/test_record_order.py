"""Borrow-record list order keeps open loans first and stays deterministic."""

import re
from datetime import timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from book.models import BorrowRecord
from book.tests.helpers import make_staff, silence_weather


def _borrowers(response):
    html = response.content.decode()
    rows = re.findall(r"<tr>(.*?)</tr>", html, re.S)
    names = []
    for row in rows:
        cells = re.findall(r"<td>([^<]*)</td>", row)
        if cells:
            names.append(cells[0].strip())
    return names


class BorrowRecordListOrderTests(TestCase):
    def setUp(self):
        weather = silence_weather()
        weather.start()
        self.addCleanup(weather.stop)
        self.client.force_login(make_staff())

    def _stamp(self, record, **fields):
        BorrowRecord.objects.filter(pk=record.pk).update(**fields)
        record.refresh_from_db()
        return record

    def test_open_loans_come_first_then_newest_created_borrow(self):
        now = timezone.now()
        older_open = BorrowRecord.objects.create(borrower="older-open", book="Guide")
        tie_low = BorrowRecord.objects.create(borrower="tie-low", book="Guide")
        tie_high = BorrowRecord.objects.create(borrower="tie-high", book="Guide")
        newer_open = BorrowRecord.objects.create(borrower="newer-open", book="Guide")
        closed = BorrowRecord.objects.create(
            borrower="just-closed", book="Guide", open_or_close=1
        )
        self._stamp(older_open, created_at=now - timedelta(days=4), closed_at=None)
        shared = now - timedelta(days=2)
        self._stamp(tie_low, created_at=shared, closed_at=None)
        self._stamp(tie_high, created_at=shared, closed_at=None)
        self._stamp(newer_open, created_at=now - timedelta(days=1), closed_at=None)
        # A closed loan created later than every open loan still sorts after them.
        self._stamp(
            closed,
            created_at=now,
            closed_at=now,
            open_or_close=1,
        )

        expected = ["newer-open", "tie-high", "tie-low", "older-open", "just-closed"]
        listed = self.client.get(reverse("record_list"))
        self.assertEqual(listed.status_code, 200)
        self.assertEqual(_borrowers(listed), expected)

        explicit = self.client.get(reverse("record_list"), {"orderby": "-closed_at"})
        self.assertEqual(_borrowers(explicit), expected)

        fallback = self.client.get(reverse("record_list"), {"orderby": "not_a_field"})
        self.assertEqual(_borrowers(fallback), expected)

    def test_closed_loans_break_ties_by_created_at_then_id(self):
        now = timezone.now()
        older = BorrowRecord.objects.create(
            borrower="older-close", book="Guide", open_or_close=1
        )
        tie_low = BorrowRecord.objects.create(
            borrower="close-tie-low", book="Guide", open_or_close=1
        )
        tie_high = BorrowRecord.objects.create(
            borrower="close-tie-high", book="Guide", open_or_close=1
        )
        newest = BorrowRecord.objects.create(
            borrower="newest-close", book="Guide", open_or_close=1
        )
        shared_close = now - timedelta(days=1)
        shared_created = now - timedelta(days=3)
        self._stamp(
            older,
            closed_at=now - timedelta(days=5),
            created_at=now,
            open_or_close=1,
        )
        self._stamp(
            tie_low,
            closed_at=shared_close,
            created_at=shared_created,
            open_or_close=1,
        )
        self._stamp(
            tie_high,
            closed_at=shared_close,
            created_at=shared_created,
            open_or_close=1,
        )
        self._stamp(
            newest,
            closed_at=shared_close,
            created_at=now - timedelta(hours=1),
            open_or_close=1,
        )

        listed = self.client.get(reverse("record_list"))
        self.assertEqual(
            _borrowers(listed),
            ["newest-close", "close-tie-high", "close-tie-low", "older-close"],
        )

    def test_home_recent_closed_stays_newest_closed_first(self):
        now = timezone.now()
        older = BorrowRecord.objects.create(
            borrower="home-older", book="Guide", open_or_close=1
        )
        newer = BorrowRecord.objects.create(
            borrower="home-newer", book="Guide", open_or_close=1
        )
        still_open = BorrowRecord.objects.create(borrower="home-open", book="Guide")
        self._stamp(older, closed_at=now - timedelta(days=2), open_or_close=1)
        self._stamp(newer, closed_at=now, open_or_close=1)
        self._stamp(still_open, closed_at=None, created_at=now)

        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 200)
        html = response.content.decode()
        recent = html.split("Recent Closed Records", 1)[1].split("New members", 1)[0]
        self.assertLess(recent.index("home-newer"), recent.index("home-older"))
        self.assertNotIn("home-open", recent)
