"""GET page coverage for library screens and the notification inbox."""

from datetime import timedelta

from django.urls import reverse
from django.utils import timezone

from book.models import Book, BorrowRecord, Category, Member, Publisher, UserActivity
from book.tests.page_utils import PageFixture

# (url name, kwargs, template, heading, staff_status)
# 403 means the page is limited to a superuser or a permission group.
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


class LibraryPageTests(PageFixture):
    def setUp(self):
        super().setUp()
        self.category = Category.objects.create(name="Fiction")
        self.publisher = Publisher.objects.create(
            name="Page Press", city="Paris", contact="press@example.com"
        )
        self.book = Book.objects.create(
            author="Ada",
            title="Page Guide",
            description="A short guide",
            quantity=4,
            category=self.category,
            publisher=self.publisher,
        )
        self.member = Member.objects.create(
            name="Pat Page", city="Paris", phone_number="0600000000"
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
            detail="Create Book << Page Guide >>",
        )

    def _url(self, name, kwargs=None):
        return reverse(name, kwargs=kwargs or {})

    def _protected_urls(self):
        names = [name for name, *_rest in STAFF_PAGES]
        names += list(POST_ONLY)
        names += [
            "book_detail",
            "book_update",
            "publisher_update",
            "member_detail",
            "member_update",
            "profile_detail",
            "profile_update",
            "record_detail",
            "global_search",
            "employees_detail",
            "employee_update",
            "data_download",
        ]
        urls = []
        for name in names:
            kwargs = {}
            if name == "data_download":
                kwargs = {"model_name": self.category._meta.db_table}
            elif name in {"book_detail", "book_update", "book_delete"}:
                kwargs = {"pk": self.book.pk}
            elif name in {"publisher_update", "publisher_delete"}:
                kwargs = {"pk": self.publisher.pk}
            elif name in {"member_detail", "member_update", "member_delete"}:
                kwargs = {"pk": self.member.pk}
            elif name == "category_delete":
                kwargs = {"pk": self.category.pk}
            elif name in {"record_detail", "record_delete", "record_close"}:
                kwargs = {"pk": self.record.pk}
            elif name in {"profile_detail", "profile_update"}:
                kwargs = {"pk": self.staff.profile.pk}
            elif name in {"employees_detail", "employee_update"}:
                kwargs = {"pk": self.staff.pk}
            elif name == "user_activity_delete":
                kwargs = {"pk": self.activity.pk}
            urls.append(self._url(name, kwargs))
        return urls

    def test_anonymous_visitors_are_sent_to_login(self):
        for url in self._protected_urls():
            with self.subTest(url=url):
                self.assert_redirects_to_login(url)

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
                    self.assert_local_static_exists(response)

        self.login(self.superuser)
        for name, kwargs, template, heading, _staff_status in STAFF_PAGES:
            with self.subTest(user="superuser", name=name):
                response = self.client.get(self._url(name, kwargs))
                self.assertEqual(response.status_code, 200, name)
                self.assertTemplateUsed(response, template)
                self.assertContains(response, heading)
                self.assert_local_static_exists(response)

    def test_chart_page_includes_plot_containers_and_highcharts(self):
        self.login(self.staff)
        page = self.client.get(reverse("chart"))
        self.assertEqual(page.status_code, 200)
        self.assertContains(page, 'id="book-count"')
        self.assertContains(page, 'id="top-borrow"')
        self.assertContains(page, 'id="record-status"')
        self.assertContains(page, "highcharts.js")
        self.assertContains(page, 'id="chart-top-5-titles"')

        Book.objects.all().delete()
        Member.objects.all().delete()
        BorrowRecord.objects.all().delete()
        empty = self.client.get(reverse("chart"))
        self.assertEqual(empty.status_code, 200)
        self.assertContains(empty, "No books in stock yet.")
        self.assertContains(empty, "No borrow history yet.")
        self.assertContains(empty, "No borrow records yet.")
        self.assertContains(empty, "No members yet.")

    def test_detail_and_edit_pages_and_missing_ids(self):
        pages = (
            ("book_detail", self.book.pk, "book/book_detail.html", "Page Guide"),
            ("book_update", self.book.pk, "book/book_update.html", "Modify Book"),
            (
                "publisher_update",
                self.publisher.pk,
                "book/publisher_update.html",
                "Update Publisher",
            ),
            ("member_detail", self.member.pk, "book/member_detail.html", "Pat Page"),
            ("member_update", self.member.pk, "book/member_update.html", "Modify Member"),
            (
                "record_detail",
                self.record.pk,
                "borrow_records/detail.html",
                "Pat Page",
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
                self.assert_local_static_exists(response)
                missing = self.client.get(reverse(name, args=[999999]))
                self.assertEqual(missing.status_code, 404)

        detail = self.client.get(reverse("record_detail", args=[self.record.pk]))
        self.assertContains(detail, "On Time")

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
        self.assertTemplateUsed(update, "book/employee_detail.html")
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
            reverse("user_activity_list"),
            reverse("user_activity_delete", args=[self.activity.pk]),
            reverse("data_center"),
            reverse("data_download", args=[self.category._meta.db_table]),
        ]
        for url in blocked:
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 403)

    def test_get_on_post_only_routes_is_method_not_allowed(self):
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
        self.assertEqual(self.client.get(reverse("notice_update")).status_code, 405)

    def test_global_search_get_returns_home(self):
        self.login(self.staff)
        response = self.client.get(reverse("global_search"))
        self.assertRedirects(response, reverse("home"))

    def test_brand_pagination_labels_and_chart_layout(self):
        self.login(self.staff)
        home = self.client.get(reverse("home"))
        self.assertContains(home, 'href="/" class="b-brand"')
        self.assertContains(home, "Open Library")

        books = self.client.get(reverse("book_list"))
        for label in ("First", "Previous", "Next", "Last"):
            self.assertContains(books, f">{label}<")
        self.assertNotContains(books, ">End<")

        category = self.client.get(reverse("category_create"))
        self.assertContains(category, 'placeholder="Name"')
        self.assertContains(category, 'aria-label="Name"')
        self.assertContains(category, 'class="form-control"')

        record = self.client.get(reverse("record_create"))
        self.assertContains(record, 'placeholder="Book title"')
        self.assertContains(record, 'aria-label="Book title"')
        self.assertContains(record, "form-control")

        charts = self.client.get(reverse("chart"))
        self.assertContains(charts, "min-height: 360px")
        self.assertContains(charts, "maxWidth: 480")
        self.assertContains(charts, "dataLabels: { enabled: false }")
        self.assertContains(charts, "minSize: 160")
        self.assertContains(charts, 'type: "bar"')

        self.assertContains(home, 'id="myTab"')
        self.assertContains(home, "recent-events")
        self.assertContains(home, "table-fit")
        self.assertNotContains(home, "Udpate Profile")

        records = self.client.get(reverse("record_list"))
        self.assertContains(records, "table-fit")
        self.assertContains(records, "d-none d-lg-table-cell")
        self.assertContains(records, "col-actions")
        self.assertNotContains(records, 'href="/record-list/ "')

        members = self.client.get(reverse("member_list"))
        self.assertContains(members, "table-fit")
        books = self.client.get(reverse("book_list"))
        self.assertContains(books, "table-fit")

        created = self.client.get(reverse("book_create"))
        self.assertNotContains(created, "tailwind")
        self.assertContains(created, "btn btn-primary")
        publisher = self.client.get(reverse("publisher_create"))
        self.assertNotContains(publisher, "tailwind")
        self.assertContains(publisher, "btn btn-primary")

        detail = self.client.get(reverse("book_detail", args=[self.book.pk]))
        self.assertContains(detail, "exportpdf")


