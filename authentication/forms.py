"""Authentication forms for the Library Management System."""

from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User


def _apply_widget_attrs(form, placeholders):
    """Add Datta Able placeholders without replacing the field widgets."""
    for name, placeholder in placeholders.items():
        field = form.fields.get(name)
        if field is None:
            continue
        field.widget.attrs.update(
            {
                "placeholder": placeholder,
                "class": "form-control",
            }
        )


class CustomUserCreationForm(UserCreationForm):
    """Custom user creation form with additional fields."""

    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)

    class Meta:
        """Meta class for CustomUserCreationForm."""

        model = User
        fields = (
            "username",
            "email",
            "first_name",
            "last_name",
            "password1",
            "password2",
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _apply_widget_attrs(
            self,
            {
                "username": "Username",
                "email": "Email",
                "first_name": "First name",
                "last_name": "Last name",
                "password1": "Password",
                "password2": "Confirm password",
            },
        )

    def save(self, commit=True):
        """Save the user with cleaned data."""
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        user.first_name = self.cleaned_data["first_name"]
        user.last_name = self.cleaned_data["last_name"]
        if commit:
            user.save()
        return user


class LoginForm(AuthenticationForm):
    """User login form used by the auth login view."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _apply_widget_attrs(
            self,
            {
                "username": "Username",
                "password": "Password",
            },
        )


class SignUpForm(UserCreationForm):
    """User signup form."""

    username = forms.CharField()
    email = forms.EmailField()
    password1 = forms.CharField(strip=False, widget=forms.PasswordInput)
    password2 = forms.CharField(strip=False, widget=forms.PasswordInput)

    class Meta:
        """Meta class for SignUpForm."""

        model = User
        fields = ("username", "email", "password1", "password2")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _apply_widget_attrs(
            self,
            {
                "username": "Username",
                "email": "Email",
                "password1": "Password",
                "password2": "Confirm password",
            },
        )
