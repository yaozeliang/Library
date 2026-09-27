"""Auth page tests for login and registration forms."""

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from authentication.forms import CustomUserCreationForm, LoginForm, SignUpForm


REGISTER_PLACEHOLDERS = (
    "Username",
    "Email",
    "First name",
    "Last name",
    "Password",
    "Confirm password",
)


class AuthPlaceholderTests(TestCase):
    def test_form_widgets_include_placeholders_and_form_control(self):
        register = CustomUserCreationForm()
        for name, placeholder in zip(
            (
                "username",
                "email",
                "first_name",
                "last_name",
                "password1",
                "password2",
            ),
            REGISTER_PLACEHOLDERS,
            strict=True,
        ):
            attrs = register.fields[name].widget.attrs
            self.assertEqual(attrs["placeholder"], placeholder)
            self.assertEqual(attrs["class"], "form-control")

        login = LoginForm()
        self.assertEqual(login.fields["username"].widget.attrs["placeholder"], "Username")
        self.assertEqual(login.fields["password"].widget.attrs["placeholder"], "Password")
        self.assertEqual(login.fields["username"].widget.attrs["class"], "form-control")
        self.assertEqual(login.fields["password"].widget.attrs["class"], "form-control")

        signup = SignUpForm()
        self.assertEqual(signup.fields["password2"].widget.attrs["placeholder"], "Confirm password")
        self.assertEqual(signup.fields["email"].widget.attrs["class"], "form-control")

    def test_register_and_login_pages_render_placeholders(self):
        for url_name in ("register", "signup"):
            page = self.client.get(reverse(url_name))
            self.assertEqual(page.status_code, 200)
            for placeholder in REGISTER_PLACEHOLDERS:
                self.assertContains(page, f'placeholder="{placeholder}"')
            self.assertContains(page, 'class="form-control"')
            self.assertContains(page, 'class="sr-only" for="id_username"')
            self.assertContains(page, 'class="sr-only" for="id_password2"')
            self.assertContains(page, "Made with ❤️ by")

        login = self.client.get(reverse("login"))
        self.assertEqual(login.status_code, 200)
        self.assertContains(login, 'placeholder="Username"')
        self.assertContains(login, 'placeholder="Password"')
        self.assertContains(login, 'name="username"')
        self.assertContains(login, 'name="password"')
        self.assertContains(login, 'class="form-control"')
        self.assertContains(login, 'class="sr-only" for="id_username"')
        self.assertContains(login, 'class="sr-only" for="id_password"')
        self.assertContains(login, "Made with ❤️ by")

    def test_failed_register_renders_field_errors(self):
        response = self.client.post(
            reverse("register"),
            {
                "username": "",
                "email": "not-an-email",
                "first_name": "",
                "last_name": "",
                "password1": "library-pass-1",
                "password2": "different-pass-1",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "text-error")
        self.assertContains(response, "This field is required.")
        self.assertContains(response, "Enter a valid email address.")
        self.assertContains(response, "The two password fields didn’t match.")

    def test_failed_login_renders_non_field_errors(self):
        response = self.client.post(
            reverse("login"),
            {"username": "missing-user", "password": "not-the-password"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "text-error")
        self.assertContains(
            response,
            "Please enter a correct username and password.",
        )

    def test_login_accepts_valid_credentials(self):
        User.objects.create_user(username="reader", password="library-pass-1")
        response = self.client.post(
            reverse("login"),
            {"username": "reader", "password": "library-pass-1"},
        )
        self.assertRedirects(response, reverse("home"), fetch_redirect_response=False)
