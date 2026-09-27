"""Book management models for the Library Management System."""

import uuid
from datetime import timedelta
from typing import Any

from dateutil.relativedelta import relativedelta
from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.urls import reverse
from django.utils import timezone
from PIL import Image

# from phonenumber_field.modelfields import PhoneNumberField

BOOK_STATUS = (
    (0, "On loan"),
    (1, "In Stock"),
)

FLOOR = (
    (1, "1st"),
    (2, "2nd"),
    (3, "3rd"),
)

OPERATION_TYPE = (
    ("success", "Create"),
    ("warning", "Update"),
    ("danger", "Delete"),
    ("info", "Close"),
)

GENDER = (
    ("m", "Male"),
    ("f", "Female"),
)

BORROW_RECORD_STATUS = (
    (0, "Open"),
    (1, "Closed"),
)


def default_borrow_end_day():
    """Return a due date one week from now. A callable so migrate stays stable."""
    return timezone.now() + timedelta(days=7)


class Category(models.Model):
    """Book category model."""

    name = models.CharField(max_length=50, blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self) -> str:
        """Return string representation of the category."""
        return self.name

    def get_absolute_url(self) -> str:
        """Return the URL for the category list view."""
        return reverse("category_list")


class Publisher(models.Model):
    """Book publisher model."""

    name = models.CharField(max_length=50, blank=True)
    city = models.CharField(max_length=50, blank=True)
    contact = models.EmailField(max_length=50, blank=True)
    # created_at = models.DateTimeField(auto_now_add=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_by = models.CharField(max_length=20, default="yaozeliang")
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        """Return string representation of the publisher."""
        return self.name

    def get_absolute_url(self) -> str:
        """Return the URL for the publisher list view."""
        return reverse("publisher_list")


