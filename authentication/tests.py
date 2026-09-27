"""Auth page tests for login and registration forms."""

from django.contrib.auth.models import User
from django.template.loader import render_to_string
from django.test import RequestFactory, TestCase
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

AUTH_TEMPLATES = (
    "accounts/login.html",
    "accounts/register.html",
    "registration/register.html",
    "login.html",
    "register.html",
)


def _field_error_html(html, field_name):
    """Return the text-error span that follows the named input."""
    marker = f'name="{field_name}"'
    start = html.find(marker)
    if start == -1:
        raise AssertionError(f"{field_name} input missing")
    span_at = html.find('class="text-error"', start)
    if span_at == -1:
        raise AssertionError(f"no text-error after {field_name}")
    end = html.find("</span>", span_at)
    return html[span_at:end]


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
            self.assertEqual(attrs["aria-label"], placeholder)
            self.assertEqual(attrs["class"], "form-control")

        login = LoginForm()
        self.assertEqual(login.fields["username"].widget.attrs["placeholder"], "Username")
        self.assertEqual(login.fields["username"].widget.attrs["aria-label"], "Username")
        self.assertEqual(login.fields["password"].widget.attrs["placeholder"], "Password")
        self.assertEqual(login.fields["password"].widget.attrs["aria-label"], "Password")
        self.assertEqual(login.fields["username"].widget.attrs["class"], "form-control")
        self.assertEqual(login.fields["password"].widget.attrs["class"], "form-control")

        signup = SignUpForm()
        self.assertEqual(
            signup.fields["password2"].widget.attrs["placeholder"],
            "Confirm password",
        )
        self.assertEqual(
            signup.fields["password2"].widget.attrs["aria-label"],
            "Confirm password",
        )
        self.assertEqual(signup.fields["email"].widget.attrs["class"], "form-control")

    def test_register_and_login_pages_render_placeholders(self):
        for url_name in ("register", "signup"):
            page = self.client.get(reverse(url_name))
            self.assertEqual(page.status_code, 200)
            for placeholder in REGISTER_PLACEHOLDERS:
                self.assertContains(page, f'placeholder="{placeholder}"')
                self.assertContains(page, f'aria-label="{placeholder}"')
            self.assertContains(page, 'class="form-control"')
            self.assertContains(page, 'class="sr-only" for="id_username"')
            self.assertContains(page, 'class="sr-only" for="id_password2"')
            self.assertNotContains(page, "checkbox-fill-1")
            self.assertNotContains(page, "Agree with")
            self.assertContains(page, "Made with ❤️ by")

        login = self.client.get(reverse("login"))
        self.assertEqual(login.status_code, 200)
        self.assertContains(login, 'placeholder="Username"')
        self.assertContains(login, 'aria-label="Username"')
        self.assertContains(login, 'placeholder="Password"')
        self.assertContains(login, 'aria-label="Password"')
        self.assertContains(login, 'name="username"')
        self.assertContains(login, 'name="password"')
        self.assertContains(login, 'class="form-control"')
        self.assertContains(login, 'class="sr-only" for="id_username"')
        self.assertContains(login, 'class="sr-only" for="id_password"')
        self.assertNotContains(login, "checkbox-fill-1")
        self.assertNotContains(login, "Save Details")
        self.assertContains(login, "Made with ❤️ by")

    def test_auth_templates_omit_fake_checkboxes(self):
        request = RequestFactory().get("/")
        register_form = CustomUserCreationForm()
        login_form = LoginForm()
        for name in AUTH_TEMPLATES:
            form = login_form if "login" in name else register_form
            html = render_to_string(name, {"form": form}, request=request)
            self.assertNotIn("checkbox-fill-1", html, name)
            self.assertNotIn("Save Details", html, name)
            self.assertNotIn("Agree with", html, name)
            self.assertIn("aria-label=", html, name)
            self.assertIn("Made with ❤️ by", html, name)

    def test_failed_signup_keeps_values_and_shows_field_errors(self):
        User.objects.create_user(username="taken", password="library-pass-1")
        cases = {
            "register": reverse("register"),
            "signup": reverse("signup"),
        }
        for url in cases.values():
            taken = self.client.post(
                url,
                {
                    "username": "taken",
                    "email": "reader@example.com",
                    "first_name": "Ada",
                    "last_name": "Lovelace",
                    "password1": "library-pass-1",
                    "password2": "library-pass-1",
                },
            )
            self.assertEqual(taken.status_code, 200)
            html = taken.content.decode()
            self.assertIn('value="taken"', html)
            self.assertIn('value="reader@example.com"', html)
            self.assertIn('value="Ada"', html)
            self.assertIn('value="Lovelace"', html)
            self.assertIn(
                "A user with that username already exists.",
                _field_error_html(html, "username"),
            )
            self.assertEqual(User.objects.filter(username="taken").count(), 1)

            invalid_email = self.client.post(
                url,
                {
                    "username": "newreader",
                    "email": "not-an-email",
                    "first_name": "Ada",
                    "last_name": "Lovelace",
                    "password1": "library-pass-1",
                    "password2": "library-pass-1",
                },
            )
            self.assertEqual(invalid_email.status_code, 200)
            email_html = invalid_email.content.decode()
            self.assertIn('value="newreader"', email_html)
            self.assertIn('value="not-an-email"', email_html)
            self.assertIn('value="Ada"', email_html)
            self.assertIn('value="Lovelace"', email_html)
            self.assertIn(
                "Enter a valid email address.",
                _field_error_html(email_html, "email"),
            )

            mismatch = self.client.post(
                url,
                {
                    "username": "newreader",
                    "email": "reader@example.com",
                    "first_name": "Ada",
                    "last_name": "Lovelace",
                    "password1": "library-pass-1",
                    "password2": "library-pass-2",
                },
            )
            self.assertEqual(mismatch.status_code, 200)
            mismatch_html = mismatch.content.decode()
            self.assertIn('value="newreader"', mismatch_html)
            self.assertIn('value="reader@example.com"', mismatch_html)
            self.assertIn(
                "The two password fields didn’t match.",
                _field_error_html(mismatch_html, "password2"),
            )

            too_short = self.client.post(
                url,
                {
                    "username": "newreader",
                    "email": "reader@example.com",
                    "first_name": "Ada",
                    "last_name": "Lovelace",
                    "password1": "short1",
                    "password2": "short1",
                },
            )
            self.assertEqual(too_short.status_code, 200)
            short_html = too_short.content.decode()
            self.assertIn('value="newreader"', short_html)
            self.assertIn('value="reader@example.com"', short_html)
            self.assertIn('value="Ada"', short_html)
            self.assertIn('value="Lovelace"', short_html)
            self.assertIn("too short", _field_error_html(short_html, "password2"))
            self.assertFalse(User.objects.filter(username="newreader").exists())

    def test_wrong_password_login_shows_an_error(self):
        User.objects.create_user(username="reader", password="library-pass-1")
        response = self.client.post(
            reverse("login"),
            {"username": "reader", "password": "not-the-password"},
        )
        self.assertEqual(response.status_code, 200)
        html = response.content.decode()
        before_fields = html.split('name="username"', 1)[0]
        self.assertIn("text-error", before_fields)
        self.assertIn(
            "Please enter a correct username and password.",
            before_fields,
        )
        self.assertIn('value="reader"', html)
        self.assertNotIn("checkbox-fill-1", html)

    def test_login_accepts_valid_credentials(self):
        User.objects.create_user(username="reader", password="library-pass-1")
        response = self.client.post(
            reverse("login"),
            {"username": "reader", "password": "library-pass-1"},
        )
        self.assertRedirects(response, reverse("home"), fetch_redirect_response=False)
