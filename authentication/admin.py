"""Admin configuration for the authentication app."""

from django.contrib import admin

from .models import UserProfile


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    """Admin configuration for UserProfile model."""

    list_display = ("user", "bio")
    search_fields = ("user__username", "user__email")
