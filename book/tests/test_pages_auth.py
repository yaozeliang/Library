"""Status and redirect checks for auth pages.

Login and register form markup is covered elsewhere and is not asserted here.
"""

from django.urls import reverse

from book.tests.page_utils import PageFixture


class AuthPageTests(PageFixture):
    def test_public_auth_pages_return_200(self):
        for name in ("login", "signup", "register"):
            with self.subTest(name=name):
                response = self.client.get(reverse(name))
                self.assertEqual(response.status_code, 200)
                self.assert_local_static_exists(response)

    def test_logged_in_user_can_still_open_login_and_register(self):
        self.login(self.reader)
        for name in ("login", "signup", "register"):
            with self.subTest(name=name):
                self.assertEqual(self.client.get(reverse(name)).status_code, 200)

    def test_profile_requires_login_and_renders_for_the_user(self):
        self.assert_redirects_to_login(reverse("profile"))
        self.login(self.reader)
        page = self.client.get(reverse("profile"))
        self.assertEqual(page.status_code, 200)
        self.assertTemplateUsed(page, "profile/profile_detail.html")
        self.assertContains(page, "My profile")
        self.assertContains(page, self.reader.username)

    def test_get_logout_does_not_end_the_session(self):
        self.login(self.reader)
        response = self.client.get(reverse("logout"))
        self.assertEqual(response.status_code, 405)
        self.assertEqual(self.client.get(reverse("profile")).status_code, 200)
