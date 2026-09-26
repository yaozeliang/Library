"""Authentication views for the Library Management System."""

from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LogoutView
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views.generic import CreateView

from .forms import CustomUserCreationForm


class PostOnlyLogoutView(LogoutView):
    """Log out only on POST so a cross-site GET cannot end the session.

    Django 2.2's LogoutView logs the user out inside ``dispatch`` before it
    checks ``http_method_names``, so GET has to be rejected first.
    """

    http_method_names = ["post", "head", "options"]

    def dispatch(self, request, *args, **kwargs):
        if request.method.lower() != "post":
            return self.http_method_not_allowed(request, *args, **kwargs)
        return super().dispatch(request, *args, **kwargs)


class SignUpView(CreateView):
    """User registration view."""

    form_class = CustomUserCreationForm
    success_url = reverse_lazy("login")
    # Public signup stays: the login page already links to /auth/register/,
    # and this URL is the same form. registration/signup.html was never added.
    template_name = "registration/register.html"


@login_required
def profile_view(request):
    """Display user profile."""
    from book.models import Profile

    # Get or create profile for the user
    profile, created = Profile.objects.get_or_create(user=request.user)

    return render(request, "profile/profile_detail.html", {"profile": profile})


def register_view(request):
    """Handle user registration."""
    if request.method == "POST":
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("home")
    else:
        form = CustomUserCreationForm()
    return render(request, "registration/register.html", {"form": form})
