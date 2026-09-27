"""Comment routes: public list, owner-only edits, and book comments."""

from django.urls import reverse

from book.models import Book
from book.tests.route_utils import RouteFixture
from comment.models import Comment


class CommentRouteTests(RouteFixture):
    def setUp(self):
        super().setUp()
        self.book = Book.objects.create(
            author="Ada", title="Commented Book", description="Notes"
        )
        self.comment = Comment.objects.create(
            book=self.book, user=self.staff, body="Shelf note"
        )

    def test_list_is_public_and_out_of_range_pages_do_not_404(self):
        anonymous = self.client.get(reverse("comment:comment_list"))
        self.assertEqual(anonymous.status_code, 200)
        self.assertTemplateUsed(anonymous, "comment/comment_list.html")
        self.assertContains(anonymous, "Comments")
        self.assertContains(anonymous, "Shelf note")

        for page in ("999", "0", "nope"):
            response = self.client.get(reverse("comment:comment_list"), {"page": page})
            self.assertEqual(response.status_code, 200, page)
            self.assertContains(response, "Comments")

    def test_create_requires_login_and_valid_post_redirects(self):
        url = reverse("comment:comment_create")
        self.assert_redirects_to_login(url)

        self.login(self.staff)
        page = self.client.get(url)
        self.assertEqual(page.status_code, 200)
        self.assertTemplateUsed(page, "comment/comment_form.html")
        self.assertContains(page, "csrfmiddlewaretoken")

        created = self.client.post(url, {"body": "A new comment"})
        self.assertRedirects(created, reverse("comment:comment_list"))
        self.assertTrue(
            Comment.objects.filter(user=self.staff, body="A new comment").exists()
        )

    def test_detail_edit_and_delete_for_owner_and_missing_ids(self):
        detail = reverse("comment:comment_detail", args=[self.comment.pk])
        edit = reverse("comment:comment_update", args=[self.comment.pk])
        delete = reverse("comment:comment_delete", args=[self.comment.pk])

        self.assert_redirects_to_login(detail)
        self.login(self.staff)

        page = self.client.get(detail)
        self.assertEqual(page.status_code, 200)
        self.assertTemplateUsed(page, "comment/comment_detail.html")
        self.assertContains(page, "Comment by")
        self.assertContains(page, "Shelf note")

        form = self.client.get(edit)
        self.assertEqual(form.status_code, 200)
        self.assertContains(form, "Comment")

        updated = self.client.post(edit, {"body": "Revised note"})
        self.assertRedirects(updated, reverse("comment:comment_list"))
        self.comment.refresh_from_db()
        self.assertEqual(self.comment.body, "Revised note")

        confirm = self.client.get(delete)
        self.assertEqual(confirm.status_code, 200)
        self.assertTemplateUsed(confirm, "comment/comment_confirm_delete.html")
        self.assertContains(confirm, "Delete this comment?")

        removed = self.client.post(delete)
        self.assertRedirects(removed, reverse("comment:comment_list"))
        self.assertFalse(Comment.objects.filter(pk=self.comment.pk).exists())

        for name in ("comment_detail", "comment_update", "comment_delete"):
            missing = self.client.get(reverse(f"comment:{name}", args=[999999]))
            self.assertEqual(missing.status_code, 404, name)

    def test_other_users_cannot_edit_or_delete(self):
        self.login(self.superuser)
        edit = reverse("comment:comment_update", args=[self.comment.pk])
        delete = reverse("comment:comment_delete", args=[self.comment.pk])
        self.assertEqual(self.client.get(edit).status_code, 404)
        self.assertEqual(self.client.post(delete).status_code, 404)
        self.assertTrue(Comment.objects.filter(pk=self.comment.pk).exists())

    def test_post_comment_on_a_book(self):
        url = reverse("comment:post_comment", args=[self.book.pk])
        self.assert_redirects_to_login(url)

        self.login(self.reader)
        rejected = self.client.get(url)
        self.assertEqual(rejected.status_code, 200)
        self.assertContains(rejected, "Comment only accepts POST requests")

        posted = self.client.post(url, {"body": "From the book page"})
        self.assertRedirects(posted, reverse("book_detail", args=[self.book.pk]))
        self.assertTrue(
            Comment.objects.filter(user=self.reader, body="From the book page").exists()
        )

        missing = self.client.post(
            reverse("comment:post_comment", args=[999999]), {"body": "Nope"}
        )
        self.assertEqual(missing.status_code, 404)
