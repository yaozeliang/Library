"""Comment models for the Library Management System."""

from ckeditor.fields import RichTextField
from django.contrib.auth.models import User
from django.db import models
from django.urls import reverse

from .sanitize import sanitize_comment_html


class Comment(models.Model):
    """Comment model for user feedback and discussions."""

    book = models.ForeignKey(
        "book.Book",
        on_delete=models.CASCADE,
        related_name="comments",
        null=True,
        blank=True,
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="comments")
    content = models.TextField(default="", blank=True)
    body = RichTextField(
        default="", blank=True
    )  # Rich text field for compatibility with existing templates
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        """Meta class for Comment model."""

        ordering = ["-created_at"]

    def save(self, *args, **kwargs):
        """Persist body only after unsafe HTML has been removed."""
        self.body = sanitize_comment_html(self.body)
        return super().save(*args, **kwargs)

    def __str__(self) -> str:
        """Return string representation of the comment."""
        return f"Comment by {self.user.username} on {self.created_at}"

    def get_absolute_url(self) -> str:
        """Return the URL for the comment detail view."""
        return reverse("comment_detail", kwargs={"pk": self.pk})
