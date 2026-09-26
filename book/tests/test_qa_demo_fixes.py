"""QA demo regressions: pages that 500'd, and superuser vs staff group gates."""

import json
import os
from pathlib import Path
from unittest.mock import patch

import requests
from django.conf import settings
from django.contrib.auth.models import Group, User
from django.test import TestCase
from django.urls import reverse

from book.models import Book, Category, Member
from book.views import TODAY
from comment.models import Comment


def _silence_weather():
    return patch(
        "book.templatetags.book_extras.requests.get",
        side_effect=requests.RequestException("offline"),
    )


class DemoPageTests(TestCase):
    def setUp(self):
        weather = _silence_weather()
        weather.start()
        self.addCleanup(weather.stop)
        self.admin = User.objects.create_superuser(
            username="admin", email="admin@example.com", password="admin-pass-1"
        )
        self.staff = User.objects.create_user(
            username="staff", password="staff-pass-1", is_staff=True
        )

    def test_employee_update_renders_for_superuser_and_forbids_staff(self):
        url = reverse("employee_update", args=[self.staff.pk])

        self.client.force_login(self.staff)
        denied = self.client.get(url)
        self.assertEqual(denied.status_code, 403)

        self.client.force_login(self.admin)
        page = self.client.get(url)
        self.assertEqual(page.status_code, 200)
        self.assertContains(page, self.staff.username)
        self.assertContains(page, "Change Group")

        missing = self.client.get(reverse("employee_update", args=[99999]))
        self.assertEqual(missing.status_code, 404)

    def test_employee_update_post_assigns_group(self):
        self.client.force_login(self.admin)
        response = self.client.post(
            reverse("employee_update", args=[self.staff.pk]),
            {"logs": "on"},
        )
        self.assertRedirects(
            response, reverse("employees_detail", args=[self.staff.pk])
        )
        self.assertTrue(self.staff.groups.filter(name="logs").exists())
        self.assertFalse(self.staff.groups.filter(name="api").exists())

    def test_signup_page_renders_and_creates_a_normal_user(self):
        page = self.client.get(reverse("signup"))
        self.assertEqual(page.status_code, 200)
        self.assertContains(page, "Sign up")

        created = self.client.post(
            reverse("signup"),
            {
                "username": "newreader",
                "email": "reader@example.com",
                "first_name": "New",
                "last_name": "Reader",
                "password1": "library-pass-1",
                "password2": "library-pass-1",
            },
        )
        self.assertRedirects(created, reverse("login"))
        user = User.objects.get(username="newreader")
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)

    def test_comment_list_renders(self):
        book = Book.objects.create(
            author="Ada", title="Catalog Notes", description="A book"
        )
        Comment.objects.create(book=book, user=self.admin, body="Shelf note")

        anonymous = self.client.get("/comment/")
        self.assertEqual(anonymous.status_code, 200)
        self.assertContains(anonymous, "Shelf note")

        self.client.force_login(self.admin)
        logged_in = self.client.get(reverse("comment:comment_list"))
        self.assertEqual(logged_in.status_code, 200)
        self.assertContains(logged_in, "Catalog Notes")

    def test_borrow_autocomplete_returns_json(self):
        Member.objects.create(name="Ada Lovelace", city="Paris", phone_number="0601")
        Member.objects.create(name="Grace Hopper", city="Paris", phone_number="0602")
        Book.objects.create(author="Knuth", title="Concrete Mathematics", description="x")
        Book.objects.create(author="Other", title="Unrelated Title", description="y")

        self.client.force_login(self.staff)
        members = self.client.get(
            reverse("auto_member_name"),
            {"term": "Ada"},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        books = self.client.get(reverse("auto_book_name"), {"term": "Concrete"})

        self.assertEqual(members.status_code, 200)
        self.assertEqual(books.status_code, 200)
        self.assertEqual(members["Content-Type"], "application/json")
        self.assertEqual(json.loads(members.content), ["Ada Lovelace"])
        self.assertEqual(json.loads(books.content), ["Concrete Mathematics"])

        self.client.logout()
        anonymous = self.client.get(reverse("auto_member_name"), {"term": "Ada"})
        self.assertEqual(anonymous.status_code, 302)


class GroupAccessTests(TestCase):
    def setUp(self):
        weather = _silence_weather()
        weather.start()
        self.addCleanup(weather.stop)
        self.admin = User.objects.create_superuser(
            username="admin", email="admin@example.com", password="admin-pass-1"
        )
        self.staff = User.objects.create_user(
            username="staff", password="staff-pass-1", is_staff=True
        )
        self.category = Category.objects.create(name="Fiction")
        self.download_url = reverse(
            "data_download", args=[self.category._meta.db_table]
        )

    def _csv_path(self):
        return os.path.join(settings.BASE_DIR, "datacenter", f"Category_{TODAY}.csv")

    def test_superuser_passes_group_gates_without_membership(self):
        self.assertFalse(self.admin.groups.exists())
        self.client.force_login(self.admin)

        pages = [
            reverse("data_center"),
            reverse("user_activity_list"),
            reverse("employees_list"),
            reverse("notice_list"),
            reverse("api-overview"),
        ]
        for url in pages:
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200, url)

        sidebar = self.client.get(reverse("data_center"))
        self.assertContains(sidebar, "Data Center")
        self.assertContains(sidebar, "Logs")
        self.assertContains(sidebar, "API")

        existed = os.path.exists(self._csv_path())
        try:
            download = self.client.get(self.download_url)
            self.assertEqual(download.status_code, 200)
            self.assertIn("text/csv", download["Content-Type"])
        finally:
            if not existed and os.path.exists(self._csv_path()):
                os.remove(self._csv_path())

    def test_anonymous_group_pages_redirect_to_login(self):
        for url in (
            reverse("data_center"),
            reverse("user_activity_list"),
            self.download_url,
        ):
            response = self.client.get(url)
            self.assertEqual(response.status_code, 302, url)
            self.assertIn("/auth/login/", response.url)

    def test_staff_without_groups_is_forbidden(self):
        self.client.force_login(self.staff)
        for url in (
            reverse("data_center"),
            self.download_url,
            reverse("user_activity_list"),
            reverse("employees_list"),
            reverse("notice_list"),
            reverse("api-overview"),
            reverse("employee_update", args=[self.staff.pk]),
        ):
            response = self.client.get(url)
            self.assertEqual(response.status_code, 403, url)

    def test_staff_with_a_group_keeps_that_access_only(self):
        logs = Group.objects.create(name="logs")
        download = Group.objects.create(name="download_data")
        api = Group.objects.create(name="api")

        self.staff.groups.add(logs)
        self.client.force_login(self.staff)
        self.assertEqual(self.client.get(reverse("user_activity_list")).status_code, 200)
        self.assertEqual(self.client.get(reverse("data_center")).status_code, 403)
        self.assertEqual(self.client.get(reverse("api-overview")).status_code, 403)
        self.assertEqual(self.client.get(reverse("employees_list")).status_code, 403)
        self.assertEqual(self.client.get(reverse("notice_list")).status_code, 403)

        self.staff.groups.set([download])
        self.assertEqual(self.client.get(reverse("data_center")).status_code, 200)
        self.assertEqual(self.client.get(reverse("user_activity_list")).status_code, 403)
        existed = os.path.exists(self._csv_path())
        try:
            self.assertEqual(self.client.get(self.download_url).status_code, 200)
        finally:
            if not existed and os.path.exists(self._csv_path()):
                os.remove(self._csv_path())

        self.staff.groups.set([api])
        self.assertEqual(self.client.get(reverse("api-overview")).status_code, 200)
        self.assertEqual(self.client.get(self.download_url).status_code, 403)


class ContainerHealthcheckTests(TestCase):
    def test_healthcheck_probes_the_port_gunicorn_binds(self):
        root = Path(settings.BASE_DIR)
        dockerfile = (root / "Dockerfile").read_text()
        gunicorn = (root / "gunicorn-cfg.py").read_text()
        self.assertIn("http://127.0.0.1:8082/", dockerfile)
        self.assertNotIn("localhost:8000", dockerfile)
        self.assertIn("ENV PORT=8082", dockerfile)
        self.assertIn('os.environ.get("PORT", "8082")', gunicorn)
