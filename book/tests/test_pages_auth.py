"""Status and redirect checks for auth pages.

Login and register form markup is covered elsewhere and is not asserted here,
except the signup help text and field-error presentation.
"""

import re

from django.contrib.auth.models import User
from django.urls import reverse

from book.tests.page_utils import PageFixture


class AuthPageTests(PageFixture):
    def test_public_auth_pages_return_200(self):
        for name in ("login", "signup", "register"):
            with self.subTest(name=name):
                response = self.client.get(reverse(name))
                self.assertEqual(response.status_code, 200)
                self.assertContains(response, 'href="/" class="b-brand')
                self.assert_local_static_exists(response)

    def test_logged_in_user_can_still_open_login_and_register(self):
        self.login(self.reader)
        self.assertEqual(self.client.get(reverse("login")).status_code, 200)
        for name in ("signup", "register"):
            with self.subTest(name=name):
                response = self.client.get(reverse(name))
                self.assertRedirects(response, reverse("home"))

    def test_profile_requires_login_and_renders_for_the_user(self):
        self.assert_redirects_to_login(reverse("profile"))
        self.login(self.reader)
        page = self.client.get(reverse("profile"))
        self.assertEqual(page.status_code, 200)
        self.assertTemplateUsed(page, "profile/profile_detail.html")
        self.assertContains(page, "My profile")
        self.assertContains(page, self.reader.username)
        self.assertContains(page, "Not set")
        editor = self.client.get(reverse("profile_update", args=[self.reader.profile.pk]))
        self.assertContains(editor, "Update Profile")
        self.assertNotContains(editor, "Udpate")

    def test_signup_help_text_matches_aria_describedby(self):
        page = self.client.get(reverse("signup"))
        html = page.content.decode()
        self.assertContains(page, 'id="id_username_helptext"')
        self.assertContains(page, 'id="id_password1_helptext"')
        self.assertContains(page, 'id="id_password2_helptext"')
        self.assertContains(page, "at least 8 characters")
        self.assertContains(page, "entirely numeric")
        self.assertContains(page, "commonly used")
        self.assertContains(page, "personal information")
        ids = set(re.findall(r'\bid="([^"]+)"', html))
        described = re.findall(r'aria-describedby="([^"]*)"', html)
        self.assertTrue(described)
        for value in described:
            for ref in value.split():
                self.assertIn(ref, ids, ref)

    def test_failed_signup_renders_errors_with_the_error_class(self):
        User.objects.create_user(username="taken", password="library-pass-1")
        response = self.client.post(
            reverse("signup"),
            {
                "username": "taken",
                "email": "not-an-email",
                "first_name": "Ada",
                "last_name": "Lovelace",
                "password1": "short",
                "password2": "other",
            },
        )
        self.assertEqual(response.status_code, 200)
        html = response.content.decode()
        self.assertIn("text-error", html)
        self.assertIn("invalid-feedback", html)
        self.assertIn("d-block", html)
        self.assertIn("is-invalid", html)
        self.assertIn('id="id_username_error"', html)
        self.assertIn("A user with that username already exists.", html)
        self.assertIn("Enter a valid email address.", html)
        ids = set(re.findall(r'\bid="([^"]+)"', html))
        for value in re.findall(r'aria-describedby="([^"]*)"', html):
            for ref in value.split():
                self.assertIn(ref, ids, ref)

    def test_get_logout_does_not_end_the_session(self):
        self.login(self.reader)
        response = self.client.get(reverse("logout"))
        self.assertEqual(response.status_code, 405)
        self.assertEqual(self.client.get(reverse("profile")).status_code, 200)
