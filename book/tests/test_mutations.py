"""Create, update, delete, borrow, and return change the database correctly.

Anonymous posts must not mutate. Staff may run library edits. Only a
superuser may change employee groups or notices.
"""

from datetime import timedelta

from django.contrib.auth.models import Group
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from notifications.signals import notify

from book.models import (
    Book,
    BorrowRecord,
    Category,
    Member,
    Publisher,
    UserActivity,
)
from book.tests.helpers import make_admin, make_staff, silence_weather
from comment.models import Comment


class MutationSetup(TestCase):
    def setUp(self):
        weather = silence_weather()
        weather.start()
        self.addCleanup(weather.stop)
        self.staff = make_staff()
        self.admin = make_admin()

    def _book_payload(self, **overrides):
        data = {
            "author": "Ada",
            "title": "Guide",
            "description": "A short guide",
            "quantity": 4,
            "floor_number": 1,
            "bookshelf_number": "0001",
        }
        data.update(overrides)
        return data

    def _member_payload(self, **overrides):
        data = {
            "name": "Ada Lovelace",
            "gender": "f",
            "age": 36,
            "email": "ada@example.com",
            "city": "London",
            "phone_number": "0600000001",
        }
        data.update(overrides)
        return data

    def _loan_payload(self, **overrides):
        data = {
            "borrower": "Ada Lovelace",
            "book": "Guide",
            "quantity": 1,
            "start_day": "2026-09-01",
            "end_day": "2026-09-08",
        }
        data.update(overrides)
        return data


class CatalogMutationTests(MutationSetup):
    def test_anonymous_posts_do_not_create_or_delete(self):
        book = Book.objects.create(author="Ada", title="Guide", description="d")
        category = Category.objects.create(name="Fiction")
        member = Member.objects.create(name="Ada", city="Paris", phone_number="1")
        targets = (
            (reverse("book_create"), self._book_payload(title="Other")),
            (reverse("member_create"), self._member_payload()),
            (reverse("category_create"), {"name": "Science"}),
            (reverse("publisher_create"), {"name": "Press", "city": "Paris", "contact": ""}),
            (reverse("book_delete", args=[book.pk]), {}),
            (reverse("category_delete", args=[category.pk]), {}),
            (reverse("member_delete", args=[member.pk]), {}),
        )
        for url, payload in targets:
            response = self.client.post(url, payload)
            self.assertEqual(response.status_code, 302, url)
            self.assertIn("/auth/login/", response.url)

        self.assertFalse(Book.objects.filter(title="Other").exists())
        self.assertFalse(Category.objects.filter(name="Science").exists())
        self.assertTrue(Book.objects.filter(pk=book.pk).exists())
        self.assertTrue(Category.objects.filter(pk=category.pk).exists())
        self.assertTrue(Member.objects.filter(pk=member.pk).exists())

    def test_staff_can_create_update_and_delete_a_book(self):
        self.client.force_login(self.staff)
        created = self.client.post(reverse("book_create"), self._book_payload())
        self.assertRedirects(created, reverse("book_list"))
        book = Book.objects.get(title="Guide")
        self.assertEqual(book.quantity, 4)
        self.assertTrue(
            UserActivity.objects.filter(
                created_by="staff", target_model="Book", detail__contains="Guide"
            ).exists()
        )

        updated = self.client.post(
            reverse("book_update", args=[book.pk]),
            self._book_payload(title="Guide revised", quantity=6),
        )
        self.assertEqual(updated.status_code, 302)
        book.refresh_from_db()
        self.assertEqual(book.title, "Guide revised")
        self.assertEqual(book.quantity, 6)
        self.assertEqual(book.updated_by, "staff")

        removed = self.client.post(reverse("book_delete", args=[book.pk]))
        self.assertRedirects(removed, reverse("book_list"))
        self.assertFalse(Book.objects.filter(pk=book.pk).exists())

    def test_invalid_book_and_member_posts_do_not_write_rows(self):
        self.client.force_login(self.staff)
        before = UserActivity.objects.count()
        rejected = self.client.post(
            reverse("book_create"), self._book_payload(description="", title="Nope")
        )
        self.assertEqual(rejected.status_code, 200)
        self.assertFalse(Book.objects.filter(title="Nope").exists())
        self.assertEqual(UserActivity.objects.count(), before)

        missing = self.client.post(reverse("book_create"), {})
        self.assertEqual(missing.status_code, 200)
        self.assertEqual(Book.objects.count(), 0)

        member_rejected = self.client.post(
            reverse("member_create"), self._member_payload(email="not-an-email")
        )
        self.assertEqual(member_rejected.status_code, 200)
        self.assertFalse(Member.objects.exists())
        self.assertEqual(UserActivity.objects.count(), before)

        book = Book.objects.create(author="Ada", title="Guide", description="d")
        original_editor = book.updated_by
        invalid_update = self.client.post(
            reverse("book_update", args=[book.pk]),
            self._book_payload(description=""),
        )
        self.assertEqual(invalid_update.status_code, 200)
        book.refresh_from_db()
        self.assertEqual(book.description, "d")
        self.assertEqual(book.updated_by, original_editor)

    def test_staff_creates_category_publisher_and_member(self):
        self.client.force_login(self.staff)
        self.assertRedirects(
            self.client.post(reverse("category_create"), {"name": "Fiction"}),
            reverse("category_list"),
        )
        self.assertTrue(Category.objects.filter(name="Fiction").exists())

        created = self.client.post(
            reverse("publisher_create"),
            {"name": "Press", "city": "Paris", "contact": "press@example.com"},
        )
        self.assertRedirects(created, reverse("publisher_list"))
        publisher = Publisher.objects.get(name="Press")

        bad = self.client.post(
            reverse("publisher_create"),
            {"name": "Bad", "city": "Paris", "contact": "nope"},
        )
        self.assertEqual(bad.status_code, 200)
        self.assertFalse(Publisher.objects.filter(name="Bad").exists())

        self.assertEqual(
            self.client.post(
                reverse("publisher_update", args=[publisher.pk]),
                {"name": "Press House", "city": "Lyon", "contact": ""},
            ).status_code,
            302,
        )
        publisher.refresh_from_db()
        self.assertEqual(publisher.name, "Press House")
        self.assertEqual(publisher.updated_by, "staff")

        self.assertEqual(
            self.client.post(reverse("member_create"), self._member_payload()).status_code,
            302,
        )
        member = Member.objects.get(name="Ada Lovelace")
        self.assertEqual(member.created_by, "staff")
        self.assertEqual(member.card_number, str(member.card_id)[:8])

        self.client.post(
            reverse("member_update", args=[member.pk]),
            self._member_payload(city="Paris"),
        )
        member.refresh_from_db()
        self.assertEqual(member.city, "Paris")
        self.assertEqual(member.updated_by, "staff")

        self.client.post(reverse("publisher_delete", args=[publisher.pk]))
        self.client.post(reverse("member_delete", args=[member.pk]))
        category = Category.objects.get(name="Fiction")
        self.client.post(reverse("category_delete", args=[category.pk]))
        self.assertFalse(Publisher.objects.filter(pk=publisher.pk).exists())
        self.assertFalse(Member.objects.filter(pk=member.pk).exists())
        self.assertFalse(Category.objects.filter(pk=category.pk).exists())


