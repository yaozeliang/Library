"""GET coverage for library, admin, notification, and error routes."""

import os
from datetime import timedelta

from django.conf import settings
from django.contrib import admin
from django.contrib.auth.models import Permission, User
from django.test import RequestFactory, override_settings
from django.urls import reverse
from django.utils import timezone

from book.models import (
    Book,
    BorrowRecord,
    Category,
    Member,
    Publisher,
    UserActivity,
)
from book.tests.route_utils import RouteFixture
from book.views import TODAY, bad_request, page_not_found, permission_denied, server_error

# (url name, kwargs, template, heading, staff_status)
# staff_status 200 is a normal page, 403 is superuser or group gated, 405 is POST-only.
STAFF_PAGES = (
    ("home", {}, "index.html", "TOTAL BOOKS", 200),
    ("book_list", {}, "book/book_list.html", "Book Management", 200),
    ("book_create", {}, "book/book_create.html", "Add New Book", 200),
    ("category_list", {}, "book/category_list.html", "Category Management", 200),
    ("category_create", {}, "book/category_create.html", "Add New Category", 200),
    ("publisher_list", {}, "book/publisher_list.html", "Publisher Management", 200),
    ("publisher_create", {}, "book/publisher_create.html", "Add New Publisher", 200),
    ("member_list", {}, "book/member_list.html", "Membership Management", 200),
    ("member_create", {}, "book/member_create.html", "Add New Member", 200),
    ("record_list", {}, "borrow_records/list.html", "All Borrow Records", 200),
    ("record_create", {}, "borrow_records/create.html", "Add New Record", 200),
    ("chart", {}, "book/charts.html", "Charts", 200),
    ("profile_create", {}, "profile/profile_create.html", "Create Profile", 200),
    ("user_activity_list", {}, "book/user_activity_list.html", "User Activity", 403),
    ("data_center", {}, "book/download_data.html", "Download data", 403),
    ("employees_list", {}, "book/employees.html", "Employee Status", 403),
    ("notice_list", {}, "notice_list.html", "All Notifications", 403),
)

POST_ONLY = (
    "book_delete",
    "category_delete",
    "publisher_delete",
    "member_delete",
    "record_delete",
    "record_close",
    "user_activity_delete",
    "notice_update",
)


