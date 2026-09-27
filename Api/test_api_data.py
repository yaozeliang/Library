"""JSON shapes for the library API, including empty lists and rejected writes."""

from django.contrib.auth.models import Group, User
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from book.models import Book, Category, Member, Publisher


class ApiDataTests(TestCase):
    def setUp(self):
        self.group = Group.objects.create(name="api")
        self.user = User.objects.create_user(
            username="api-staff", password="api-pass-1", is_staff=True
        )
        self.user.groups.add(self.group)
        self.client = APIClient()
        self.client.force_login(self.user)
        self.anonymous = APIClient()

    def test_lists_are_empty_arrays_before_any_rows_exist(self):
        for path in (
            "/api/category-list/",
            "/api/book-list/",
            "/api/publisher-list/",
            "/api/members/",
        ):
            response = self.client.get(path)
            self.assertEqual(response.status_code, 200, path)
            self.assertEqual(response.json(), [])

    def test_seeded_lists_and_details_use_the_documented_shape(self):
        category = Category.objects.create(name="Fiction")
        publisher = Publisher.objects.create(
            name="Press", city="Paris", contact="press@example.com"
        )
        book = Book.objects.create(
            author="Ada",
            title="Guide",
            description="A short guide",
            quantity=3,
            category=category,
            publisher=publisher,
            floor_number=2,
            bookshelf_number="0008",
        )
        member = Member.objects.create(
            name="Pat", city="Paris", phone_number="0600000000", email="pat@example.com"
        )
        today = timezone.now().strftime("%Y/%m/%d")

        categories = self.client.get("/api/category-list/").json()
        self.assertEqual(categories[0]["name"], "Fiction")
        self.assertEqual(categories[0]["created_at"], today)

        detail = self.client.get(f"/api/category-detail/{category.pk}/")
        self.assertEqual(detail.status_code, 200)
        self.assertEqual(detail.json()["id"], category.pk)

        books = self.client.get("/api/book-list/").json()
        self.assertEqual(
            set(books[0]),
            {
                "id",
                "author",
                "title",
                "description",
                "quantity",
                "category",
                "publisher",
                "floor_number",
                "bookshelf_number",
                "created_at",
                "updated_at",
            },
        )
        self.assertEqual(books[0]["title"], "Guide")
        self.assertEqual(books[0]["created_at"], today)

        members = self.client.get("/api/members/").json()
        self.assertEqual(members[0]["name"], "Pat")
        self.assertEqual(members[0]["created_at"], today)
        self.assertNotIn("card_id", members[0])

        one = self.client.get(f"/api/members/{member.pk}")
        self.assertEqual(one.status_code, 200)
        self.assertEqual(one.json()["phone_number"], "0600000000")

        pubs = self.client.get("/api/publisher-list/").json()
        self.assertEqual(pubs[0]["name"], "Press")
        self.assertEqual(pubs[0]["created_at"], today)
        self.assertEqual(book.publisher_id, publisher.pk)

    def test_invalid_creates_are_400_and_do_not_insert(self):
        rejected = self.client.post(
            "/api/category-create/", {"name": "x" * 51}, format="json"
        )
        self.assertEqual(rejected.status_code, 400)
        self.assertIn("name", rejected.json())
        self.assertEqual(Category.objects.count(), 0)

        bad_email = self.client.post(
            "/api/publisher-create/",
            {"name": "Press", "city": "Paris", "contact": "not-an-email"},
            format="json",
        )
        self.assertEqual(bad_email.status_code, 400)
        self.assertEqual(Publisher.objects.count(), 0)

        book = self.client.post(
            "/api/book-create/", {"author": "Ada", "title": "Guide"}, format="json"
        )
        self.assertEqual(book.status_code, 400)
        self.assertEqual(Book.objects.count(), 0)

        member = self.client.post("/api/members/", {"name": "Pat"}, format="json")
        self.assertEqual(member.status_code, 400)
        self.assertEqual(Member.objects.count(), 0)

    def test_valid_create_update_and_missing_rows(self):
        created = self.client.post(
            "/api/book-create/",
            {
                "author": "Ada",
                "title": "Guide",
                "description": "A short guide",
                "quantity": 2,
            },
            format="json",
        )
        self.assertEqual(created.status_code, 200)
        book_id = created.json()["id"]
        self.assertEqual(Book.objects.get(pk=book_id).quantity, 2)

        updated = self.client.post(
            f"/api/book-update/{book_id}/",
            {
                "author": "Ada",
                "title": "Guide",
                "description": "Revised",
                "quantity": 9,
            },
            format="json",
        )
        self.assertEqual(updated.status_code, 200)
        self.assertEqual(Book.objects.get(pk=book_id).description, "Revised")

        invalid = self.client.post(
            f"/api/book-update/{book_id}/", {"title": "Only"}, format="json"
        )
        self.assertEqual(invalid.status_code, 400)
        self.assertEqual(Book.objects.get(pk=book_id).description, "Revised")

        self.assertEqual(self.client.get("/api/book-detail/999999/").status_code, 404)
        self.assertEqual(self.client.delete("/api/book-delete/999999/").status_code, 404)
        self.assertEqual(self.client.get("/api/category-detail/999999/").status_code, 404)
        self.assertEqual(self.client.get("/api/members/999999").status_code, 404)
        self.assertEqual(self.client.delete("/api/members/999999").status_code, 404)

        removed = self.client.delete(f"/api/book-delete/{book_id}/")
        self.assertEqual(removed.status_code, 200)
        self.assertFalse(Book.objects.filter(pk=book_id).exists())

    def test_anonymous_and_outsider_cannot_mutate(self):
        category = Category.objects.create(name="Fiction")
        anonymous = self.anonymous.post(
            "/api/category-create/", {"name": "Sneaky"}, format="json"
        )
        self.assertIn(anonymous.status_code, (401, 403))
        self.assertFalse(Category.objects.filter(name="Sneaky").exists())

        outsider = APIClient()
        outsider.force_login(
            User.objects.create_user(username="outsider", password="out-pass-1", is_staff=True)
        )
        denied = outsider.delete(f"/api/category-delete/{category.pk}/")
        self.assertEqual(denied.status_code, 403)
        self.assertTrue(Category.objects.filter(pk=category.pk).exists())
