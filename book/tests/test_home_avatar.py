"""Home stays up when activity authors have no profile picture."""

import shutil
import tempfile
from io import BytesIO
from unittest.mock import patch

import requests
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from PIL import Image

from book.models import Profile, UserActivity

MEDIA_ROOT = tempfile.mkdtemp(prefix="library-avatar-tests-")


def _png_upload(name="avatar.png"):
    buffer = BytesIO()
    Image.new("RGB", (20, 20), color="red").save(buffer, format="PNG")
    return SimpleUploadedFile(name, buffer.getvalue(), content_type="image/png")


@override_settings(MEDIA_ROOT=MEDIA_ROOT)
class HomeAvatarTests(TestCase):
    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        weather = patch(
            "book.templatetags.book_extras.requests.get",
            side_effect=requests.RequestException("offline"),
        )
        weather.start()
        self.addCleanup(weather.stop)

        self.user = User.objects.create_user(
            username="alice", password="pass12345", email="alice@example.com"
        )
        self.client.login(username="alice", password="pass12345")
        UserActivity.objects.create(
            created_by=self.user.username,
            operation_type="success",
            target_model="Book",
            detail="Added a book",
        )

    def test_home_renders_when_activity_author_has_no_avatar(self):
        profile = Profile.objects.get(user=self.user)
        self.assertFalse(profile.profile_pic)

        response = self.client.get(reverse("home"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "alice")
        self.assertContains(response, "assets/images/user/avatar-2.jpg")

    def test_home_renders_when_activity_author_has_no_profile(self):
        UserActivity.objects.create(
            created_by="missing-user",
            operation_type="info",
            target_model="Book",
            detail="Unknown author",
        )

        response = self.client.get(reverse("home"))

        self.assertEqual(response.status_code, 200)

    def test_profile_pic_upload_redirects_home_without_error(self):
        profile = Profile.objects.get(user=self.user)
        response = self.client.post(
            reverse("profile_update", args=[profile.pk]),
            {
                "bio": "Updated bio",
                "phone_number": "0600000000",
                "email": "alice@example.com",
                "profile_pic": _png_upload(),
            },
            follow=True,
        )

        profile.refresh_from_db()
        self.assertTrue(profile.profile_pic)
        self.assertRedirects(response, reverse("home"))
        self.assertContains(response, profile.profile_pic.url)


@override_settings(MEDIA_ROOT=MEDIA_ROOT)
class ProfileUpdateOwnershipTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(username="owner", password="pass12345")
        self.other = User.objects.create_user(username="other", password="pass12345")
        self.client.login(username="owner", password="pass12345")

    def test_user_can_open_own_profile_update(self):
        response = self.client.get(
            reverse("profile_update", args=[self.owner.profile.pk])
        )
        self.assertEqual(response.status_code, 200)

    def test_user_cannot_edit_another_profile(self):
        other_profile = self.other.profile
        url = reverse("profile_update", args=[other_profile.pk])

        self.assertEqual(self.client.get(url).status_code, 404)

        response = self.client.post(
            url,
            {
                "bio": "taken over",
                "phone_number": "0600000001",
                "email": "other@example.com",
            },
        )
        self.assertEqual(response.status_code, 404)
        other_profile.refresh_from_db()
        self.assertNotEqual(other_profile.bio, "taken over")