class LibraryPageTests(RouteFixture):
    def setUp(self):
        super().setUp()
        self.category = Category.objects.create(name="Fiction")
        self.publisher = Publisher.objects.create(
            name="Route Press", city="Paris", contact="press@example.com"
        )
        self.book = Book.objects.create(
            author="Ada",
            title="Route Guide",
            description="A short guide",
            quantity=4,
            category=self.category,
            publisher=self.publisher,
        )
        self.member = Member.objects.create(
            name="Pat Route", city="Paris", phone_number="0600000000"
        )
        self.record = BorrowRecord.objects.create(
            borrower=self.member.name,
            book=self.book.title,
            borrower_card=self.member.card_number,
            end_day=timezone.now() + timedelta(days=3),
        )
        self.activity = UserActivity.objects.create(
            created_by=self.staff.username,
            target_model="Book",
            detail="Create Book << Route Guide >>",
        )

    def _url(self, name, kwargs=None):
        return reverse(name, kwargs=kwargs or {})

    def test_anonymous_visitors_are_sent_to_login(self):
        protected = [name for name, *_rest in STAFF_PAGES]
        protected += list(POST_ONLY)
        protected += [
            "book_detail",
            "book_update",
            "publisher_update",
            "member_detail",
            "member_update",
            "profile_detail",
            "profile_update",
            "record_detail",
            "auto_member_name",
            "auto_book_name",
            "global_search",
            "employees_detail",
            "employee_update",
            "data_download",
        ]
        for name in protected:
            kwargs = {}
            if name == "data_download":
                kwargs = {"model_name": self.category._meta.db_table}
            elif name in {
                "book_detail",
                "book_update",
                "book_delete",
            }:
                kwargs = {"pk": self.book.pk}
            elif name in {"publisher_update", "publisher_delete"}:
                kwargs = {"pk": self.publisher.pk}
            elif name in {"member_detail", "member_update", "member_delete"}:
                kwargs = {"pk": self.member.pk}
            elif name in {"category_delete"}:
                kwargs = {"pk": self.category.pk}
            elif name in {"record_detail", "record_delete", "record_close"}:
                kwargs = {"pk": self.record.pk}
            elif name in {"profile_detail", "profile_update"}:
                kwargs = {"pk": self.staff.profile.pk}
            elif name in {"employees_detail", "employee_update"}:
                kwargs = {"pk": self.staff.pk}
            elif name == "user_activity_delete":
                kwargs = {"pk": self.activity.pk}
            with self.subTest(name=name):
                self.assert_redirects_to_login(self._url(name, kwargs))

    def test_staff_and_superuser_pages_render(self):
        self.login(self.staff)
        for name, kwargs, template, heading, staff_status in STAFF_PAGES:
            with self.subTest(user="staff", name=name):
                response = self.client.get(self._url(name, kwargs))
                self.assertEqual(response.status_code, staff_status, name)
                if staff_status == 200:
                    self.assertTemplateUsed(response, template)
                    self.assertContains(response, heading)
                    self.assertContains(response, "csrfmiddlewaretoken")

        self.login(self.superuser)
        for name, kwargs, template, heading, _staff_status in STAFF_PAGES:
            with self.subTest(user="superuser", name=name):
                response = self.client.get(self._url(name, kwargs))
                self.assertEqual(response.status_code, 200, name)
                self.assertTemplateUsed(response, template)
                self.assertContains(response, heading)

    def test_detail_and_edit_pages_and_missing_ids(self):
        pages = (
            ("book_detail", self.book.pk, "book/book_detail.html", "Route Guide"),
            ("book_update", self.book.pk, "book/book_update.html", "Modify Book"),
            (
                "publisher_update",
                self.publisher.pk,
                "book/publisher_update.html",
                "Update Publisher",
            ),
            (
                "member_detail",
                self.member.pk,
                "book/member_detail.html",
                "Pat Route",
            ),
            (
                "member_update",
                self.member.pk,
                "book/member_update.html",
                "Modify Member",
            ),
            (
                "record_detail",
                self.record.pk,
                "borrow_records/detail.html",
                "Pat Route",
            ),
            (
                "profile_detail",
                self.staff.profile.pk,
                "profile/profile_detail.html",
                "My profile",
            ),
            (
                "profile_update",
                self.staff.profile.pk,
                "profile/profile_update.html",
                "Update Profile",
            ),
        )
        self.login(self.staff)
        for name, pk, template, heading in pages:
            with self.subTest(name=name):
                response = self.client.get(reverse(name, args=[pk]))
                self.assertEqual(response.status_code, 200)
                self.assertTemplateUsed(response, template)
                self.assertContains(response, heading)
                missing = self.client.get(reverse(name, args=[999999]))
                self.assertEqual(missing.status_code, 404)

        self.login(self.superuser)
        employee = self.client.get(reverse("employees_detail", args=[self.staff.pk]))
        self.assertEqual(employee.status_code, 200)
        self.assertTemplateUsed(employee, "book/employee_detail.html")
        self.assertContains(employee, self.staff.username)
        self.assertContains(employee, ">Update</button>")
        self.assertEqual(
            self.client.get(reverse("employees_detail", args=[999999])).status_code,
            404,
        )
        update = self.client.get(reverse("employee_update", args=[self.staff.pk]))
        self.assertEqual(update.status_code, 200)
        self.assertEqual(
            self.client.get(reverse("employee_update", args=[999999])).status_code,
            404,
        )

    def test_staff_cannot_open_another_users_profile_editor(self):
        self.login(self.staff)
        response = self.client.get(
            reverse("profile_update", args=[self.reader.profile.pk])
        )
        self.assertEqual(response.status_code, 404)

    def test_staff_is_blocked_from_superuser_and_group_routes(self):
        self.login(self.staff)
        blocked = [
            reverse("employees_list"),
            reverse("employees_detail", args=[self.staff.pk]),
            reverse("employee_update", args=[self.staff.pk]),
            reverse("notice_list"),
            reverse("notice_update"),
            reverse("user_activity_list"),
            reverse("user_activity_delete", args=[self.activity.pk]),
            reverse("data_center"),
            reverse("data_download", args=[self.category._meta.db_table]),
        ]
        for url in blocked:
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 403)

    def test_post_only_gets_are_method_not_allowed_for_superuser(self):
        self.login(self.superuser)
        targets = {
            "book_delete": self.book.pk,
            "category_delete": self.category.pk,
            "publisher_delete": self.publisher.pk,
            "member_delete": self.member.pk,
            "record_delete": self.record.pk,
            "record_close": self.record.pk,
            "user_activity_delete": self.activity.pk,
        }
        for name, pk in targets.items():
            response = self.client.get(reverse(name, args=[pk]))
            self.assertEqual(response.status_code, 405, name)
            self.assertTrue(Book.objects.filter(pk=self.book.pk).exists())
        self.assertEqual(self.client.get(reverse("notice_update")).status_code, 405)

    def test_empty_dashboard_and_charts_do_not_break(self):
        Book.objects.all().delete()
        Member.objects.all().delete()
        Category.objects.all().delete()
        Publisher.objects.all().delete()
        BorrowRecord.objects.all().delete()
        self.login(self.staff)

        home = self.client.get(reverse("home"))
        self.assertEqual(home.status_code, 200)
        self.assertContains(home, '<h3 class="f-w-300">0</h3>', count=4)
        self.assertNotContains(home, ">None<")

        charts = self.client.get(reverse("chart"))
        self.assertEqual(charts.status_code, 200)
        self.assertContains(charts, "No books in stock yet.")
        self.assertContains(charts, "No borrow history yet.")
        self.assertContains(charts, "No borrow records yet.")
        self.assertContains(charts, "No members yet.")

    def test_borrow_detail_shows_on_time_and_survives_a_missing_member(self):
        self.login(self.staff)
        page = self.client.get(reverse("record_detail", args=[self.record.pk]))
        self.assertContains(page, "On Time")
        self.assertNotContains(page, "delayed")

        orphan = BorrowRecord.objects.create(
            borrower="Nobody Home",
            book=self.book.title,
            end_day=timezone.now() + timedelta(days=2),
        )
        orphan_page = self.client.get(reverse("record_detail", args=[orphan.pk]))
        self.assertEqual(orphan_page.status_code, 200)
        self.assertContains(orphan_page, "Nobody Home")

    def test_search_filter_and_pagination(self):
        for index in range(6):
            Book.objects.create(
                author="Pager",
                title=f"Paged Book {index}",
                description="page",
                quantity=1,
            )
        Book.objects.create(
            author="Ada",
            title="Two Words Guide",
            description="spaces",
            quantity=1,
        )
        self.login(self.staff)

        found = self.client.get(reverse("book_list"), {"search": "Two Words"})
        self.assertEqual(found.status_code, 200)
        self.assertContains(found, "Two Words Guide")
        self.assertContains(found, 'value="Two Words"')
        self.assertNotContains(found, "Paged Book 0")

        ordered = self.client.get(
            reverse("book_list"), {"orderby": "title", "search": "Paged"}
        )
        self.assertEqual(ordered.status_code, 200)
        self.assertContains(ordered, "Paged Book 0")

        bogus = self.client.get(reverse("book_list"), {"orderby": "not_a_field"})
        self.assertEqual(bogus.status_code, 200)
        self.assertContains(bogus, "Two Words Guide")

        for page in ("2", "999", "0", "nope"):
            response = self.client.get(reverse("book_list"), {"page": page})
            self.assertEqual(response.status_code, 200, page)

        last = self.client.get(reverse("book_list"), {"page": 1})
        self.assertContains(last, "orderby=-updated_at")

        self.login(self.superuser)
        logs = self.client.get(
            reverse("user_activity_list"),
            {"search": "Book", "created_by": self.staff.username, "page": "999"},
        )
        self.assertEqual(logs.status_code, 200)
        self.assertContains(logs, "Route Guide")
        self.assertContains(logs, 'value="Book"')

        members = self.client.get(
            reverse("member_list"), {"search": "Pat", "orderby": "name", "page": "5"}
        )
        self.assertEqual(members.status_code, 200)
        self.assertContains(members, "Pat Route")
        self.assertContains(members, 'value="Pat"')

        categories = self.client.get(
            reverse("category_list"), {"search": "Fic", "orderby": "nope"}
        )
        self.assertEqual(categories.status_code, 200)
        self.assertContains(categories, "Fiction")

        publishers = self.client.get(
            reverse("publisher_list"), {"search": "Route", "page": "nope"}
        )
        self.assertEqual(publishers.status_code, 200)
        self.assertContains(publishers, "Route Press")

        records = self.client.get(
            reverse("record_list"), {"search": "Pat", "orderby": "borrower"}
        )
        self.assertEqual(records.status_code, 200)
        self.assertContains(records, "Pat Route")

    def test_autocomplete_and_global_search(self):
        self.login(self.staff)
        members = self.client.get(reverse("auto_member_name"), {"term": "Pat"})
        books = self.client.get(reverse("auto_book_name"), {"term": ""})
        self.assertEqual(members.status_code, 200)
        self.assertEqual(books.status_code, 200)
        self.assertEqual(members["Content-Type"], "application/json")
        self.assertEqual(members.json(), ["Pat Route"])
        self.assertIn("Route Guide", books.json())

        empty = self.client.get(reverse("auto_member_name"), {"term": "zzzz-none"})
        self.assertEqual(empty.json(), [])

        home = self.client.get(reverse("global_search"))
        self.assertRedirects(home, reverse("home"))
        blank = self.client.post(reverse("global_search"), {"global_search": "  "})
        self.assertEqual(blank.status_code, 200)
        self.assertContains(blank, "Search Result")

        found = self.client.post(reverse("global_search"), {"global_search": "Route"})
        self.assertEqual(found.status_code, 200)
        self.assertTemplateUsed(found, "book/global_search.html")
        self.assertContains(found, "Search Result")
        self.assertContains(found, "Route Press")
        self.assertContains(found, "Pat Route")
        self.assertContains(found, "Route Guide")

    def test_empty_and_unknown_downloads(self):
        self.login(self.superuser)
        center = self.client.get(reverse("data_center"))
        self.assertEqual(center.status_code, 200)
        self.assertContains(center, self.category._meta.db_table)

        unknown = self.client.get(reverse("data_download", args=["not-a-dataset"]))
        self.assertEqual(unknown.status_code, 404)

        table = UserActivity._meta.db_table
        path = os.path.join(settings.BASE_DIR, "datacenter", f"UserActivity_{TODAY}.csv")
        UserActivity.objects.all().delete()
        existed = os.path.exists(path)
        try:
            download = self.client.get(reverse("data_download", args=[table]))
            self.assertEqual(download.status_code, 200)
            self.assertIn("text/csv", download["Content-Type"])
            self.assertIn(b"attachment", download["Content-Disposition"].encode())
        finally:
            if not existed and os.path.exists(path):
                os.remove(path)