class BorrowReturnTests(MutationSetup):
    def setUp(self):
        super().setUp()
        self.book = Book.objects.create(
            author="Ada", title="Guide", description="A short guide", quantity=5
        )
        self.member = Member.objects.create(
            name="Ada Lovelace",
            city="London",
            phone_number="0600000001",
            email="ada@example.com",
        )
        self.client.force_login(self.staff)

    def test_borrow_decrements_stock_and_copies_member_details(self):
        response = self.client.post(
            reverse("record_create"), self._loan_payload(quantity=2)
        )
        self.assertRedirects(response, reverse("record_list"))
        record = BorrowRecord.objects.get()
        self.book.refresh_from_db()
        self.assertEqual(record.quantity, 2)
        self.assertEqual(record.borrower_card, self.member.card_number)
        self.assertEqual(record.borrower_email, "ada@example.com")
        self.assertEqual(record.borrower_phone_number, "0600000001")
        self.assertEqual(record.created_by, "staff")
        self.assertEqual(record.open_or_close, 0)
        self.assertEqual(self.book.quantity, 3)
        self.assertEqual(self.book.status, 0)
        self.assertEqual(self.book.total_borrow_times, 1)

    def test_invalid_loans_leave_stock_unchanged(self):
        cases = (
            self._loan_payload(book="Missing"),
            self._loan_payload(borrower="Nobody"),
            self._loan_payload(quantity=9),
            self._loan_payload(quantity=0),
            self._loan_payload(start_day="2026-09-20", end_day="2026-09-01"),
        )
        for payload in cases:
            response = self.client.post(reverse("record_create"), payload)
            self.assertEqual(response.status_code, 200, payload)
            self.assertEqual(BorrowRecord.objects.count(), 0)
            self.book.refresh_from_db()
            self.assertEqual(self.book.quantity, 5)
            self.assertEqual(self.book.status, 1)
            self.assertEqual(self.book.total_borrow_times, 0)

    def test_anonymous_cannot_borrow_or_return(self):
        self.client.logout()
        borrowed = self.client.post(reverse("record_create"), self._loan_payload())
        self.assertEqual(borrowed.status_code, 302)
        self.assertEqual(BorrowRecord.objects.count(), 0)

        record = BorrowRecord.objects.create(
            borrower=self.member.name, book=self.book.title, quantity=2
        )
        returned = self.client.post(reverse("record_close", args=[record.pk]))
        self.assertEqual(returned.status_code, 302)
        record.refresh_from_db()
        self.assertEqual(record.open_or_close, 0)
        self.book.refresh_from_db()
        self.assertEqual(self.book.quantity, 5)

    def test_return_restores_borrowed_quantity_and_ignores_a_second_close(self):
        self.client.post(reverse("record_create"), self._loan_payload(quantity=2))
        self.client.post(reverse("record_create"), self._loan_payload(quantity=1))
        first, second = list(BorrowRecord.objects.order_by("id"))

        self.client.post(reverse("record_close", args=[first.pk]))
        first.refresh_from_db()
        self.book.refresh_from_db()
        self.assertEqual(first.open_or_close, 1)
        self.assertEqual(first.closed_by, "staff")
        self.assertEqual(self.book.quantity, 4)
        self.assertEqual(self.book.status, 0)

        self.client.post(reverse("record_close", args=[second.pk]))
        self.book.refresh_from_db()
        self.assertEqual(self.book.quantity, 5)
        self.assertEqual(self.book.status, 1)

        self.client.post(reverse("record_close", args=[second.pk]))
        self.book.refresh_from_db()
        self.assertEqual(self.book.quantity, 5)
        self.assertEqual(
            UserActivity.objects.filter(operation_type="info").count(), 2
        )

    def test_overdue_return_records_delay_and_the_list_marks_it(self):
        record = BorrowRecord.objects.create(
            borrower=self.member.name,
            book=self.book.title,
            quantity=1,
            end_day=timezone.now() - timedelta(days=4),
        )
        self.book.quantity = 4
        self.book.status = 0
        self.book.save()

        listed = self.client.get(reverse("record_list"))
        self.assertContains(listed, "Overdue")
        self.assertContains(listed, "table-danger")

        self.client.post(reverse("record_close", args=[record.pk]))
        record.refresh_from_db()
        self.book.refresh_from_db()
        self.assertEqual(record.final_status, "Overdue")
        self.assertGreaterEqual(record.delay_days, 4)
        self.assertEqual(self.book.quantity, 5)
        self.assertEqual(self.book.status, 1)

    def test_return_of_a_missing_book_still_closes_the_record(self):
        record = BorrowRecord.objects.create(
            borrower=self.member.name, book="Gone", quantity=2
        )
        response = self.client.post(reverse("record_close", args=[record.pk]))
        self.assertRedirects(response, reverse("record_list"))
        record.refresh_from_db()
        self.assertEqual(record.open_or_close, 1)

    def test_duplicate_title_is_rejected(self):
        Book.objects.create(author="Grace", title="Guide", description="other copy")
        response = self.client.post(reverse("record_create"), self._loan_payload())
        self.assertEqual(response.status_code, 200)
        self.assertEqual(BorrowRecord.objects.count(), 0)
        self.book.refresh_from_db()
        self.assertEqual(self.book.quantity, 5)

    def test_record_page_renders_when_the_member_is_gone(self):
        record = BorrowRecord.objects.create(borrower="Nobody", book=self.book.title)
        response = self.client.get(reverse("record_detail", args=[record.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Nobody")

    def test_missing_delete_targets_are_not_found(self):
        for url in (
            reverse("book_delete", args=[999999]),
            reverse("record_delete", args=[999999]),
            reverse("member_delete", args=[999999]),
        ):
            self.assertEqual(self.client.post(url).status_code, 404, url)

    def test_staff_delete_removes_a_record_and_anonymous_cannot(self):
        record = BorrowRecord.objects.create(
            borrower=self.member.name, book=self.book.title
        )
        self.client.logout()
        denied = self.client.post(reverse("record_delete", args=[record.pk]))
        self.assertEqual(denied.status_code, 302)
        self.assertTrue(BorrowRecord.objects.filter(pk=record.pk).exists())

        self.client.force_login(self.staff)
        removed = self.client.post(reverse("record_delete", args=[record.pk]))
        self.assertRedirects(removed, reverse("record_list"))
        self.assertFalse(BorrowRecord.objects.filter(pk=record.pk).exists())


class AdminOnlyMutationTests(MutationSetup):
    def test_staff_cannot_change_groups_or_notices(self):
        notify.send(self.admin, recipient=self.admin, verb="Review the catalog")
        notice = self.admin.notifications.unread().get()
        group = Group.objects.create(name="logs")
        self.staff.groups.add(group)

        self.client.force_login(self.staff)
        denied_group = self.client.post(
            reverse("employee_update", args=[self.staff.pk]), {"api": "on"}
        )
        self.assertEqual(denied_group.status_code, 403)
        self.assertEqual(list(self.staff.groups.values_list("name", flat=True)), ["logs"])

        denied_notice = self.client.post(
            reverse("notice_update"), {"notice_id": notice.id}
        )
        self.assertEqual(denied_notice.status_code, 403)
        self.assertTrue(self.admin.notifications.unread().filter(pk=notice.pk).exists())

        self.client.logout()
        anonymous = self.client.post(reverse("notice_update"), {"notice_id": notice.id})
        self.assertEqual(anonymous.status_code, 302)
        self.assertTrue(self.admin.notifications.unread().filter(pk=notice.pk).exists())

    def test_superuser_marks_one_notice_and_unknown_ids_are_not_found(self):
        notify.send(self.staff, recipient=self.admin, verb="Review the catalog")
        notice = self.admin.notifications.unread().get()
        self.client.force_login(self.admin)
        missing = self.client.post(reverse("notice_update"), {"notice_id": 999999})
        self.assertEqual(missing.status_code, 404)
        self.assertTrue(self.admin.notifications.unread().filter(pk=notice.pk).exists())

        marked = self.client.post(reverse("notice_update"), {"notice_id": notice.id})
        self.assertRedirects(marked, reverse("category_list"))
        self.assertFalse(self.admin.notifications.unread().filter(pk=notice.pk).exists())

        notify.send(self.staff, recipient=self.admin, verb="Another note")
        cleared = self.client.post(reverse("notice_update"), {})
        self.assertRedirects(cleared, reverse("notice_list"))
        self.assertEqual(self.admin.notifications.unread().count(), 0)


class CommentMutationTests(MutationSetup):
    def test_owner_posts_a_sanitized_comment_and_others_cannot_change_it(self):
        book = Book.objects.create(author="Ada", title="Guide", description="d")
        self.client.force_login(self.staff)
        created = self.client.post(
            reverse("comment:post_comment", args=[book.pk]),
            {"body": '<script>alert(1)</script><p>hello</p>'},
        )
        self.assertRedirects(created, reverse("book_detail", args=[book.pk]))
        comment = Comment.objects.get()
        self.assertEqual(comment.user, self.staff)
        self.assertEqual(comment.book, book)
        self.assertNotIn("<script", comment.body)
        self.assertIn("hello", comment.body)

        self.client.force_login(self.admin)
        blocked = self.client.post(
            reverse("comment:comment_update", args=[comment.pk]),
            {"body": "<p>replaced</p>"},
        )
        self.assertEqual(blocked.status_code, 404)
        comment.refresh_from_db()
        self.assertIn("hello", comment.body)

        self.client.logout()
        anonymous = self.client.post(
            reverse("comment:post_comment", args=[book.pk]),
            {"body": "<p>nope</p>"},
        )
        self.assertEqual(anonymous.status_code, 302)
        self.assertEqual(Comment.objects.count(), 1)

    def test_owner_can_delete_their_comment(self):
        book = Book.objects.create(author="Ada", title="Guide", description="d")
        comment = Comment.objects.create(book=book, user=self.staff, body="<p>hello</p>")
        self.client.force_login(self.admin)
        self.assertEqual(
            self.client.post(reverse("comment:comment_delete", args=[comment.pk])).status_code,
            404,
        )
        self.assertTrue(Comment.objects.filter(pk=comment.pk).exists())

        self.client.force_login(self.staff)
        removed = self.client.post(reverse("comment:comment_delete", args=[comment.pk]))
        self.assertRedirects(removed, reverse("comment:comment_list"))
        self.assertFalse(Comment.objects.filter(pk=comment.pk).exists())


class DownloadGuardTests(MutationSetup):
    def test_unknown_dataset_is_not_found_and_staff_cannot_download(self):
        self.client.force_login(self.staff)
        denied = self.client.get(reverse("data_download", args=["book_book"]))
        self.assertEqual(denied.status_code, 403)

        self.client.force_login(self.admin)
        missing = self.client.get(reverse("data_download", args=["not_a_table"]))
        self.assertEqual(missing.status_code, 404)
