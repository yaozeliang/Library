"""Model string forms, constraints, computed fields, and save/signal side effects."""

import io
import tempfile
from datetime import timedelta

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
