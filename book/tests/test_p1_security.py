"""P1 security: auth on the API, POST-only mutations, and escaped HTML."""

from unittest.mock import patch

import requests
from django.contrib.auth.models import User
from django.core.exceptions import ImproperlyConfigured
from django.test import TestCase
from django.urls import reverse

from book.models import Book, BorrowRecord
from comment.models import Comment
from comment.sanitize import sanitize_comment_html
from core.production_config import (
    DJANGO_22_REDIS_BACKEND,
    INSECURE_SECRET_KEYS,
    LOCAL_DEV_SECRET_KEY,
    caches_from_redis_url,
    production_debug,
    require_production_secret_key,
)


def _silence_weather():
    return patch(
        "book.templatetags.book_extras.requests.get",
        side_effect=requests.RequestException("offline"),
    )


class ProductionSettingsGuardTests(TestCase):
    def test_missing_and_placeholder_secret_keys_are_rejected(self):
        for secret in INSECURE_SECRET_KEYS:
            with self.assertRaises(ImproperlyConfigured):
                require_production_secret_key(secret)
        with self.assertRaises(ImproperlyConfigured):
            require_production_secret_key(None)
        with self.assertRaises(ImproperlyConfigured):
            require_production_secret_key("  S#perS3crEt_1122  ")

    def test_unique_secret_key_is_kept(self):
        self.assertEqual(
            require_production_secret_key("  a-unique-production-secret  "),
            "a-unique-production-secret",
        )
        self.assertIn(LOCAL_DEV_SECRET_KEY, INSECURE_SECRET_KEYS)
        self.assertNotIn("S#perS3crEt_1122", {LOCAL_DEV_SECRET_KEY})

    def test_production_debug_defaults_to_false(self):
        self.assertIs(production_debug(None), False)
        self.assertIs(production_debug(False), False)
        self.assertIs(production_debug(True), True)

    def test_cache_backend_is_django_redis_not_django_4_redis(self):
        caches = caches_from_redis_url("")
        backend = caches["default"]["BACKEND"]
        self.assertEqual(backend, DJANGO_22_REDIS_BACKEND)
        self.assertEqual(backend, "django_redis.cache.RedisCache")
        self.assertNotEqual(
            backend, "django.core.cache.backends.redis.RedisCache"
        )
        self.assertEqual(
            caches["default"]["OPTIONS"]["CLIENT_CLASS"],
            "django_redis.client.DefaultClient",
        )
        self.assertEqual(
            caches_from_redis_url("redis://cache.internal:6379/2")["default"][
                "LOCATION"
            ],
            "redis://cache.internal:6379/2",
        )


class ApiAuthenticationTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="api-user", password="pass12345")

    def test_anonymous_cannot_read_or_write_members(self):
        listed = self.client.get("/api/members/")
        created = self.client.post(
            "/api/members/",
            {"name": "Pat", "city": "Paris", "phone_number": "0600000000"},
        )
        self.assertIn(listed.status_code, (401, 403))
        self.assertIn(created.status_code, (401, 403))
        self.assertFalse(listed.content and b"Pat" in listed.content)

    def test_authenticated_user_can_read_members(self):
        self.client.force_login(self.user)
        response = self.client.get("/api/members/")
        self.assertEqual(response.status_code, 200)

    def test_anonymous_book_list_is_rejected(self):
        response = self.client.get("/api/book-list/")
        self.assertIn(response.status_code, (401, 403))


class DestructiveGetTests(TestCase):
    def setUp(self):
        weather = _silence_weather()
        weather.start()
        self.addCleanup(weather.stop)
        self.user = User.objects.create_user(username="staffer", password="pass12345")
        self.client.force_login(self.user)
        self.book = Book.objects.create(
            author="Ada", title="Guide", description="A short guide"
        )

    def test_get_does_not_delete_a_book(self):
        response = self.client.get(reverse("book_delete", args=[self.book.pk]))
        self.assertEqual(response.status_code, 405)
        self.assertTrue(Book.objects.filter(pk=self.book.pk).exists())

    def test_post_deletes_a_book(self):
        response = self.client.post(
            reverse("book_delete", args=[self.book.pk]), follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Book.objects.filter(pk=self.book.pk).exists())

    def test_get_does_not_close_a_borrow_record(self):
        record = BorrowRecord.objects.create(borrower="Sam", book=self.book.title)
        response = self.client.get(reverse("record_close", args=[record.pk]))
        record.refresh_from_db()
        self.assertEqual(response.status_code, 405)
        self.assertEqual(record.open_or_close, 0)

    def test_post_closes_a_borrow_record(self):
        record = BorrowRecord.objects.create(borrower="Sam", book=self.book.title)
        response = self.client.post(
            reverse("record_close", args=[record.pk]), follow=True
        )
        record.refresh_from_db()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(record.open_or_close, 1)

    def test_get_logout_keeps_the_session(self):
        response = self.client.get(reverse("logout"))
        self.assertEqual(response.status_code, 405)
        self.assertEqual(self.client.session.get("_auth_user_id"), str(self.user.pk))
        home = self.client.get(reverse("home"))
        self.assertEqual(home.status_code, 200)

    def test_post_logout_ends_the_session(self):
        response = self.client.post(reverse("logout"), follow=True)
        self.assertEqual(response.status_code, 200)
        home = self.client.get(reverse("home"))
        self.assertEqual(home.status_code, 302)


class CommentAndChartXssTests(TestCase):
    def setUp(self):
        weather = _silence_weather()
        weather.start()
        self.addCleanup(weather.stop)
        self.user = User.objects.create_user(username="reader", password="pass12345")
        self.client.force_login(self.user)

    def test_script_tags_are_removed_from_stored_and_rendered_comments(self):
        book = Book.objects.create(
            author="Ada", title="Guide", description="A short guide"
        )
        payload = '<script>alert(1)</script><p>hello</p><a href="javascript:alert(1)">x</a>'
        comment = Comment.objects.create(book=book, user=self.user, body=payload)
        comment.refresh_from_db()
        self.assertNotIn("<script", comment.body)
        self.assertIn("hello", comment.body)
        self.assertNotIn("javascript:", comment.body)

        # Bypass save() so the template filter is what stops a stored payload.
        Comment.objects.filter(pk=comment.pk).update(body=payload)
        response = self.client.get(reverse("book_detail", args=[book.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "<script>alert(1)</script>", html=False)
        self.assertContains(response, "hello")

    def test_sanitize_comment_html_keeps_simple_formatting(self):
        cleaned = sanitize_comment_html("<p><strong>ok</strong></p>")
        self.assertIn("<strong>ok</strong>", cleaned)

    def test_chart_titles_are_not_injected_as_raw_script(self):
        Book.objects.create(
            author="Ada",
            title='</script><script>alert(1)</script>',
            description="A short guide",
            quantity=3,
        )
        response = self.client.get(reverse("chart"))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "</script><script>alert(1)</script>")
        self.assertContains(response, "chart-top-5-titles")
