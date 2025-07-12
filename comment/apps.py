"""Comment app configuration for the Library Management System."""

from django.apps import AppConfig


class CommentConfig(AppConfig):
    """Configuration for the comment app."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "comment"
