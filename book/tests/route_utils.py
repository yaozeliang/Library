"""Shared setup for route tests. No seed database; objects are created in setUp."""

from copy import deepcopy
from unittest.mock import patch

import requests
from django.conf import settings
from django.contrib.auth.models import User
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
class RouteFixture(TestCase):
    """Staff, superuser, and a plain user, plus one of each library object."""

    def setUp(self):
        weather = patch(
            "book.templatetags.book_extras.requests.get",
            side_effect=requests.RequestException("offline"),
        )
        weather.start()
        self.addCleanup(weather.stop)

        self.staff = User.objects.create_user(
            username="route-staff", password="pass12345", is_staff=True
        )
        self.superuser = User.objects.create_superuser(
            username="route-root",
            email="route-root@example.com",
            password="pass12345",
        )
        self.reader = User.objects.create_user(
            username="route-reader", password="pass12345"
        )
        self.client.logout()

    def login(self, user):
        self.client.force_login(user)

    def assert_redirects_to_login(self, url):
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302, url)
        self.assertIn("/auth/login/", response.url, url)
        return response
