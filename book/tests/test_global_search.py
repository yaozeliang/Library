"""Global search redirects empty requests and still renders POST queries."""

from unittest.mock import patch

import requests
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from book.models import Book, BorrowRecord, Category, Member, Publisher


class GlobalSearchTests(TestCase):
    def setUp(self):
        weather = patch(
            "book.templatetags.book_extras.requests.get",
            side_effect=requests.RequestException("offline"),
        )
        weather.start()
        self.addCleanup(weather.stop)

        self.user = User.objects.create_user(username="searcher", password="pass12345")
        self.client.force_login(self.user)
        self.url = reverse("global_search")

        Category.objects.create(name="Science Fiction")
        Publisher.objects.create(
            name="Orbit Press", city="Paris", contact="orbit@example.com"
        )
        Book.objects.create(
            author="Ada", title="Guide to Galaxies", description="A short guide"
        )
        Member.objects.create(name="Sam Orbit", city="Lyon", phone_number="0600000000")
        BorrowRecord.objects.create(borrower="Sam Orbit", book="Guide")

    def test_authenticated_get_redirects_home(self):
        response = self.client.get(self.url)
        self.assertRedirects(response, reverse("home"))

    def test_empty_post_redirects_home(self):
        response = self.client.post(self.url, {"global_search": ""})
        self.assertRedirects(response, reverse("home"))

    def test_missing_search_field_redirects_home(self):
        response = self.client.post(self.url, {})
        self.assertRedirects(response, reverse("home"))

    def test_post_query_returns_matching_results(self):
        response = self.client.post(self.url, {"global_search": "Orbit"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Search Result")
        self.assertContains(response, "Orbit Press")
        self.assertContains(response, "Sam Orbit")
        self.assertNotContains(response, "Guide to Galaxies")
        self.assertNotContains(response, "Science Fiction")

    def test_post_query_matches_book_title(self):
        response = self.client.post(self.url, {"global_search": "Galaxies"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Guide to Galaxies")
        self.assertContains(response, "Ada")
        self.assertNotContains(response, "Orbit Press")
