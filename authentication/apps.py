"""Authentication app configuration for the Library Management System."""

from django.apps import AppConfig


class AuthenticationConfig(AppConfig):
    """Configuration for the authentication app."""

    default_auto_field = "django.db.models.AutoField"
    name = "authentication"
