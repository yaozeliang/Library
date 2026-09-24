"""Book app configuration for the Library Management System."""

from django.apps import AppConfig


class BookConfig(AppConfig):
    """Configuration for the book app."""

    default_auto_field = "django.db.models.AutoField"
    name = "book"
