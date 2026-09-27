"""Model string forms, constraints, computed fields, and save/signal side effects."""

import io
import tempfile
from datetime import date, datetime, timedelta, timezone as datetime_timezone
from unittest.mock import patch

from django.apps import apps

from django.contrib.auth.models import User
from django.core.files.base import ContentFile
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from PIL import Image

from book.models import (
    Book,
    BorrowRecord,
    Category,
    Member,
    Profile,
    Publisher,
    UserActivity,
    default_borrow_end_day,
)
from comment.models import Comment


class CategoryPublisherBookTests(TestCase):
    def test_string_and_absolute_urls(self):
        category = Category.objects.create(name="Fiction")
        publisher = Publisher.objects.create(
            name="Press", city="Paris", contact="press@example.com"
        )
        book = Book.objects.create(
            author="Ada",
            title="Guide",
            description="A short guide",
            category=category,
            publisher=publisher,
        )
        activity = UserActivity.objects.create(
            created_by="staff",
            operation_type="success",
            target_model="Book",
            detail="Create Book",
        )

        self.assertEqual(str(category), "Fiction")
        self.assertEqual(str(publisher), "Press")
        self.assertEqual(str(book), "Guide")
        self.assertEqual(category.get_absolute_url(), reverse("category_list"))
        self.assertEqual(publisher.get_absolute_url(), reverse("publisher_list"))
        self.assertEqual(book.get_absolute_url(), reverse("book_list"))
        self.assertEqual(activity.get_absolute_url(), reverse("user_activity_list"))
        self.assertEqual(book.status, 1)
        self.assertEqual(book.quantity, 10)
        self.assertEqual(publisher.updated_by, "yaozeliang")

    def test_deleting_category_nulls_the_book_link(self):
        category = Category.objects.create(name="Science")
        book = Book.objects.create(
            author="Ada", title="Notes", description="Lab notes", category=category
        )
        category.delete()
        book.refresh_from_db()
        self.assertIsNone(book.category_id)


class MemberSaveTests(TestCase):
    def test_save_sets_card_number_and_one_year_expiry(self):
        before = timezone.now()
        member = Member.objects.create(
            name="Ada Lovelace", city="London", phone_number="0600000001"
        )
        member.refresh_from_db()
        self.assertEqual(str(member), "Ada Lovelace")
        self.assertEqual(member.card_number, str(member.card_id)[:8])
        self.assertEqual(len(member.card_number), 8)
        self.assertGreater(member.expired_at, before + timedelta(days=360))
        self.assertEqual(member.get_absolute_url(), reverse("member_list"))

    def test_partial_update_still_persists_generated_card_fields(self):
        member = Member.objects.create(
            name="Grace", city="Paris", phone_number="0600000002"
        )
        original_card = member.card_number
        member.name = "Grace Hopper"
        member.card_number = ""
        member.save(update_fields=["name"])
        member.refresh_from_db()
        self.assertEqual(member.name, "Grace Hopper")
        self.assertEqual(member.card_number, original_card)


class ProfileSignalAndImageTests(TestCase):
    def test_creating_a_user_creates_and_updates_a_profile(self):
        user = User.objects.create_user(username="reader", password="reader-pass-1")
        profile = Profile.objects.get(user=user)
        self.assertEqual(str(profile), "reader")
        self.assertEqual(profile.get_absolute_url(), reverse("home"))

        user.first_name = "Ada"
        user.save()
        self.assertTrue(Profile.objects.filter(user=user).exists())

    def test_profile_picture_is_resized_to_400px_wide(self):
        user = User.objects.create_user(username="pic", password="pic-pass-1")
        buffer = io.BytesIO()
        Image.new("RGB", (800, 200), "red").save(buffer, format="PNG")
        upload = SimpleUploadedFile(
            "avatar.png", buffer.getvalue(), content_type="image/png"
        )
        with tempfile.TemporaryDirectory() as media_root:
            with override_settings(MEDIA_ROOT=media_root):
                profile = user.profile
                profile.profile_pic.save("avatar.png", ContentFile(upload.read()), save=True)
                with Image.open(profile.profile_pic.path) as image:
                    self.assertEqual(image.size[0], 400)
                    self.assertEqual(image.size[1], 100)


