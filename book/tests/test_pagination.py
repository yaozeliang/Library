"""Search, sort, and page query params on catalog list views.

Out-of-range ``?page=`` must clamp to the last page that still has rows.
A non-integer page opens the first page. Neither case may 500 or render an
empty table while earlier pages have results.
"""

from datetime import timedelta

from django.contrib.auth.models import Group
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from book.models import Book, BorrowRecord, Category, Member, Publisher, UserActivity
from book.tests.helpers import make_admin, make_staff, silence_weather
from book.views import PAGINATOR_NUMBER


class PaginationSetup(TestCase):
    def setUp(self):
        weather = silence_weather()
        weather.start()
        self.addCleanup(weather.stop)
        self.staff = make_staff()
        self.admin = make_admin()
        self.client.force_login(self.staff)

    def assert_clamped(self, url, needle_on_last, needle_on_first, total_label):
        first = self.client.get(url, {"page": 1, "orderby": "title"})
        last_number = 2
        last = self.client.get(url, {"page": last_number, "orderby": "title"})
        too_far = self.client.get(url, {"page": 4, "orderby": "title"})
        nonsense = self.client.get(url, {"page": "abc", "orderby": "title"})
        negative = self.client.get(url, {"page": 0, "orderby": "title"})
        invalid_sort = self.client.get(url, {"page": 4, "orderby": "not_a_field"})

        for response in (first, last, too_far, nonsense, negative, invalid_sort):
            self.assertEqual(response.status_code, 200, response.request["PATH_INFO"])
            self.assertContains(response, total_label)

        self.assertContains(first, needle_on_first)
        self.assertNotContains(first, needle_on_last)
        self.assertContains(last, needle_on_last)
        self.assertContains(too_far, needle_on_last)
        self.assertNotContains(too_far, needle_on_first)
        self.assertContains(nonsense, needle_on_first)
        self.assertContains(negative, needle_on_last)
        self.assertEqual(invalid_sort.status_code, 200)


class BookCategoryPublisherMemberPaginationTests(PaginationSetup):
    def test_book_list_clamps_page_four_and_ignores_a_bad_sort(self):
        for index in range(PAGINATOR_NUMBER + 1):
            Book.objects.create(
                author="Ada",
                title=f"Title-{index:02d}",
                description="A short guide",
            )
        self.assert_clamped(
            reverse("book_list"),
            needle_on_last="Title-05",
            needle_on_first="Title-00",
            total_label=f"Total {PAGINATOR_NUMBER + 1} books",
        )

    def test_book_search_keeps_the_requested_order(self):
        Book.objects.create(author="Zoe", title="Zebra", description="d")
        Book.objects.create(author="Amy", title="Aardvark", description="d")
        response = self.client.get(
            reverse("book_list"), {"search": "a", "orderby": "author"}
        )
        self.assertEqual(response.status_code, 200)
        html = response.content.decode()
        self.assertLess(html.index("Amy"), html.index("Zoe"))
        self.assertContains(response, "Total 2 books")

    def test_empty_book_list_page_four_is_not_an_error(self):
        response = self.client.get(reverse("book_list"), {"page": 4})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Total 0 books")

    def test_category_publisher_and_member_lists_clamp_too(self):
        for index in range(PAGINATOR_NUMBER + 1):
            Category.objects.create(name=f"Cat-{index:02d}")
            Publisher.objects.create(name=f"Pub-{index:02d}", city="Paris")
            Member.objects.create(
                name=f"Mem-{index:02d}", city="Paris", phone_number=f"0600{index:04d}"
            )

        cases = (
            (reverse("category_list"), "Cat-05", "Cat-00", "categories"),
            (reverse("publisher_list"), "Pub-05", "Pub-00", "publishers"),
            (reverse("member_list"), "Mem-05", "Mem-00", "members"),
        )
        for url, last_name, first_name, label in cases:
            too_far = self.client.get(url, {"page": 4, "orderby": "name"})
            nonsense = self.client.get(url, {"page": "nope", "orderby": "name"})
            self.assertEqual(too_far.status_code, 200, url)
            self.assertContains(too_far, last_name)
            self.assertNotContains(too_far, first_name)
            self.assertContains(too_far, f"Total {PAGINATOR_NUMBER + 1} {label}")
            self.assertEqual(nonsense.status_code, 200, url)
            self.assertContains(nonsense, first_name)

        bad_sort = self.client.get(
            reverse("member_list"), {"orderby": "password", "page": 99}
        )
        self.assertEqual(bad_sort.status_code, 200)


class BorrowRecordPaginationTests(PaginationSetup):
    def test_record_list_page_four_shows_the_last_page(self):
        """``/record-list/?page=4`` with only two pages must not be empty or 500."""
        names = [f"reader-{letter}" for letter in ("z", "m", "a", "b", "y", "c")]
        for name in names:
            BorrowRecord.objects.create(borrower=name, book="Guide")
        self.assertEqual(len(names), PAGINATOR_NUMBER + 1)

        url = reverse("record_list")
        last = self.client.get(url, {"page": 2, "orderby": "borrower"})
        page_four = self.client.get(url, {"page": 4, "orderby": "borrower"})
        huge = self.client.get(url, {"page": 99, "orderby": "borrower"})
        nonsense = self.client.get(url, {"page": "4abc"})

        for response in (last, page_four, huge, nonsense):
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, f"Total {len(names)} records")

        self.assertContains(page_four, "reader-z")
        self.assertNotContains(page_four, "reader-a")
        self.assertContains(huge, "reader-z")
        self.assertContains(nonsense, "reader-a")
        self.assertContains(last, "reader-z")

    def test_record_search_does_not_drop_the_sort(self):
        for name in ("reader-z", "reader-a", "reader-m"):
            BorrowRecord.objects.create(borrower=name, book="Guide")
        response = self.client.get(
            reverse("record_list"), {"search": "reader", "orderby": "borrower"}
        )
        self.assertEqual(response.status_code, 200)
        html = response.content.decode()
        self.assertLess(html.index("reader-a"), html.index("reader-m"))
        self.assertLess(html.index("reader-m"), html.index("reader-z"))
        self.assertContains(response, "Total 3 records")

    def test_empty_record_list_page_four_renders(self):
        response = self.client.get(reverse("record_list"), {"page": 4})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Total 0 records")


class ActivityListPaginationTests(PaginationSetup):
    def test_activity_pages_are_ordered_and_clamped(self):
        logs = Group.objects.create(name="logs")
        self.staff.groups.add(logs)
        now = timezone.now()
        for index in range(PAGINATOR_NUMBER + 1):
            activity = UserActivity.objects.create(
                created_by="staff",
                target_model=f"Model-{index:02d}",
                detail=f"row {index}",
            )
            UserActivity.objects.filter(pk=activity.pk).update(
                created_at=now - timedelta(days=index)
            )

        url = reverse("user_activity_list")
        page_four = self.client.get(url, {"page": 4})
        nonsense = self.client.get(url, {"page": "abc"})
        self.assertEqual(page_four.status_code, 200)
        self.assertContains(page_four, "Model-05")
        self.assertNotContains(page_four, "Model-00")
        self.assertContains(nonsense, "Model-00")
        self.assertEqual(
            self.client.get(url, {"orderby": "not_a_field", "page": 9}).status_code,
            200,
        )

        filtered = self.client.get(url, {"search": "Model-0", "created_by": "staff"})
        self.assertEqual(filtered.status_code, 200)
        self.assertContains(filtered, f"Total {PAGINATOR_NUMBER + 1} activities")