class NotificationRouteTests(RouteFixture):
    def test_inbox_and_json_endpoints(self):
        all_url = reverse("notifications:all")
        unread = reverse("notifications:unread")
        self.assert_redirects_to_login(all_url)
        self.assert_redirects_to_login(reverse("notifications:mark_all_as_read"))

        self.login(self.staff)
        page = self.client.get(all_url)
        self.assertEqual(page.status_code, 200)
        self.assertEqual(self.client.get(unread).status_code, 200)
        self.assertEqual(
            self.client.get(unread, {"page": "999"}).status_code in (200, 404),
            True,
        )
        marked = self.client.get(reverse("notifications:mark_all_as_read"))
        self.assertEqual(marked.status_code, 302)

        missing = "999999"
        for name in ("mark_as_read", "mark_as_unread", "delete"):
            response = self.client.get(reverse(f"notifications:{name}", args=[missing]))
            self.assertEqual(response.status_code, 404, name)

        self.client.logout()
        for name, key in (
            ("live_unread_notification_count", "unread_count"),
            ("live_all_notification_count", "all_count"),
            ("live_unread_notification_list", "unread_list"),
            ("live_all_notification_list", "all_list"),
        ):
            response = self.client.get(reverse(f"notifications:{name}"))
            self.assertEqual(response.status_code, 200, name)
            self.assertIn("application/json", response["Content-Type"])
            payload = response.json()
            self.assertIn(key, payload)
            if key.endswith("list"):
                self.assertEqual(payload[key], [])

        self.login(self.superuser)
        count = self.client.get(reverse("notifications:live_unread_notification_count"))
        self.assertEqual(count.status_code, 200)
        self.assertEqual(count.json()["unread_count"], 0)


