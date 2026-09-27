"""POST create, update, and delete flows for library routes."""

from datetime import timedelta

from django.test import Client
from django.urls import reverse
from django.utils import timezone

from book.models import (
    Book,
    BorrowRecord,
    Category,
    Member,
    Publisher,
    UserActivity,
)
from book.tests.route_utils import RouteFixture


class WriteRouteTests(RouteFixture):
    def setUp(self):
        super().setUp()
        self.login(self.staff)
        self.category = Category.objects.create(name="Fiction")
        self.publisher = Publisher.objects.create(
            name="Route Press", city="Paris", contact="press@example.com"
        )
        self.book = Book.objects.create(
            author="Ada",
            title="Route Guide",
            description="A short guide",
            quantity=4,
            category=self.category,
            publisher=self.publisher,
        )
        self.member = Member.objects.create(
            name="Pat Route", city="Paris", phone_number="0600000000", email="pat@example.com"
        )

    def _book_payload(self, **overrides):
        payload = {
            "author": "Grace",
            "title": "New Algorithms",
            "description": "Sorting",
            "quantity": 2,
            "category": self.category.pk,
            "publisher": self.publisher.pk,
            "floor_number": 1,
            "bookshelf_number": "0008",
        }
        payload.update(overrides)
        return payload

    def test_book_create_update_and_delete(self):
        invalid = self.client.post(reverse("book_create"), self._book_payload(title=""))
        self.assertEqual(invalid.status_code, 200)
        self.assertTemplateUsed(invalid, "book/book_create.html")
        self.assertContains(invalid, "This field is required")
        self.assertFalse(Book.objects.filter(title="").exists())
        self.assertFalse(UserActivity.objects.filter(detail__contains="New Algorithms").exists())

        created = self.client.post(reverse("book_create"), self._book_payload())
        self.assertRedirects(created, reverse("book_list"))
        book = Book.objects.get(title="New Algorithms")
        self.assertTrue(
            UserActivity.objects.filter(detail__contains="New Algorithms").exists()
        )

        before = UserActivity.objects.count()
        rejected = self.client.post(
            reverse("book_update", args=[book.pk]),
            self._book_payload(title=""),
        )
        self.assertEqual(rejected.status_code, 200)
        self.assertTemplateUsed(rejected, "book/book_update.html")
        book.refresh_from_db()
        self.assertEqual(book.title, "New Algorithms")
        self.assertEqual(UserActivity.objects.count(), before)

        updated = self.client.post(
            reverse("book_update", args=[book.pk]),
            self._book_payload(title="Renamed Algorithms"),
        )
        self.assertRedirects(updated, reverse("book_list"))
        book.refresh_from_db()
        self.assertEqual(book.title, "Renamed Algorithms")
        self.assertEqual(book.updated_by, self.staff.username)

        missing = self.client.post(reverse("book_delete", args=[999999]))
        self.assertEqual(missing.status_code, 404)
        removed = self.client.post(reverse("book_delete", args=[book.pk]))
        self.assertRedirects(removed, reverse("book_list"))
        self.assertFalse(Book.objects.filter(pk=book.pk).exists())

    def test_category_publisher_and_member_writes(self):
        bad_category = self.client.post(reverse("category_create"), {"name": "x" * 51})
        self.assertEqual(bad_category.status_code, 200)
        self.assertContains(bad_category, "Ensure this value has at most 50 characters")
        self.assertFalse(Category.objects.filter(name="x" * 51).exists())

        created_category = self.client.post(reverse("category_create"), {"name": "Mystery"})
        self.assertRedirects(created_category, reverse("category_list"))
        category = Category.objects.get(name="Mystery")
        self.assertEqual(
            self.client.post(reverse("category_delete", args=[999999])).status_code,
            404,
        )
        deleted = self.client.post(reverse("category_delete", args=[category.pk]))
        self.assertRedirects(deleted, reverse("category_list"))
        self.assertFalse(Category.objects.filter(pk=category.pk).exists())

        bad_publisher = self.client.post(
            reverse("publisher_create"),
            {"name": "Bad Press", "city": "Lyon", "contact": "not-an-email"},
        )
        self.assertEqual(bad_publisher.status_code, 200)
        self.assertTemplateUsed(bad_publisher, "book/publisher_create.html")
        self.assertContains(bad_publisher, "Enter a valid email")
        self.assertFalse(Publisher.objects.filter(name="Bad Press").exists())

        created_publisher = self.client.post(
            reverse("publisher_create"),
            {"name": "Good Press", "city": "Lyon", "contact": "good@example.com"},
        )
        self.assertRedirects(created_publisher, reverse("publisher_list"))
        publisher = Publisher.objects.get(name="Good Press")
        updated = self.client.post(
            reverse("publisher_update", args=[publisher.pk]),
            {"name": "Better Press", "city": "Lyon", "contact": "good@example.com"},
        )
        self.assertRedirects(updated, reverse("publisher_list"))
        publisher.refresh_from_db()
        self.assertEqual(publisher.name, "Better Press")
        self.assertEqual(publisher.updated_by, self.staff.username)
        self.assertEqual(
            self.client.post(reverse("publisher_delete", args=[999999])).status_code,
            404,
        )
        self.assertRedirects(
            self.client.post(reverse("publisher_delete", args=[publisher.pk])),
            reverse("publisher_list"),
        )

        bad_member = self.client.post(
            reverse("member_create"),
            {
                "name": "",
                "gender": "m",
                "age": 20,
                "email": "bad",
                "city": "Paris",
                "phone_number": "0600",
            },
        )
        self.assertEqual(bad_member.status_code, 200)
        self.assertTemplateUsed(bad_member, "book/member_create.html")
        self.assertContains(bad_member, "This field is required")

        created_member = self.client.post(
            reverse("member_create"),
            {
                "name": "Grace Hopper",
                "gender": "f",
                "age": 40,
                "email": "grace@example.com",
                "city": "Paris",
                "phone_number": "0612345678",
            },
        )
        self.assertRedirects(created_member, reverse("member_list"))
        member = Member.objects.get(name="Grace Hopper")
        self.assertEqual(member.created_by, self.staff.username)

        rejected = self.client.post(
            reverse("member_update", args=[member.pk]),
            {
                "name": "",
                "gender": "f",
                "age": 40,
                "email": "grace@example.com",
                "city": "Paris",
                "phone_number": "0612345678",
            },
        )
        self.assertEqual(rejected.status_code, 200)
        member.refresh_from_db()
        self.assertEqual(member.name, "Grace Hopper")

        renamed = self.client.post(
            reverse("member_update", args=[member.pk]),
            {
                "name": "Grace M. Hopper",
                "gender": "f",
                "age": 41,
                "email": "grace@example.com",
                "city": "Paris",
                "phone_number": "0612345678",
            },
        )
        self.assertRedirects(renamed, reverse("member_list"))
        member.refresh_from_db()
        self.assertEqual(member.name, "Grace M. Hopper")
        self.assertEqual(member.updated_by, self.staff.username)
        self.assertEqual(
            self.client.post(reverse("member_delete", args=[999999])).status_code, 404
        )
        self.assertRedirects(
            self.client.post(reverse("member_delete", args=[member.pk])),
            reverse("member_list"),
        )

    def test_profile_create_updates_the_existing_row(self):
        invalid = self.client.post(
            reverse("profile_create"),
            {"bio": "", "phone_number": "", "email": "not-an-email"},
        )
        self.assertEqual(invalid.status_code, 200)
        self.assertTemplateUsed(invalid, "profile/profile_create.html")
        self.assertContains(invalid, "This field is required")
        self.staff.profile.refresh_from_db()
        self.assertEqual(self.staff.profile.bio, "")

        saved = self.client.post(
            reverse("profile_create"),
            {"bio": "Desk librarian", "phone_number": "0600111222", "email": "desk@example.com"},
        )
        self.assertRedirects(saved, reverse("profile_detail", args=[self.staff.profile.pk]))
        self.staff.profile.refresh_from_db()
        self.assertEqual(self.staff.profile.bio, "Desk librarian")

        cleared = self.client.post(
            reverse("profile_update", args=[self.staff.profile.pk]),
            {"bio": "", "phone_number": "0600111222", "email": "desk@example.com"},
        )
        self.assertEqual(cleared.status_code, 200)
        self.assertTemplateUsed(cleared, "profile/profile_update.html")
        self.staff.profile.refresh_from_db()
        self.assertEqual(self.staff.profile.bio, "Desk librarian")

        updated = self.client.post(
            reverse("profile_update", args=[self.staff.profile.pk]),
            {"bio": "Updated bio", "phone_number": "0600111222", "email": "desk@example.com"},
        )
        self.assertRedirects(updated, reverse("home"))
        self.staff.profile.refresh_from_db()
        self.assertEqual(self.staff.profile.bio, "Updated bio")

    def test_borrow_record_create_close_and_delete(self):
        start = timezone.now().strftime("%Y-%m-%d %H:%M:%S")
        end = (timezone.now() + timedelta(days=7)).strftime("%Y-%m-%d %H:%M:%S")
        payload = {
            "borrower": self.member.name,
            "book": self.book.title,
            "quantity": 1,
            "start_day": start,
            "end_day": end,
        }
        invalid = self.client.post(reverse("record_create"), {**payload, "borrower": ""})
        self.assertEqual(invalid.status_code, 200)
        self.assertTemplateUsed(invalid, "borrow_records/create.html")
        self.assertEqual(BorrowRecord.objects.count(), 0)

        unknown = self.client.post(
            reverse("record_create"), {**payload, "book": "Missing Title"}
        )
        self.assertEqual(unknown.status_code, 200)
        self.assertContains(unknown, "Select an existing book")
        self.assertEqual(BorrowRecord.objects.count(), 0)

        unknown_member = self.client.post(
            reverse("record_create"), {**payload, "borrower": "No Such Person"}
        )
        self.assertEqual(unknown_member.status_code, 200)
        self.assertContains(unknown_member, "Select an existing member")

        too_many = self.client.post(
            reverse("record_create"), {**payload, "quantity": 99}
        )
        self.assertEqual(too_many.status_code, 200)
        self.assertContains(too_many, "Not enough copies in stock")
        self.assertEqual(BorrowRecord.objects.count(), 0)

        created = self.client.post(reverse("record_create"), payload)
        self.assertRedirects(created, reverse("record_list"))
        record = BorrowRecord.objects.get(borrower=self.member.name)
        self.book.refresh_from_db()
        self.assertEqual(self.book.quantity, 3)
        self.assertEqual(self.book.total_borrow_times, 1)

        self.assertEqual(
            self.client.post(reverse("record_close", args=[999999])).status_code, 404
        )
        closed = self.client.post(reverse("record_close", args=[record.pk]))
        self.assertRedirects(closed, reverse("record_list"))
        record.refresh_from_db()
        self.assertEqual(record.open_or_close, 1)
        self.book.refresh_from_db()
        self.assertEqual(self.book.quantity, 4)

        self.assertEqual(
            self.client.post(reverse("record_delete", args=[999999])).status_code, 404
        )
        removed = self.client.post(reverse("record_delete", args=[record.pk]))
        self.assertRedirects(removed, reverse("record_list"))
        self.assertFalse(BorrowRecord.objects.filter(pk=record.pk).exists())

    def test_activity_delete_and_notice_clear_for_superuser(self):
        activity = UserActivity.objects.create(
            created_by=self.staff.username, target_model="Book", detail="temp"
        )
        self.login(self.superuser)
        missing = self.client.post(reverse("user_activity_delete", args=[999999]))
        self.assertEqual(missing.status_code, 404)
        removed = self.client.post(reverse("user_activity_delete", args=[activity.pk]))
        self.assertRedirects(removed, reverse("user_activity_list"))
        self.assertFalse(UserActivity.objects.filter(pk=activity.pk).exists())

        from notifications.signals import notify

        notify.send(self.staff, recipient=self.superuser, verb="ping")
        notice = self.superuser.notifications.unread().get()
        one = self.client.post(reverse("notice_update"), {"notice_id": notice.id})
        self.assertRedirects(one, reverse("category_list"))
        self.assertFalse(self.superuser.notifications.unread().filter(pk=notice.pk).exists())

        cleared = self.client.post(reverse("notice_update"), {})
        self.assertRedirects(cleared, reverse("notice_list"))

    def test_post_without_csrf_is_rejected(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.staff)
        response = client.post(reverse("category_create"), {"name": "Nope"})
        self.assertEqual(response.status_code, 403)
        self.assertFalse(Category.objects.filter(name="Nope").exists())