class BorrowRecordComputedTests(TestCase):
    def test_default_due_date_is_about_one_week_out(self):
        due = default_borrow_end_day()
        delta = due - timezone.now()
        self.assertGreater(delta, timedelta(days=6))
        self.assertLess(delta, timedelta(days=8))

    def test_open_record_on_time_and_overdue(self):
        on_time = BorrowRecord.objects.create(
            borrower="Sam",
            book="Guide",
            end_day=timezone.now() + timedelta(days=2),
        )
        self.assertEqual(str(on_time), "Sam - Guide")
        self.assertEqual(on_time.return_status, "On Time")
        self.assertEqual(on_time.get_delay_number_days, 0)
        self.assertEqual(on_time.delay_days, 0)
        self.assertEqual(on_time.get_absolute_url(), reverse("record_list"))

        overdue = BorrowRecord.objects.create(
            borrower="Sam",
            book="Guide",
            end_day=timezone.now() - timedelta(days=3, hours=2),
        )
        self.assertEqual(overdue.return_status, "Overdue")
        self.assertGreaterEqual(overdue.delay_days, 3)
        self.assertGreaterEqual(overdue.get_delay_number_days, 3)

    def test_closed_record_keeps_stored_delay_and_says_returned(self):
        closed = BorrowRecord.objects.create(
            borrower="Sam",
            book="Guide",
            open_or_close=1,
            delay_days=4,
            end_day=timezone.now() - timedelta(days=10),
        )
        self.assertEqual(closed.return_status, "Returned")
        self.assertEqual(closed.get_delay_number_days, 4)
        closed.refresh_from_db()
        self.assertEqual(closed.delay_days, 4)

    def test_closed_at_is_set_only_when_the_loan_is_closed(self):
        open_record = BorrowRecord.objects.create(borrower="Sam", book="Guide")
        open_record.borrower = "Sam Two"
        open_record.save()
        open_record.refresh_from_db()
        self.assertIsNone(open_record.closed_at)
        self.assertEqual(open_record.open_or_close, 0)

        closed = BorrowRecord.objects.create(
            borrower="Sam", book="Guide", open_or_close=1
        )
        stamp = closed.closed_at
        self.assertIsNotNone(stamp)
        closed.borrower = "Renamed"
        closed.save()
        closed.refresh_from_db()
        self.assertEqual(closed.closed_at, stamp)
        self.assertEqual(closed.borrower, "Renamed")

        closed.open_or_close = 0
        closed.save()
        closed.refresh_from_db()
        self.assertIsNone(closed.closed_at)
        self.assertEqual(closed.open_or_close, 0)

    def test_data_migration_clears_closed_at_on_open_records_only(self):
        import importlib

        migration = importlib.import_module(
            "book.migrations.0038_borrowrecord_closed_at_nullable"
        )

        open_record = BorrowRecord.objects.create(borrower="Open", book="Guide")
        BorrowRecord.objects.filter(pk=open_record.pk).update(
            closed_at=timezone.now()
        )
        closed = BorrowRecord.objects.create(
            borrower="Shut", book="Guide", open_or_close=1
        )
        stamp = closed.closed_at
        self.assertIsNotNone(stamp)

        migration.clear_closed_at_on_open_records(apps, None)

        open_record.refresh_from_db()
        closed.refresh_from_db()
        self.assertIsNone(open_record.closed_at)
        self.assertEqual(closed.closed_at, stamp)


