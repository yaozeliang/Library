"""Admin configuration for the comment app."""

from django.contrib import admin

from .models import Comment


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    """Admin configuration for Comment model."""

    list_display = ("user", "body", "created_at")
    list_filter = ("created_at",)
    search_fields = ("user__username", "body")
    readonly_fields = ("created_at", "updated_at")
