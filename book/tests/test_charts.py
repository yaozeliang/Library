"""Charts page loads Highcharts from a public CDN and names the page honestly."""

from unittest.mock import patch

import requests
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from book.models import Book, BorrowRecord, Member


class ChartPageTests(TestCase):
    def setUp(self):
        weather = patch(
            "book.templatetags.book_extras.requests.get",
            side_effect=requests.RequestException("offline"),
        )
        weather.start()
        self.addCleanup(weather.stop)

        self.user = User.objects.create_user(username="staff", password="staff")
        self.client.login(username="staff", password="staff")

    def test_empty_library_shows_empty_states_and_not_morris(self):
        response = self.client.get(reverse("chart"))

        self.assertEqual(response.status_code, 200)
        html = response.content.decode()
        self.assertIn("Charts | Open Library", html)
        self.assertNotIn("Charts Morris", html)
        self.assertNotIn("code.highcharts.com", html)
        self.assertIn("cdn.jsdelivr.net/npm/highcharts@11.4.8/highcharts.js", html)
        self.assertIn("Highcharts.chart(", html)
        self.assertNotIn("new Highcharts.chart", html)
        self.assertIn('textOverflow: "none"', html)
        self.assertIn('whiteSpace: "normal"', html)
        self.assertIn("xAxis: categoryAxis(stockTitles)", html)
        self.assertIn("xAxis: categoryAxis(borrowTitles)", html)
        self.assertIn("{point.key}", html)
        self.assertContains(response, "No books in stock yet.")
        self.assertContains(response, "No borrow history yet.")
        self.assertContains(response, "No borrow records yet.")
        self.assertContains(response, "No members yet.")

    def test_seed_data_is_embedded_for_each_chart(self):
        Book.objects.create(
            author="Ada",
            title="Catalogued",
            description="On the shelf",
            quantity=4,
            total_borrow_times=2,
        )
        Member.objects.create(
            name="Pat",
            city="Paris",
            phone_number="0600000000",
        )
        BorrowRecord.objects.create(borrower="Pat", book="Catalogued", open_or_close=0)
        BorrowRecord.objects.create(borrower="Pat", book="Catalogued", open_or_close=1)

        response = self.client.get(reverse("chart"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Catalogued")
        self.assertNotContains(response, '<p class="chart-empty">No books in stock yet.</p>')
        self.assertNotContains(response, '<p class="chart-empty">No members yet.</p>')
        self.assertNotContains(response, '<p class="chart-empty">No borrow records yet.</p>')
