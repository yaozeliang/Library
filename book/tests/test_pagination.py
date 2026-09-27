"""Search, sort, and page query params on catalog list views.

An integer ``?page=`` past the last page is a 302 to ``page=<last>``,
keeping the rest of the query string. A non-integer or a page below 1
is a 302 that drops ``page``. An empty list renders page 1 and does not
redirect again.
"""

from datetime import timedelta
from urllib.parse import parse_qs, urlparse

from django.contrib.auth.models import Group
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from book.models import Book, BorrowRecord, Category, Member, Publisher, UserActivity
from book.tests.helpers import make_admin, make_staff, silence_weather
from book.views import PAGINATOR_NUMBER
from comment.models import Comment


class PaginationSetup(TestCase):
    def setUp(self):
        weather = silence_weather()
        weather.start()
        self.addCleanup(weather.stop)
        self.staff = make_staff()
        self.admin = make_admin()
        self.client.force_login(self.staff)

    def query(self, response):
        self.assertEqual(response.status_code, 302, response.get("Location"))
        return parse_qs(urlparse(response["Location"]).query)

    def follow(self, response):
        followed = self.client.get(response["Location"])
        self.assertEqual(followed.status_code, 200)
        return followed


class BookCategoryPublisherMemberPaginationTests(PaginationSetup):
    def test_book_list_redirects_page_four_and_ignores_a_bad_sort(self):
        for index in range(PAGINATOR_NUMBER + 1):
            Book.objects.create(
                author="Ada",
                title=f"Title-{index:02d}",
                description="A short guide",
            )
        url = reverse("book_list")
        too_far = self.client.get(url, {"page": 4, "orderby": "title"})
        huge = self.client.get(url, {"page": 999, "orderby": "title", "search": "Title"})
        nonsense = self.client.get(url, {"page": "abc", "orderby": "title"})
        negative = self.client.get(url, {"page": 0, "orderby": "title"})
        below = self.client.get(url, {"page": -3, "orderby": "title"})
        on_last = self.client.get(url, {"page": 2, "orderby": "title"})
        invalid_sort = self.client.get(url, {"orderby": "not_a_field"})

        self.assertEqual(
            self.query(too_far), {"page": ["2"], "orderby": ["title"]}
        )
        self.assertEqual(
            self.query(huge),
            {"page": ["2"], "orderby": ["title"], "search": ["Title"]},
        )
        self.assertEqual(self.query(nonsense), {"orderby": ["title"]})
        self.assertEqual(self.query(negative), {"orderby": ["title"]})
        self.assertEqual(self.query(below), {"orderby": ["title"]})
        self.assertEqual(on_last.status_code, 200)
        self.assertEqual(invalid_sort.status_code, 200)

        last_page = self.follow(too_far)
        self.assertContains(last_page, "Title-05")
        self.assertNotContains(last_page, "Title-00")
        self.assertContains(last_page, f"Total {PAGINATOR_NUMBER + 1} books")
        first_page = self.follow(nonsense)
        self.assertContains(first_page, "Title-00")
        self.assertNotContains(first_page, "Title-05")

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

    def test_empty_book_list_page_four_stops_at_page_one(self):
        url = reverse("book_list")
        too_far = self.client.get(url, {"page": 4, "orderby": "title"})
        self.assertEqual(self.query(too_far), {"page": ["1"], "orderby": ["title"]})
        landed = self.follow(too_far)
        self.assertContains(landed, "Total 0 books")
        again = self.client.get(url, {"page": 1, "orderby": "title"})
        self.assertEqual(again.status_code, 200)
        dropped = self.client.get(url, {"page": "nope"})
        self.assertEqual(self.query(dropped), {})
        self.assertEqual(self.client.get(url).status_code, 200)

    def test_category_list_redirects_out_of_range_pages(self):
        for index in range(PAGINATOR_NUMBER + 1):
            Category.objects.create(name=f"Cat-{index:02d}")
        url = reverse("category_list")
        too_far = self.client.get(url, {"page": 4, "orderby": "name", "search": "Cat"})
        nonsense = self.client.get(url, {"page": "nope", "orderby": "name"})
        self.assertEqual(
            self.query(too_far),
            {"page": ["2"], "orderby": ["name"], "search": ["Cat"]},
        )
        landed = self.follow(too_far)
        self.assertContains(landed, "Cat-05")
        self.assertNotContains(landed, "Cat-00")
        self.assertContains(landed, f"Total {PAGINATOR_NUMBER + 1} categories")
        self.assertEqual(self.query(nonsense), {"orderby": ["name"]})
        self.assertContains(self.follow(nonsense), "Cat-00")
        empty = self.client.get(url, {"page": 9, "search": "missing"})
        self.assertEqual(self.query(empty), {"page": ["1"], "search": ["missing"]})
        self.assertEqual(
            self.client.get(url, {"page": 1, "search": "missing"}).status_code, 200
        )

    def test_publisher_list_redirects_out_of_range_pages(self):
        for index in range(PAGINATOR_NUMBER + 1):
            Publisher.objects.create(name=f"Pub-{index:02d}", city="Paris")
        url = reverse("publisher_list")
        too_far = self.client.get(url, {"page": 999, "orderby": "name"})
        fractional = self.client.get(url, {"page": "2.5", "orderby": "name"})
        self.assertEqual(self.query(too_far), {"page": ["2"], "orderby": ["name"]})
        landed = self.follow(too_far)
        self.assertContains(landed, "Pub-05")
        self.assertNotContains(landed, "Pub-00")
        self.assertContains(landed, f"Total {PAGINATOR_NUMBER + 1} publishers")
        self.assertEqual(self.query(fractional), {"orderby": ["name"]})
        self.assertContains(self.follow(fractional), "Pub-00")

    def test_member_list_redirects_out_of_range_pages(self):
        for index in range(PAGINATOR_NUMBER + 1):
            Member.objects.create(
                name=f"Mem-{index:02d}", city="Paris", phone_number=f"0600{index:04d}"
            )
        url = reverse("member_list")
        too_far = self.client.get(url, {"page": 4, "orderby": "name"})
        nonsense = self.client.get(url, {"page": "nope", "orderby": "name"})
        bad_sort = self.client.get(url, {"orderby": "password", "page": 99})
        self.assertEqual(self.query(too_far), {"page": ["2"], "orderby": ["name"]})
        landed = self.follow(too_far)
        self.assertContains(landed, "Mem-05")
        self.assertNotContains(landed, "Mem-00")
        self.assertContains(landed, f"Total {PAGINATOR_NUMBER + 1} members")
        self.assertEqual(self.query(nonsense), {"orderby": ["name"]})
        self.assertContains(self.follow(nonsense), "Mem-00")
        self.assertEqual(self.query(bad_sort), {"page": ["2"], "orderby": ["password"]})
        self.assertEqual(self.follow(bad_sort).status_code, 200)


