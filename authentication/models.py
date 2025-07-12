"""Authentication models for the Library Management System."""

from django.db import models


class UserProfile(models.Model):
    """User profile model for authentication."""

    user = models.OneToOneField("auth.User", on_delete=models.CASCADE)
    bio = models.TextField(blank=True)
    profile_pic = models.ImageField(upload_to="profile_pics/", blank=True, null=True)

    def __str__(self) -> str:
        """Return string representation of the user profile."""
        return f"{self.user.username}'s Profile"