class BorrowRecordCalendarDelayTests(TestCase):
    """Due dates are local calendar dates, not timestamp comparisons."""

    def setUp(self):
        # 15:30 in Europe/Paris, so earlier and later times the same day exist.
        self.frozen_now = timezone.make_aware(datetime(2026, 9, 27, 15, 30))
        self.now_patch = patch(
            "django.utils.timezone.now", return_value=self.frozen_now
        )
        self.now_patch.start()
        self.addCleanup(self.now_patch.stop)

    def _loan(self, end_day, **kwargs):
        return BorrowRecord.objects.create(
            borrower="Sam", book="Guide", end_day=end_day, **kwargs
        )

    def test_due_yesterday_is_overdue_by_one_calendar_day(self):
        # 23:00 yesterday is only 16.5 hours ago, so a timestamp delta is 0 days.
        record = self._loan(timezone.make_aware(datetime(2026, 9, 26, 23, 0)))
        self.assertEqual(record.return_status, "Overdue")
        self.assertEqual(record.get_delay_number_days, 1)
        record.refresh_from_db()
        self.assertEqual(record.delay_days, 1)

    def test_due_today_earlier_or_later_than_now_is_on_time(self):
        earlier = self._loan(timezone.make_aware(datetime(2026, 9, 27, 8, 0)))
        later = self._loan(timezone.make_aware(datetime(2026, 9, 27, 22, 0)))
        for record in (earlier, later):
            self.assertEqual(record.return_status, "On Time")
            self.assertEqual(record.get_delay_number_days, 0)
            record.refresh_from_db()
            self.assertEqual(record.delay_days, 0)

    def test_due_tomorrow_is_on_time(self):
        record = self._loan(timezone.make_aware(datetime(2026, 9, 28, 1, 0)))
        self.assertEqual(record.return_status, "On Time")
        self.assertEqual(record.get_delay_number_days, 0)
        record.refresh_from_db()
        self.assertEqual(record.delay_days, 0)

    def test_delay_counts_calendar_days_not_elapsed_timestamps(self):
        # 23:00 three dates back is 2 days and 16.5 hours, which truncates to 2.
        record = self._loan(timezone.make_aware(datetime(2026, 9, 24, 23, 0)))
        self.assertEqual(record.return_status, "Overdue")
        self.assertEqual(record.get_delay_number_days, 3)
        record.refresh_from_db()
        self.assertEqual(record.delay_days, 3)

    def test_closed_record_returns_stored_delay_days(self):
        closed = self._loan(
            timezone.make_aware(datetime(2026, 9, 20, 9, 0)),
            open_or_close=1,
            delay_days=4,
        )
        self.assertEqual(closed.return_status, "Returned")
        self.assertEqual(closed.get_delay_number_days, 4)
        closed.refresh_from_db()
        self.assertEqual(closed.delay_days, 4)

    def test_naive_end_day_uses_its_date_not_a_timezone_conversion(self):
        yesterday = BorrowRecord(
            borrower="Sam",
            book="Guide",
            end_day=datetime(2026, 9, 26, 23, 0),
        )
        due_today = BorrowRecord(
            borrower="Sam",
            book="Guide",
            end_day=datetime(2026, 9, 27, 8, 0),
        )
        self.assertFalse(timezone.is_aware(yesterday.end_day))
        self.assertEqual(yesterday.return_status, "Overdue")
        self.assertEqual(yesterday.get_delay_number_days, 1)
        self.assertEqual(due_today.return_status, "On Time")
        self.assertEqual(due_today.get_delay_number_days, 0)

    def test_closing_a_loan_keeps_the_calendar_delay(self):
        record = self._loan(timezone.make_aware(datetime(2026, 9, 25, 23, 30)))
        record.final_status = record.return_status
        record.delay_days = record.get_delay_number_days
        record.open_or_close = 1
        record.closed_at = timezone.now()
        record.save()
        record.refresh_from_db()
        self.assertEqual(record.final_status, "Overdue")
        self.assertEqual(record.delay_days, 2)
        self.assertEqual(record.return_status, "Returned")
        self.assertEqual(record.get_delay_number_days, 2)


