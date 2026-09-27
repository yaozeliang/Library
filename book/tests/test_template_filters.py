"""Template helpers used by list pages, kept off the route-smoke suite."""

from datetime import timedelta

from django.contrib.auth.models import Group, User
from django.template import Context
from django.test import RequestFactory, TestCase
from django.utils import timezone

from book.custom_filter import get_item as custom_get_item
from book.custom_filter import has_group as custom_has_group
from book.templatetags.book_extras import get_item, has_group, param_replace, timesince


class TimesinceTests(TestCase):
    def test_buckets(self):
        now = timezone.now()
        self.assertIn("just now", timesince(now - timedelta(seconds=10)))
        self.assertIn("minutes ago", timesince(now - timedelta(minutes=5)))
        self.assertIn("hours ago", timesince(now - timedelta(hours=3)))
        self.assertIn("day ago", timesince(now - timedelta(days=1)))
        self.assertIn("days ago", timesince(now - timedelta(days=4)))
        self.assertIn("months ago", timesince(now - timedelta(days=40)))
        self.assertIn("years ago", timesince(now - timedelta(days=400)))
        self.assertEqual(timesince(now + timedelta(days=1)), "")


class GroupAndQueryTests(TestCase):
    def test_has_group_and_get_item(self):
        user = User.objects.create_user(username="pat", password="pat-pass-1")
        admin = User.objects.create_superuser(
            username="root", email="root@example.com", password="root-pass-1"
        )
        Group.objects.create(name="logs")
        user.groups.add(Group.objects.get(name="logs"))

        self.assertTrue(has_group(user, "logs"))
        self.assertFalse(has_group(user, "api"))
        self.assertTrue(has_group(admin, "api"))
        self.assertTrue(custom_has_group(admin, "download_data"))
        self.assertEqual(get_item({"a": 1}, "a"), 1)
        self.assertIsNone(get_item({"a": 1}, "missing"))
        self.assertEqual(custom_get_item({"a": 1}, "a"), 1)

    def test_param_replace_drops_empty_values(self):
        request = RequestFactory().get("/record-list/", {"page": "2", "search": ""})
        rendered = param_replace(Context({"request": request}), page=4, orderby="borrower")
        self.assertIn("page=4", rendered)
        self.assertIn("orderby=borrower", rendered)
        self.assertNotIn("search", rendered)
