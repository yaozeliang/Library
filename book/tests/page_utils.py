"""Shared setup for page tests. Objects are created in setUp, not from the seed database."""

from copy import deepcopy
from unittest.mock import patch

import re

import requests
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.staticfiles import finders
from django.test import TestCase, override_settings


class InvalidTemplateVariable(str):
    """Raise when a template prints a variable that was never provided."""

    def __mod__(self, other):
        raise AssertionError(f"Missing template variable: {other}")


def strict_templates():
    templates = deepcopy(settings.TEMPLATES)
    options = dict(templates[0].get("OPTIONS") or {})
    options["string_if_invalid"] = InvalidTemplateVariable("%s")
    templates[0]["OPTIONS"] = options
    return templates


@override_settings(TEMPLATES=strict_templates())
class PageFixture(TestCase):
    """Staff, superuser, and a plain user. The weather widget is offline."""

    def setUp(self):
        weather = patch(
            "book.templatetags.book_extras.requests.get",
            side_effect=requests.RequestException("offline"),
        )
        weather.start()
        self.addCleanup(weather.stop)

        self.staff = User.objects.create_user(
            username="page-staff", password="pass12345", is_staff=True
        )
        self.superuser = User.objects.create_superuser(
            username="page-root",
            email="page-root@example.com",
            password="pass12345",
        )
        self.reader = User.objects.create_user(
            username="page-reader", password="pass12345"
        )
        self.client.logout()

    def login(self, user):
        self.client.force_login(user)

    def assert_redirects_to_login(self, url):
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302, url)
        self.assertIn("/auth/login/", response.url, url)
        return response

    def assert_local_static_exists(self, response):
        """Every live same-origin /static/ reference on the page resolves to a file."""
        html = re.sub(r"<!--.*?-->", "", response.content.decode(), flags=re.S)
        prefix = settings.STATIC_URL
        for quoted in html.split(prefix)[1:]:
            relative = quoted.split('"', 1)[0].split("'", 1)[0].split("?", 1)[0]
            if not relative or relative.startswith(("http://", "https://")):
                continue
            self.assertIsNotNone(
                finders.find(relative),
                f"missing static file {prefix}{relative}",
            )
