"""GET coverage for Django admin pages."""

from django.contrib import admin
from django.contrib.auth.models import Permission, User
from django.urls import reverse

from book.models import Category
from book.tests.page_utils import PageFixture


class AdminPageTests(PageFixture):
    def test_admin_login_and_index_permissions(self):
        index = reverse("admin:index")
        login = reverse("admin:login")
        anonymous = self.client.get(index)
        self.assertEqual(anonymous.status_code, 302)
        self.assertIn("/admin/login/", anonymous.url)
        self.assertEqual(self.client.get(login).status_code, 200)
        self.assertContains(self.client.get(login), "Django administration")

        self.login(self.reader)
        reader = self.client.get(index)
        self.assertEqual(reader.status_code, 302)
        self.assertIn("/admin/login/", reader.url)

        for user in (self.staff, self.superuser):
            self.login(user)
            page = self.client.get(index)
            self.assertEqual(page.status_code, 200, user.username)
            self.assertContains(page, "Site administration")
            self.assert_local_static_exists(page)

    def test_each_registered_model_changelist_and_change_page(self):
        self.login(self.superuser)
        Category.objects.create(name="Admin Fiction")
        for model, _model_admin in admin.site._registry.items():
            opts = model._meta
            changelist = reverse(f"admin:{opts.app_label}_{opts.model_name}_changelist")
            with self.subTest(model=opts.label):
                listed = self.client.get(changelist)
                self.assertEqual(listed.status_code, 200, opts.label)
                add_url = reverse(f"admin:{opts.app_label}_{opts.model_name}_add")
                added = self.client.get(add_url)
                self.assertIn(added.status_code, (200, 403), opts.label)
                obj = model.objects.order_by("pk").first()
                if obj is not None:
                    change = self.client.get(
                        reverse(
                            f"admin:{opts.app_label}_{opts.model_name}_change",
                            args=[obj.pk],
                        )
                    )
                    self.assertEqual(change.status_code, 200, opts.label)
                missing = self.client.get(
                    reverse(
                        f"admin:{opts.app_label}_{opts.model_name}_change",
                        args=[999999],
                    )
                )
                self.assertIn(missing.status_code, (302, 404), opts.label)

        book_list = reverse("admin:book_book_changelist")
        self.login(self.staff)
        self.assertEqual(self.client.get(book_list).status_code, 403)
        view_book = Permission.objects.get(
            codename="view_book", content_type__app_label="book"
        )
        self.staff.user_permissions.add(view_book)
        self.staff = User.objects.get(pk=self.staff.pk)
        self.login(self.staff)
        self.assertEqual(self.client.get(book_list).status_code, 200)

        self.login(self.reader)
        self.assertEqual(self.client.get(book_list).status_code, 302)
