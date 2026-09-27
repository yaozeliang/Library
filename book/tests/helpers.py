"""Shared fixtures for library tests. Nothing here reads the demo database."""

from unittest.mock import patch

import requests
from django.contrib.auth.models import User


def silence_weather():
    """Navigation renders a weather widget that must not call the network."""
    return patch(
        "book.templatetags.book_extras.requests.get",
        side_effect=requests.RequestException("offline"),
    )


def make_staff(username="staff", password="staff-pass-1"):
    return User.objects.create_user(
        username=username, password=password, is_staff=True
    )


def make_admin(username="admin", password="admin-pass-1"):
    return User.objects.create_superuser(
        username=username, email=f"{username}@example.com", password=password
    )
