"""Chart data embedded for the dashboard is valid JSON with empty and seeded rows."""

import json
import re

from django.test import TestCase
from django.urls import reverse

from book.models import Book, BorrowRecord, Member
from book.tests.helpers import make_staff, silence_weather

_SCRIPT = re.compile(
    r'<script id="([^"]+)" type="application/json">(.*?)</script>',
    re.DOTALL,
)


def _payloads(response):
    return {
        script_id: json.loads(body)
        for script_id, body in _SCRIPT.findall(response.content.decode())
    }


class ChartPayloadTests(TestCase):
    def setUp(self):
        weather = silence_weather()
        weather.start()
        self.addCleanup(weather.stop)
        self.client.force_login(make_staff())

    def test_empty_library_payloads_are_empty_lists_and_zero_counts(self):
        response = self.client.get(reverse("chart"))
        self.assertEqual(response.status_code, 200)
        data = _payloads(response)
        self.assertEqual(data["chart-top-5-titles"], [])
        self.assertEqual(data["chart-top-5-qty"], [])
        self.assertEqual(data["chart-top-borrow-titles"], [])
        self.assertEqual(data["chart-top-borrow-times"], [])
        self.assertEqual(data["chart-r-open"], 0)
        self.assertEqual(data["chart-r-close"], 0)
        self.assertEqual(data["chart-months-member"], [])
        self.assertEqual(data["chart-monthly-member"], [])

    def test_seeded_payloads_keep_parallel_shapes(self):
        Book.objects.create(
            author="Ada",
            title="Catalogued",
            description="On the shelf",
            quantity=4,
            total_borrow_times=2,
        )
        Book.objects.create(
            author="Grace",
            title="Second",
            description="Also on the shelf",
            quantity=1,
            total_borrow_times=0,
        )
        Member.objects.create(name="Pat", city="Paris", phone_number="0600000000")
        BorrowRecord.objects.create(borrower="Pat", book="Catalogued", open_or_close=0)
        BorrowRecord.objects.create(borrower="Pat", book="Second", open_or_close=1)

        response = self.client.get(reverse("chart"))
        data = _payloads(response)
        self.assertEqual(len(data["chart-top-5-titles"]), len(data["chart-top-5-qty"]))
        self.assertEqual(
            len(data["chart-top-borrow-titles"]), len(data["chart-top-borrow-times"])
        )
        self.assertIn("Catalogued", data["chart-top-5-titles"])
        self.assertTrue(all(isinstance(qty, int) for qty in data["chart-top-5-qty"]))
        self.assertTrue(all(isinstance(n, int) for n in data["chart-top-borrow-times"]))
        self.assertEqual(data["chart-r-open"], 1)
        self.assertEqual(data["chart-r-close"], 1)
        self.assertEqual(len(data["chart-months-member"]), len(data["chart-monthly-member"]))
        self.assertTrue(data["chart-months-member"])
        self.assertTrue(all(isinstance(n, int) for n in data["chart-monthly-member"]))
        for label in data["chart-months-member"]:
            self.assertRegex(label, r"^\d{2}/\d{4}$")
