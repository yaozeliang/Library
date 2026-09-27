"""GET page coverage for comments."""

from django.urls import reverse

from book.models import Book, Category
from book.tests.page_utils import PageFixture
from comment.models import Comment


class CommentPageTests(PageFixture):
    def setUp(self):
        super().setUp()
        self.category = Category.objects.create(name="Essays")
        self.book = Book.objects.create(
            author="Ada",
            title="Comment Guide",
            description="notes",
            quantity=1,
            category=self.category,
        )
        self.comment = Comment.objects.create(
            book=self.book,
            user=self.staff,
            body="A public note",
        )

    def test_list_is_public(self):
        page = self.client.get(reverse("comment:comment_list"))
        self.assertEqual(page.status_code, 200)
        self.assertTemplateUsed(page, "comment/comment_list.html")
        self.assertContains(page, "Comments")
        self.assertContains(page, "A public note")
        self.assertContains(page, ">Login<")
        self.assertNotContains(page, "Lend Book")
        self.assertNotContains(page, "Create Profile")
        self.assertNotContains(page, 'name="global_search"')
        self.assert_local_static_exists(page)

        self.login(self.superuser)
        again = self.client.get(reverse("comment:comment_list"))
        self.assertEqual(again.status_code, 200)
        self.assertContains(again, "Comments")
        self.assertContains(again, "Lend Book")
        self.assertContains(again, 'name="global_search"')

    def test_create_detail_edit_and_delete_pages(self):
        create = reverse("comment:comment_create")
        detail = reverse("comment:comment_detail", args=[self.comment.pk])
        edit = reverse("comment:comment_update", args=[self.comment.pk])
        delete = reverse("comment:comment_delete", args=[self.comment.pk])
        post = reverse("comment:post_comment", args=[self.book.pk])

        for url in (create, detail, edit, delete, post):
            with self.subTest(url=url):
                self.assert_redirects_to_login(url)

        self.login(self.staff)
        created = self.client.get(create)
        self.assertEqual(created.status_code, 200)
        self.assertTemplateUsed(created, "comment/comment_form.html")
        self.assertContains(created, "Comment")
        self.assertContains(created, 'placeholder="Comment"')
        self.assertContains(created, 'aria-label="Comment"')
        self.assertContains(created, "form-control")

        shown = self.client.get(detail)
        self.assertEqual(shown.status_code, 200)
        self.assertTemplateUsed(shown, "comment/comment_detail.html")
        self.assertContains(shown, "Comment by page-staff")

        edited = self.client.get(edit)
        self.assertEqual(edited.status_code, 200)
        self.assertTemplateUsed(edited, "comment/comment_form.html")
        self.assertContains(edited, "Comment")
        self.assertContains(edited, 'placeholder="Comment"')
        self.assertContains(edited, 'aria-label="Comment"')

        confirm = self.client.get(delete)
        self.assertEqual(confirm.status_code, 200)
        self.assertTemplateUsed(confirm, "comment/comment_confirm_delete.html")
        self.assertContains(confirm, "Delete this comment?")

        for name in ("comment_detail", "comment_update", "comment_delete"):
            missing = self.client.get(reverse(f"comment:{name}", args=[999999]))
            self.assertEqual(missing.status_code, 404, name)

        text = self.client.get(post)
        self.assertEqual(text.status_code, 200)
        self.assertContains(text, "Comment only accepts POST requests")
        missing_book = self.client.get(reverse("comment:post_comment", args=[999999]))
        self.assertEqual(missing_book.status_code, 404)

    def test_other_users_cannot_open_edit_or_delete(self):
        self.login(self.reader)
        edit = self.client.get(reverse("comment:comment_update", args=[self.comment.pk]))
        delete = self.client.get(
            reverse("comment:comment_delete", args=[self.comment.pk])
        )
        self.assertEqual(edit.status_code, 404)
        self.assertEqual(delete.status_code, 404)
        detail = self.client.get(reverse("comment:comment_detail", args=[self.comment.pk]))
        self.assertEqual(detail.status_code, 200)
