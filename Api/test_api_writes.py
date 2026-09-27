"""Required fields and success status for library API writes.

Category and publisher names are optional on the model (``blank=True``,
not unique). The API still requires a real name. Other invalid writes
that already returned 400 stay 400. Creates return 201; updates stay 200.
"""

from django.contrib.auth.models import Group, User
from django.test import TestCase
from rest_framework.test import APIClient

from book.models import Book, Category, Member, Publisher

_BOOK = {"author": "Ada", "title": "Guide", "description": "A short guide"}
_MEMBER = {"name": "Pat", "city": "Paris", "phone_number": "0600000000"}


class ApiWriteTests(TestCase):
    def setUp(self):
        group = Group.objects.create(name="api")
        user = User.objects.create_user(
            username="api-staff", password="api-pass-1", is_staff=True
        )
        user.groups.add(group)
        self.client = APIClient()
        self.client.force_login(user)

    def test_category_name_is_required_and_not_unique(self):
        self.assertFalse(Category._meta.get_field("name").unique)

        missing = self.client.post("/api/category-create/", {}, format="json")
        self.assertEqual(missing.status_code, 400)
        self.assertIn("name", missing.json())
        self.assertIn("required", " ".join(missing.json()["name"]).lower())
        self.assertEqual(Category.objects.count(), 0)

        for payload in ({"name": ""}, {"name": "   "}, {"name": "\t"}):
            rejected = self.client.post(
                "/api/category-create/", payload, format="json"
            )
            self.assertEqual(rejected.status_code, 400, payload)
            self.assertIn("name", rejected.json())
            self.assertEqual(Category.objects.count(), 0)

        created = self.client.post(
            "/api/category-create/", {"name": "  Fiction  "}, format="json"
        )
        self.assertEqual(created.status_code, 201)
        self.assertEqual(created.json()["name"], "Fiction")
        self.assertEqual(Category.objects.get().name, "Fiction")

        # The column is not unique, so the same name is another row.
        duplicate = self.client.post(
            "/api/category-create/", {"name": "Fiction"}, format="json"
        )
        self.assertEqual(duplicate.status_code, 201)
        self.assertEqual(Category.objects.filter(name="Fiction").count(), 2)

    def test_publisher_name_is_required_and_city_and_contact_stay_optional(self):
        self.assertFalse(Publisher._meta.get_field("name").unique)

        missing = self.client.post("/api/publisher-create/", {}, format="json")
        self.assertEqual(missing.status_code, 400)
        self.assertIn("name", missing.json())
        self.assertIn("required", " ".join(missing.json()["name"]).lower())
        self.assertNotIn("city", missing.json())
        self.assertNotIn("contact", missing.json())
        self.assertEqual(Publisher.objects.count(), 0)

        for payload in (
            {"name": ""},
            {"name": "   ", "city": "Paris"},
            {"name": "", "city": "", "contact": ""},
        ):
            rejected = self.client.post(
                "/api/publisher-create/", payload, format="json"
            )
            self.assertEqual(rejected.status_code, 400, payload)
            self.assertIn("name", rejected.json())
            self.assertEqual(Publisher.objects.count(), 0)

        created = self.client.post(
            "/api/publisher-create/", {"name": "  Press  "}, format="json"
        )
        self.assertEqual(created.status_code, 201)
        self.assertEqual(created.json()["name"], "Press")
        self.assertEqual(created.json()["city"], "")
        self.assertEqual(created.json()["contact"], "")
        publisher = Publisher.objects.get()
        self.assertEqual(publisher.name, "Press")

        duplicate = self.client.post(
            "/api/publisher-create/",
            {"name": "Press", "city": "Lyon", "contact": ""},
            format="json",
        )
        self.assertEqual(duplicate.status_code, 201)
        self.assertEqual(Publisher.objects.filter(name="Press").count(), 2)

        blanked = self.client.post(
            f"/api/publisher-update/{publisher.pk}/",
            {"name": "   ", "city": "Lyon", "contact": ""},
            format="json",
        )
        self.assertEqual(blanked.status_code, 400)
        self.assertIn("name", blanked.json())
        publisher.refresh_from_db()
        self.assertEqual(publisher.name, "Press")
        self.assertEqual(publisher.city, "")

        omitted = self.client.post(
            f"/api/publisher-update/{publisher.pk}/",
            {"city": "Lyon"},
            format="json",
        )
        self.assertEqual(omitted.status_code, 400)
        self.assertIn("required", " ".join(omitted.json()["name"]).lower())
        publisher.refresh_from_db()
        self.assertEqual(publisher.name, "Press")
        self.assertEqual(publisher.city, "")

        renamed = self.client.post(
            f"/api/publisher-update/{publisher.pk}/",
            {"name": "Press House", "city": "Lyon"},
            format="json",
        )
        self.assertEqual(renamed.status_code, 200)
        publisher.refresh_from_db()
        self.assertEqual(publisher.name, "Press House")
        self.assertEqual(publisher.city, "Lyon")

    def test_invalid_writes_that_already_fail_stay_400(self):
        """Keep the invalid inputs that already returned 400."""
        book = Book.objects.create(
            author="Ada", title="Guide", description="A short guide"
        )
        member = Member.objects.create(
            name="Pat", city="Paris", phone_number="0600000000"
        )
        cases = (
            ("post", "/api/category-create/", {"name": "x" * 51}),
            ("post", "/api/book-create/", {}),
            ("post", "/api/book-create/", {"author": "Ada", "title": "Guide"}),
            (
                "post",
                "/api/book-create/",
                {"author": "Ada", "title": "Guide", "description": ""},
            ),
            (
                "post",
                "/api/book-create/",
                {"author": "Ada", "title": "   ", "description": "d"},
            ),
            (
                "post",
                "/api/book-create/",
                {"author": "   ", "title": "Guide", "description": "d"},
            ),
            (
                "post",
                "/api/book-create/",
                {**_BOOK, "quantity": -1},
            ),
            (
                "post",
                "/api/book-create/",
                {**_BOOK, "title": "Other", "floor_number": 9},
            ),
            ("post", f"/api/book-update/{book.pk}/", {}),
            ("post", f"/api/book-update/{book.pk}/", {"title": "Only"}),
            (
                "post",
                f"/api/book-update/{book.pk}/",
                {"author": "Ada", "title": "   ", "description": "d"},
            ),
            (
                "post",
                "/api/publisher-create/",
                {"name": "Press", "city": "Paris", "contact": "not-an-email"},
            ),
            ("post", "/api/members/", {}),
            ("post", "/api/members/", {"name": "Pat"}),
            (
                "post",
                "/api/members/",
                {"name": "   ", "city": "Paris", "phone_number": "1"},
            ),
            (
                "post",
                "/api/members/",
                {"name": "Pat", "city": "", "phone_number": "1"},
            ),
            (
                "post",
                "/api/members/",
                {"name": "Pat", "city": "Paris", "phone_number": ""},
            ),
            (
                "post",
                "/api/members/",
                {**_MEMBER, "email": "not-an-email"},
            ),
            ("put", f"/api/members/{member.pk}", {}),
            ("put", f"/api/members/{member.pk}", {"name": "Pat", "city": "Paris"}),
            (
                "put",
                f"/api/members/{member.pk}",
                {"name": "   ", "city": "Paris", "phone_number": "1"},
            ),
        )
        self.assertEqual(len(cases), 21)
        before = {
            "categories": Category.objects.count(),
            "books": Book.objects.count(),
            "publishers": Publisher.objects.count(),
            "members": Member.objects.count(),
        }
        for method, path, payload in cases:
            response = getattr(self.client, method)(path, payload, format="json")
            self.assertEqual(
                response.status_code,
                400,
                (path, payload, response.json()),
            )

        book.refresh_from_db()
        member.refresh_from_db()
        self.assertEqual(book.title, "Guide")
        self.assertEqual(book.description, "A short guide")
        self.assertEqual(member.name, "Pat")
        self.assertEqual(Category.objects.count(), before["categories"])
        self.assertEqual(Book.objects.count(), before["books"])
        self.assertEqual(Publisher.objects.count(), before["publishers"])
        self.assertEqual(Member.objects.count(), before["members"])

    def test_creates_are_201_and_updates_stay_200(self):
        category = self.client.post(
            "/api/category-create/", {"name": "Fiction"}, format="json"
        )
        book = self.client.post("/api/book-create/", _BOOK, format="json")
        publisher = self.client.post(
            "/api/publisher-create/",
            {"name": "Press", "city": "Paris", "contact": "press@example.com"},
            format="json",
        )
        member = self.client.post("/api/members/", _MEMBER, format="json")
        for response in (category, book, publisher, member):
            self.assertEqual(response.status_code, 201, response.json())

        updated_book = self.client.post(
            f"/api/book-update/{book.json()['id']}/",
            {**_BOOK, "description": "Revised"},
            format="json",
        )
        updated_publisher = self.client.post(
            f"/api/publisher-update/{publisher.json()['id']}/",
            {"name": "Press House", "city": "Lyon", "contact": ""},
            format="json",
        )
        updated_member = self.client.put(
            f"/api/members/{member.json()['id']}",
            {**_MEMBER, "city": "Lyon"},
            format="json",
        )
        for response in (updated_book, updated_publisher, updated_member):
            self.assertEqual(response.status_code, 200, response.json())
        self.assertEqual(
            Book.objects.get(pk=book.json()["id"]).description, "Revised"
        )
        self.assertEqual(
            Publisher.objects.get(pk=publisher.json()["id"]).name, "Press House"
        )
        self.assertEqual(Member.objects.get(pk=member.json()["id"]).city, "Lyon")
