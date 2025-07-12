"""Admin configuration for the book app."""

from django.contrib import admin

from .models import Book, BorrowRecord, Category, Member, Profile, Publisher, UserActivity


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    """Admin configuration for Book model."""

    list_display = ("title", "author", "quantity", "status", "created_at")
    list_filter = ("status", "category", "publisher")
    search_fields = ("title", "author")


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    """Admin configuration for Category model."""

    list_display = ("name", "created_at")
    search_fields = ("name",)


@admin.register(Publisher)
class PublisherAdmin(admin.ModelAdmin):
    """Admin configuration for Publisher model."""

    list_display = ("name", "city", "contact", "created_at")
    search_fields = ("name", "city")


@admin.register(Member)
class MemberAdmin(admin.ModelAdmin):
    """Admin configuration for Member model."""

    list_display = ("name", "age", "gender", "city", "card_number", "expired_at")
    list_filter = ("gender", "city")
    search_fields = ("name", "card_number")


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    """Admin configuration for Profile model."""

    list_display = ("user", "phone_number", "email")
    search_fields = ("user__username", "phone_number", "email")


@admin.register(BorrowRecord)
class BorrowRecordAdmin(admin.ModelAdmin):
    """Admin configuration for BorrowRecord model."""

    list_display = ("borrower", "book", "quantity", "start_day", "end_day", "return_status")
    list_filter = ("open_or_close", "start_day", "end_day")
    search_fields = ("borrower", "book")


@admin.register(UserActivity)
class UserActivityAdmin(admin.ModelAdmin):
    """Admin configuration for UserActivity model."""

    list_display = ("created_by", "operation_type", "target_model", "created_at")
    list_filter = ("operation_type", "target_model", "created_at")
    search_fields = ("created_by", "target_model")