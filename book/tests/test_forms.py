"""Validation for catalog forms. Auth and sign-up forms are out of scope."""

from django.test import TestCase

from book.forms import (
    BookCreateEditForm,
    BorrowRecordCreateForm,
    MemberCreateEditForm,
    ProfileForm,
    PubCreateEditForm,
)
from comment.forms import CommentForm


class BookFormTests(TestCase):
    def test_required_fields_and_negative_quantity(self):
        empty = BookCreateEditForm(data={})
        self.assertFalse(empty.is_valid())
        self.assertIn("author", empty.errors)
        self.assertIn("title", empty.errors)
        self.assertIn("description", empty.errors)

        negative = BookCreateEditForm(
            data={
                "author": "Ada",
                "title": "Guide",
                "description": "A short guide",
                "quantity": -1,
                "floor_number": 1,
                "bookshelf_number": "0001",
            }
        )
        self.assertFalse(negative.is_valid())
        self.assertIn("quantity", negative.errors)

    def test_valid_book_accepts_optional_category(self):
        form = BookCreateEditForm(
            data={
                "author": "Ada",
                "title": "Guide",
                "description": "A short guide",
                "quantity": 4,
                "floor_number": 2,
                "bookshelf_number": "0008",
            }
        )
        self.assertTrue(form.is_valid(), form.errors)


class PublisherAndMemberFormTests(TestCase):
    def test_publisher_rejects_a_bad_email_and_accepts_a_blank_one(self):
        invalid = PubCreateEditForm(
            data={"name": "Press", "city": "Paris", "contact": "not-an-email"}
        )
        self.assertFalse(invalid.is_valid())
        self.assertIn("contact", invalid.errors)

        blank = PubCreateEditForm(data={"name": "Press", "city": "Paris", "contact": ""})
        self.assertTrue(blank.is_valid(), blank.errors)

    def test_member_requires_name_city_and_phone_and_validates_email(self):
        missing = MemberCreateEditForm(data={"gender": "m", "age": 20})
        self.assertFalse(missing.is_valid())
        for field in ("name", "city", "phone_number"):
            self.assertIn(field, missing.errors)

        bad_email = MemberCreateEditForm(
            data={
                "name": "Ada",
                "gender": "f",
                "age": 30,
                "email": "nope",
                "city": "Paris",
                "phone_number": "0600",
            }
        )
        self.assertFalse(bad_email.is_valid())
        self.assertIn("email", bad_email.errors)

        valid = MemberCreateEditForm(
            data={
                "name": "Ada",
                "gender": "f",
                "age": 30,
                "email": "ada@example.com",
                "city": "Paris",
                "phone_number": "0600",
            }
        )
        self.assertTrue(valid.is_valid(), valid.errors)


class BorrowAndProfileFormTests(TestCase):
    def _payload(self, **overrides):
        data = {
            "borrower": "Ada",
            "book": "Guide",
            "quantity": 1,
            "start_day": "2026-09-01",
            "end_day": "2026-09-08",
        }
        data.update(overrides)
        return data

    def test_rejects_zero_quantity_and_a_return_before_the_borrow_date(self):
        zero = BorrowRecordCreateForm(data=self._payload(quantity=0))
        self.assertFalse(zero.is_valid())
        self.assertIn("quantity", zero.errors)

        backwards = BorrowRecordCreateForm(
            data=self._payload(start_day="2026-09-10", end_day="2026-09-01")
        )
        self.assertFalse(backwards.is_valid())
        self.assertIn("end_day", backwards.errors)

    def test_accepts_a_normal_loan(self):
        form = BorrowRecordCreateForm(data=self._payload())
        self.assertTrue(form.is_valid(), form.errors)

    def test_profile_bio_is_required(self):
        empty = ProfileForm(data={"bio": "", "phone_number": "", "email": ""})
        self.assertFalse(empty.is_valid())
        self.assertIn("bio", empty.errors)

        bad_email = ProfileForm(
            data={"bio": "Hello", "phone_number": "0600", "email": "nope"}
        )
        self.assertFalse(bad_email.is_valid())
        self.assertIn("email", bad_email.errors)

        valid = ProfileForm(
            data={"bio": "Hello", "phone_number": "0600", "email": "ada@example.com"}
        )
        self.assertTrue(valid.is_valid(), valid.errors)


class CommentFormTests(TestCase):
    def test_body_is_optional_and_kept_for_later_sanitizing(self):
        empty = CommentForm(data={"body": ""})
        self.assertTrue(empty.is_valid(), empty.errors)

        filled = CommentForm(data={"body": "<p>hello</p>"})
        self.assertTrue(filled.is_valid(), filled.errors)
        self.assertIn("<p>hello</p>", filled.cleaned_data["body"])