@override_settings(TIME_ZONE="Europe/Paris")
class BorrowRecordParisMidnightTests(TestCase):
    """Local calendar dates around midnight, not the UTC date of the timestamp.

    Django stores aware datetimes in UTC and ``timezone.now()`` is UTC.
    ``datetime.date()`` on those values is the UTC day. Europe/Paris in
    September is UTC+2, so local 00:30 is 22:30 UTC on the previous day.
    """

    def setUp(self):
        self.assertEqual(str(timezone.get_current_timezone()), "Europe/Paris")

    def _freeze_local(self, wall_clock):
        """Freeze ``timezone.now()`` at a Paris wall time, returned in UTC."""
        frozen_utc = timezone.make_aware(wall_clock).astimezone(datetime_timezone.utc)
        patcher = patch("django.utils.timezone.now", return_value=frozen_utc)
        patcher.start()
        self.addCleanup(patcher.stop)
        return frozen_utc

    def _open_loan(self, due_wall_clock):
        record = BorrowRecord.objects.create(
            borrower="Sam",
            book="Guide",
            end_day=timezone.make_aware(due_wall_clock),
        )
        # Reload so ``end_day`` is the stored UTC instant, as the list view sees it.
        record.refresh_from_db()
        return record

    def _assert_list_status(self, record, status, days):
        """Borrow lists render ``return_status`` and ``get_delay_number_days``."""
        self.assertEqual(record.return_status, status)
        self.assertEqual(record.get_delay_number_days, days)

    def _close_and_assert_saved_delay(self, record, status, days):
        """Close the way ``BorrowRecordClose`` does, then read the saved delay.

        The view copies the list properties, then ``save()`` persists
        ``delay_days`` without recomputing it for a closed loan.
        """
        record.final_status = record.return_status
        record.delay_days = record.get_delay_number_days
        record.open_or_close = 1
        record.closed_at = timezone.now()
        record.save()
        record.refresh_from_db()
        self.assertEqual(record.final_status, status)
        self.assertEqual(record.delay_days, days)
        self.assertEqual(record.return_status, "Returned")
        self.assertEqual(record.get_delay_number_days, days)

    def test_local_2359_on_the_due_date_is_on_time(self):
        # 23:59 in Paris is 21:59 UTC the same calendar day.
        frozen_utc = self._freeze_local(datetime(2026, 9, 27, 23, 59))
        self.assertEqual(timezone.localdate(), date(2026, 9, 27))
        self.assertEqual(frozen_utc.date(), date(2026, 9, 27))
        self.assertEqual((frozen_utc.hour, frozen_utc.minute), (21, 59))

        # Due 00:30 local is 22:30 UTC the previous day. UTC .date() is Sep 26.
        record = self._open_loan(datetime(2026, 9, 27, 0, 30))
        self.assertEqual(record.end_day.utcoffset(), timedelta(0))
        self.assertEqual(record.end_day.date(), date(2026, 9, 26))
        self.assertEqual(timezone.localdate(record.end_day), date(2026, 9, 27))
        self.assertEqual(record.delay_days, 0)
        self._assert_list_status(record, "On Time", 0)
        self._close_and_assert_saved_delay(record, "On Time", 0)

    def test_local_0030_on_the_due_date_is_on_time(self):
        # 00:30 in Paris is 22:30 UTC on the previous day.
        frozen_utc = self._freeze_local(datetime(2026, 9, 27, 0, 30))
        self.assertEqual(timezone.localdate(), date(2026, 9, 27))
        self.assertEqual(frozen_utc.date(), date(2026, 9, 26))
        self.assertEqual((frozen_utc.hour, frozen_utc.minute), (22, 30))

        # Due later that local day. Its UTC date is Sep 27, now's UTC date is Sep 26.
        record = self._open_loan(datetime(2026, 9, 27, 23, 59))
        self.assertEqual(record.end_day.date(), date(2026, 9, 27))
        self.assertEqual(timezone.localdate(record.end_day), date(2026, 9, 27))
        self.assertNotEqual(timezone.now().date(), timezone.localdate())
        self.assertEqual(record.delay_days, 0)
        self._assert_list_status(record, "On Time", 0)
        self._close_and_assert_saved_delay(record, "On Time", 0)

    def test_local_0030_the_morning_after_the_due_date_is_one_day_overdue(self):
        # Still Sep 27 in UTC, already Sep 28 in Paris.
        frozen_utc = self._freeze_local(datetime(2026, 9, 28, 0, 30))
        self.assertEqual(timezone.localdate(), date(2026, 9, 28))
        self.assertEqual(frozen_utc.date(), date(2026, 9, 27))
        self.assertEqual((frozen_utc.hour, frozen_utc.minute), (22, 30))

        record = self._open_loan(datetime(2026, 9, 27, 23, 59))
        self.assertEqual(record.end_day.date(), date(2026, 9, 27))
        self.assertEqual(timezone.localdate(record.end_day), date(2026, 9, 27))
        # UTC .date() of now and of end_day match, which would be delay 0.
        self.assertEqual(timezone.now().date(), record.end_day.date())
        self.assertEqual(record.delay_days, 1)
        self._assert_list_status(record, "Overdue", 1)
        self._close_and_assert_saved_delay(record, "Overdue", 1)


class CommentSaveTests(TestCase):
    def test_save_strips_unsafe_html_and_builds_urls(self):
        user = User.objects.create_user(username="reader", password="reader-pass-1")
        book = Book.objects.create(author="Ada", title="Guide", description="A short guide")
        comment = Comment.objects.create(
            book=book,
            user=user,
            body='<script>alert(1)</script><p>hello</p><a href="javascript:alert(1)">x</a>',
        )
        comment.refresh_from_db()
        self.assertNotIn("<script", comment.body)
        self.assertIn("hello", comment.body)
        self.assertNotIn("javascript:", comment.body)
        self.assertIn(user.username, str(comment))
        self.assertEqual(
            comment.get_absolute_url(),
            reverse("comment:comment_detail", kwargs={"pk": comment.pk}),
        )

    def test_empty_body_is_stored_as_an_empty_string(self):
        user = User.objects.create_user(username="reader2", password="reader-pass-1")
        comment = Comment.objects.create(user=user, body="")
        self.assertEqual(comment.body, "")