class Book(models.Model):
    """Book model for library management."""

    author = models.CharField("Author", max_length=20)
    title = models.CharField("Title", max_length=100)
    description = models.TextField()
    created_at = models.DateTimeField("Created Time", default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    total_borrow_times = models.PositiveIntegerField(default=0)
    quantity = models.PositiveIntegerField(default=10)
    category = models.ForeignKey(
        Category,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="category",
    )

    publisher = models.ForeignKey(
        Publisher,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="publisher",
    )

    status = models.IntegerField(choices=BOOK_STATUS, default=1)
    floor_number = models.IntegerField(choices=FLOOR, default=1)
    bookshelf_number = models.CharField(
        "Bookshelf Number", max_length=10, default="0001"
    )
    updated_by = models.CharField(max_length=20, default="yaozeliang")

    def get_absolute_url(self) -> str:
        """Return the URL for the book list view."""
        return reverse("book_list")

    def __str__(self) -> str:
        """Return string representation of the book."""
        return self.title


class UserActivity(models.Model):
    """User activity tracking model."""

    created_by = models.CharField(default="", max_length=20)
    created_at = models.DateTimeField(auto_now_add=True)
    operation_type = models.CharField(
        choices=OPERATION_TYPE, default="success", max_length=20
    )
    target_model = models.CharField(default="", max_length=20)
    detail = models.CharField(default="", max_length=50)

    def get_absolute_url(self) -> str:
        """Return the URL for the user activity list view."""
        return reverse("user_activity_list")


class Member(models.Model):
    """Library member model."""

    name = models.CharField(max_length=50, blank=False)
    age = models.PositiveIntegerField(default=20)
    gender = models.CharField(max_length=10, choices=GENDER, default="m")

    city = models.CharField(max_length=20, blank=False)
    email = models.EmailField(max_length=50, blank=True)
    phone_number = models.CharField(max_length=30, blank=False)

    created_at = models.DateTimeField(default=timezone.now)
    created_by = models.CharField(max_length=20, default="")
    updated_by = models.CharField(max_length=20, default="")
    updated_at = models.DateTimeField(auto_now=True)

    card_id = models.UUIDField(unique=True, default=uuid.uuid4, editable=False)
    card_number = models.CharField(max_length=8, default="")
    expired_at = models.DateTimeField(default=timezone.now)

    def get_absolute_url(self) -> str:
        """Return the URL for the member list view."""
        return reverse("member_list")

    def save(self, *args: Any, **kwargs: Any) -> None:
        """Save the member with auto-generated card number and expiration date."""
        self.card_number = str(self.card_id)[:8]
        self.expired_at = timezone.now() + relativedelta(years=1)
        # A partial update would otherwise drop the generated card fields.
        update_fields = kwargs.get("update_fields")
        if update_fields is not None:
            kwargs["update_fields"] = list(
                set(update_fields) | {"card_number", "expired_at"}
            )
        return super().save(*args, **kwargs)

    def __str__(self) -> str:
        """Return string representation of the member."""
        return self.name


# UserProfile
class Profile(models.Model):
    """User profile model."""

    user = models.OneToOneField(User, null=True, on_delete=models.CASCADE)
    bio = models.TextField()
    profile_pic = models.ImageField(upload_to="profile/%Y%m%d/", blank=True, null=True)
    phone_number = models.CharField(max_length=30, blank=True)
    email = models.EmailField(max_length=50, blank=True)

    def save(self, *args: Any, **kwargs: Any) -> None:
        """Save the profile with image resizing."""
        # 调用原有的 save() 的功能
        profile = super().save(*args, **kwargs)

        # 固定宽度缩放图片大小
        if self.profile_pic and not kwargs.get("update_fields"):
            image = Image.open(self.profile_pic.path)
            (x, y) = image.size
            new_x = 400
            new_y = int(new_x * (y / x))
            resample = getattr(Image, "Resampling", Image).LANCZOS
            resized_image = image.resize((new_x, new_y), resample)
            resized_image.save(self.profile_pic.path)

        return profile

    def __str__(self) -> str:
        """Return string representation of the profile."""
        return str(self.user)

    def get_absolute_url(self) -> str:
        """Return the URL for the home view."""
        return reverse("home")


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Create a user profile when a new user is created."""
    if created:
        Profile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """Save the user profile when the user is saved."""
    if hasattr(instance, "profile"):
        instance.profile.save()


# Borrow Record
class BorrowRecord(models.Model):
    """Book borrowing record model."""

    borrower = models.CharField(blank=False, max_length=20)
    borrower_card = models.CharField(max_length=8, blank=True)
    borrower_email = models.EmailField(max_length=50, blank=True)
    borrower_phone_number = models.CharField(max_length=30, blank=True)
    # Same limit as Book.title so a stored borrow keeps the full title.
    book = models.CharField(blank=False, max_length=100)
    quantity = models.PositiveIntegerField(default=1)

    start_day = models.DateTimeField(default=timezone.now)
    end_day = models.DateTimeField(default=default_borrow_end_day)
    periode = models.PositiveIntegerField(default=0)

    open_or_close = models.IntegerField(choices=BORROW_RECORD_STATUS, default=0)
    delay_days = models.IntegerField(default=0)
    final_status = models.CharField(max_length=10, default="Unknown")

    created_at = models.DateTimeField(default=timezone.now)
    created_by = models.CharField(max_length=20, blank=True)
    closed_by = models.CharField(max_length=20, default="")
    # Stamped only when the loan is closed. auto_now refreshed this on every
    # save, so open loans showed a close date.
    closed_at = models.DateTimeField(null=True, blank=True)

    def _local_end_date(self):
        """Calendar due date of ``end_day`` in the active time zone.

        Aware values are converted with ``timezone.localdate``. Naive values
        already store a wall-clock date, so ``.date()`` is used as-is.
        """
        end_day = self.end_day
        if timezone.is_aware(end_day):
            return timezone.localdate(end_day)
        return end_day.date()

    def _calendar_delay_days(self) -> int:
        """Calendar days past the local due date, or 0 when not yet overdue.

        Due today is not overdue. The count is the difference of local dates,
        not the number of 24-hour periods between the two timestamps.
        """
        delay = (timezone.localdate() - self._local_end_date()).days
        if delay > 0:
            return delay
        return 0

    @property
    def return_status(self) -> str:
        """Return the current return status of the borrowed book.

        An open loan is overdue only when today's local date is strictly
        after the local date of ``end_day``. A loan due today is on time.
        """
        if self.open_or_close == 0:
            if self._calendar_delay_days() > 0:
                return "Overdue"
            return "On Time"
        return "Returned"

    @property
    def get_delay_number_days(self) -> int:
        """Calendar days past due for an open loan, else the stored delay.

        Closed records keep the ``delay_days`` saved when the loan was open
        or returned. They are not recomputed from today's date.
        """
        if self.open_or_close == 0:
            return self._calendar_delay_days()
        return self.delay_days

    def get_absolute_url(self) -> str:
        """Return the URL for the borrow record list view."""
        return reverse("record_list")

    def __str__(self) -> str:
        """Return string representation of the borrow record."""
        return f"{self.borrower} - {self.book}"

    def save(self, *args: Any, **kwargs: Any) -> None:
        """Save the borrow record and keep ``closed_at`` in step with status.

        An open loan has no close timestamp. While it stays open, ``delay_days``
        is the number of local calendar days past ``end_day`` (zero when that
        date is today or later). Closing does not recompute that value: the
        caller copies ``get_delay_number_days`` first, and this method leaves
        the stored delay alone once the loan is closed. The first save that
        marks the loan closed stamps ``closed_at``; later edits leave that
        stamp alone. Opening the loan again clears it. There is no dedicated
        reopen view; this covers any save that sets ``open_or_close`` back
        to open.
        """
        if self.open_or_close == 0:
            self.delay_days = self._calendar_delay_days()
            self.closed_at = None
        elif self.closed_at is None:
            self.closed_at = timezone.now()
        update_fields = kwargs.get("update_fields")
        if update_fields is not None:
            kwargs["update_fields"] = list(
                set(update_fields) | {"delay_days", "closed_at"}
            )
        return super().save(*args, **kwargs)