class NotificationPageTests(PageFixture):
    def test_inbox_pages_require_login_and_missing_slugs_are_404(self):
        all_url = reverse("notifications:all")
        unread = reverse("notifications:unread")
        self.assert_redirects_to_login(all_url)
        self.assert_redirects_to_login(unread)
        self.assert_redirects_to_login(reverse("notifications:mark_all_as_read"))

        self.login(self.staff)
        empty = self.client.get(all_url)
        self.assertEqual(empty.status_code, 200)
        self.assertContains(empty, "Notifications")
        self.assertContains(empty, "No notifications yet.")
        self.assertContains(empty, 'class="notifications"')
        self.assertTemplateUsed(empty, "notifications/list.html")

        from notifications.signals import notify

        notify.send(self.superuser, recipient=self.staff, verb="lent a book")
        page = self.client.get(all_url)
        self.assertContains(page, "lent a book")
        self.assertContains(page, "page-root")
        self.assertContains(page, "notification-unread")
        self.assertContains(page, "Mark as read")
        self.assertContains(page, "Mark all as read")
        unread_page = self.client.get(unread)
        self.assertEqual(unread_page.status_code, 200)
        self.assertContains(unread_page, "Unread notifications")
        self.assertContains(unread_page, "lent a book")

        marked = self.client.get(reverse("notifications:mark_all_as_read"))
        self.assertEqual(marked.status_code, 302)

        for name in ("mark_as_read", "mark_as_unread", "delete"):
            response = self.client.get(
                reverse(f"notifications:{name}", args=["999999"])
            )
            self.assertEqual(response.status_code, 404, name)

        self.login(self.superuser)
        self.assertEqual(self.client.get(all_url).status_code, 200)
        self.assertEqual(self.client.get(unread).status_code, 200)


class ErrorPageTests(PageFixture):
    def test_unknown_path_uses_the_404_template(self):
        from django.test import override_settings

        with override_settings(DEBUG=False, ALLOWED_HOSTS=["*"]):
            response = self.client.get("/this-route-does-not-exist/")
        self.assertEqual(response.status_code, 404)
        self.assertContains(response, "Error 404", status_code=404)

    def test_handler_views_set_status_and_heading(self):
        from django.test import RequestFactory

        from book.views import bad_request, page_not_found, permission_denied, server_error

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
