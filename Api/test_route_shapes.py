"""JSON shape, empty tables, missing ids, and invalid writes for /api/."""

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from book.models import Book, Category, Member, Publisher

_BOOK = {
    "author": "Ada",
    "title": "Guide",
    "description": "A short guide",
    "quantity": 2,
    "floor_number": 1,
    "bookshelf_number": "0001",
}


class ApiRouteShapeTests(TestCase):
    def setUp(self):
        self.superuser = User.objects.create_superuser(
            username="api-shape-root",
            email="api-shape@example.com",
            password="pass12345",
        )
        self.staff = User.objects.create_user(
            username="api-shape-staff", password="pass12345", is_staff=True
        )
        self.client = APIClient()

    def test_empty_lists_are_json_arrays(self):
        self.client.force_login(self.superuser)
        for path in (
            "/api/category-list/",
            "/api/book-list/",
            "/api/publisher-list/",
            "/api/members/",
            "/api/category-list.json",
        ):
            response = self.client.get(path)
            self.assertEqual(response.status_code, 200, path)
            self.assertIn("application/json", response["Content-Type"])
            self.assertEqual(response.json(), [])

        overview = self.client.get(reverse("api-overview"))
        self.assertEqual(overview.status_code, 200)
        self.assertIsInstance(overview.json(), dict)
        self.assertIn("/api/book-list/", overview.json().values())
        self.assertTrue(all(isinstance(path, str) for path in overview.json().values()))

        self.client.force_login(self.staff)
        denied = self.client.get("/api/book-list/")
        self.assertEqual(denied.status_code, 403)
        self.client.logout()
        anonymous = self.client.get("/api/book-list/")
        self.assertIn(anonymous.status_code, (401, 403))

    def test_detail_shape_missing_id_and_invalid_writes(self):
        self.client.force_login(self.superuser)
        category = Category.objects.create(name="Fiction")
        publisher = Publisher.objects.create(name="Press", city="Paris")
        book = Book.objects.create(
            author="Ada", title="Guide", description="A short guide", quantity=2
        )
        member = Member.objects.create(
            name="Pat", city="Paris", phone_number="0600000000"
        )

        listed = self.client.get("/api/book-list/")
        self.assertEqual(listed.status_code, 200)
        row = listed.json()[0]
        for key in ("id", "author", "title", "description", "quantity", "created_at"):
            self.assertIn(key, row)
        self.assertEqual(row["title"], "Guide")

        detail = self.client.get(f"/api/book-detail/{book.pk}/")
        self.assertEqual(detail.status_code, 200)
        self.assertEqual(detail.json()["id"], book.pk)

        for path in (
            f"/api/category-detail/{category.pk}/",
            f"/api/book-detail/{book.pk}/",
            f"/api/members/{member.pk}",
        ):
            self.assertEqual(self.client.get(path).status_code, 200, path)

        for path in (
            "/api/category-detail/999999/",
            "/api/book-detail/999999/",
            "/api/members/999999",
            "/api/book-update/999999/",
            "/api/publisher-update/999999/",
            "/api/category-delete/999999/",
            "/api/book-delete/999999/",
            "/api/publisher-delete/999999/",
        ):
            method = "get"
            if path.endswith("update/999999/") or "update/" in path:
                method = "post"
            if "delete" in path:
                method = "delete"
            response = getattr(self.client, method)(path, _BOOK, format="json")
            self.assertEqual(response.status_code, 404, path)

        member_missing = self.client.delete("/api/members/999999")
        self.assertEqual(member_missing.status_code, 404)

        bad_category = self.client.post(
            "/api/category-create/", {"name": "x" * 51}, format="json"
        )
        self.assertEqual(bad_category.status_code, 400)
        self.assertIn("name", bad_category.json())
        self.assertFalse(Category.objects.filter(name="x" * 51).exists())

        bad_book = self.client.post("/api/book-create/", {"author": "Ada"}, format="json")
        self.assertEqual(bad_book.status_code, 400)
        self.assertIn("title", bad_book.json())

        bad_publisher = self.client.post(
            "/api/publisher-create/",
            {"name": "Press 2", "contact": "not-an-email"},
            format="json",
        )
        self.assertEqual(bad_publisher.status_code, 400)
        self.assertIn("contact", bad_publisher.json())

        bad_member = self.client.post("/api/members/", {"name": ""}, format="json")
        self.assertEqual(bad_member.status_code, 400)

        created = self.client.post(
            "/api/category-create/", {"name": "Mystery"}, format="json"
        )
        self.assertEqual(created.status_code, 200)
        self.assertEqual(created.json()["name"], "Mystery")

        updated = self.client.post(
            f"/api/publisher-update/{publisher.pk}/",
            {"name": "Updated Press", "city": "Lyon", "contact": ""},
            format="json",
        )
        self.assertEqual(updated.status_code, 200)
        publisher.refresh_from_db()
        self.assertEqual(publisher.name, "Updated Press")

        changed = self.client.put(
            f"/api/members/{member.pk}",
            {
                "name": "Pat Updated",
                "gender": "f",
                "age": 22,
                "email": "pat@example.com",
                "city": "Lyon",
                "phone_number": "0600000001",
            },
            format="json",
        )
        self.assertEqual(changed.status_code, 200)
        member.refresh_from_db()
        self.assertEqual(member.name, "Pat Updated")

        invalid_put = self.client.put(
            f"/api/members/{member.pk}", {"name": ""}, format="json"
        )
        self.assertEqual(invalid_put.status_code, 400)

        removed = self.client.delete(f"/api/members/{member.pk}")
        self.assertEqual(removed.status_code, 204)
        self.assertFalse(Member.objects.filter(pk=member.pk).exists())

    def test_browsable_api_auth_pages(self):
        login = self.client.get("/api/api-auth/login/")
        self.assertEqual(login.status_code, 200)
        self.client.force_login(self.superuser)
        logout = self.client.get("/api/api-auth/logout/")
        self.assertIn(logout.status_code, (200, 302, 405))