class BorrowRecordPaginationTests(PaginationSetup):
    def test_record_list_page_four_redirects_to_the_last_page(self):
        """``/record-list/?page=4`` with only two pages must not render page 4."""
        names = [f"reader-{letter}" for letter in ("z", "m", "a", "b", "y", "c")]
        for name in names:
            BorrowRecord.objects.create(borrower=name, book="Guide")
        self.assertEqual(len(names), PAGINATOR_NUMBER + 1)

        url = reverse("record_list")
        page_four = self.client.get(url, {"page": 4, "orderby": "borrower"})
        huge = self.client.get(
            url, {"page": 99, "orderby": "borrower", "search": "reader"}
        )
        nonsense = self.client.get(url, {"page": "4abc"})
        on_last = self.client.get(url, {"page": 2, "orderby": "borrower"})

        self.assertEqual(self.query(page_four), {"page": ["2"], "orderby": ["borrower"]})
        self.assertEqual(
            self.query(huge),
            {"page": ["2"], "orderby": ["borrower"], "search": ["reader"]},
        )
        self.assertEqual(self.query(nonsense), {})
        self.assertEqual(on_last.status_code, 200)

        last_page = self.follow(page_four)
        self.assertContains(last_page, "reader-z")
        self.assertNotContains(last_page, "reader-a")
        self.assertContains(last_page, f"Total {len(names)} records")
        self.assertContains(self.follow(huge), "reader-z")
        self.assertContains(self.follow(nonsense), "reader-a")

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

    def test_empty_record_list_page_four_stops_at_page_one(self):
        url = reverse("record_list")
        too_far = self.client.get(url, {"page": 4})
        self.assertEqual(self.query(too_far), {"page": ["1"]})
        landed = self.follow(too_far)
        self.assertContains(landed, "Total 0 records")
        self.assertEqual(self.client.get(url, {"page": 1}).status_code, 200)
        self.assertEqual(self.client.get(url).status_code, 200)