class AdminRouteTests(RouteFixture):
    def test_admin_login_and_index_permissions(self):
        index = reverse("admin:index")
        login = reverse("admin:login")
        anonymous = self.client.get(index)
        self.assertEqual(anonymous.status_code, 302)
        self.assertIn("/admin/login/", anonymous.url)
        self.assertEqual(self.client.get(login).status_code, 200)

        self.login(self.reader)
        reader = self.client.get(index)
        self.assertEqual(reader.status_code, 302)
        self.assertIn("/admin/login/", reader.url)

        for user in (self.staff, self.superuser):
            self.login(user)
            page = self.client.get(index)
            self.assertEqual(page.status_code, 200, user.username)
            self.assertContains(page, "Site administration")

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
        # is_staff alone does not grant model permissions.
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


class ErrorHandlerTests(RouteFixture):
    @override_settings(DEBUG=False, ALLOWED_HOSTS=["*"])
    def test_unknown_path_uses_the_404_template(self):
        response = self.client.get("/this-route-does-not-exist/")
        self.assertEqual(response.status_code, 404)
        self.assertContains(response, "Error 404", status_code=404)

    def test_handler_views_set_status_and_heading(self):
        request = RequestFactory().get("/")
        cases = (
            (bad_request, 400, "Error 400"),
            (permission_denied, 403, "Error 403"),
            (page_not_found, 404, "Error 404"),
            (server_error, 500, "Error 500"),
        )
        for view, status, heading in cases:
            if view is page_not_found:
                response = view(request, Exception("missing"))
            else:
                response = view(request)
            self.assertEqual(response.status_code, status)
            self.assertContains(response, heading, status_code=status)