class ActivityListPaginationTests(PaginationSetup):
    def setUp(self):
        super().setUp()
        logs = Group.objects.create(name="logs")
        self.staff.groups.add(logs)

    def test_activity_pages_redirect_when_out_of_range(self):
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
        page_four = self.client.get(url, {"page": 4, "created_by": "staff"})
        nonsense = self.client.get(url, {"page": "abc", "created_by": "staff"})
        self.assertEqual(
            self.query(page_four), {"page": ["2"], "created_by": ["staff"]}
        )
        last_page = self.follow(page_four)
        self.assertContains(last_page, "Model-05")
        self.assertNotContains(last_page, "Model-00")
        self.assertEqual(self.query(nonsense), {"created_by": ["staff"]})
        self.assertContains(self.follow(nonsense), "Model-00")
        self.assertEqual(
            self.client.get(url, {"orderby": "not_a_field"}).status_code, 200
        )

        filtered = self.client.get(url, {"search": "Model-0", "created_by": "staff"})
        self.assertEqual(filtered.status_code, 200)
        self.assertContains(filtered, f"Total {PAGINATOR_NUMBER + 1} activities")

    def test_empty_activity_list_does_not_redirect_loop(self):
        url = reverse("user_activity_list")
        too_far = self.client.get(url, {"page": 999, "created_by": "staff"})
        self.assertEqual(
            self.query(too_far), {"page": ["1"], "created_by": ["staff"]}
        )
        self.assertEqual(self.follow(too_far).status_code, 200)
        self.assertEqual(
            self.client.get(url, {"page": 1, "created_by": "staff"}).status_code, 200
        )


class CommentListPaginationTests(PaginationSetup):
    def test_comment_list_redirects_out_of_range_pages(self):
        book = Book.objects.create(author="Ada", title="Notes", description="d")
        now = timezone.now()
        total = 11
        for index in range(total):
            comment = Comment.objects.create(
                book=book, user=self.staff, body=f"note-{index:02d}"
            )
            Comment.objects.filter(pk=comment.pk).update(
                created_at=now - timedelta(minutes=index)
            )

        url = reverse("comment:comment_list")
        too_far = self.client.get(url, {"page": 4})
        nonsense = self.client.get(url, {"page": "abc"})
        self.assertEqual(self.query(too_far), {"page": ["2"]})
        last_page = self.follow(too_far)
        self.assertContains(last_page, "note-10")
        self.assertNotContains(last_page, "note-00")
        self.assertEqual(self.query(nonsense), {})
        self.assertContains(self.follow(nonsense), "note-00")
        self.assertEqual(self.client.get(url, {"page": 1}).status_code, 200)

    def test_empty_comment_list_stops_at_page_one(self):
        url = reverse("comment:comment_list")
        too_far = self.client.get(url, {"page": 4})
        self.assertEqual(self.query(too_far), {"page": ["1"]})
        landed = self.follow(too_far)
        self.assertContains(landed, "No comments yet.")
        self.assertEqual(self.client.get(url, {"page": 1}).status_code, 200)
