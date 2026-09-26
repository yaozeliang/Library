"""Every /api/ route requires a superuser or a member of the api group."""

import re

from django.contrib.auth.models import Group, User
from django.test import TestCase
from django.urls import URLPattern, URLResolver, resolve, reverse
from rest_framework.settings import api_settings
from rest_framework.test import APIClient

from Api.permissions import IsSuperuserOrApiGroup
from book.models import Book, Category, Member, Publisher

# Canonical routes from Api.urls. Format-suffix copies are registered too
# and are included by walking urlpatterns.
REQUIRED_ROUTES = (
    "",
    "category-list/",
    "category-create/",
    "category-detail/<int:pk>/",
    "category-delete/<int:pk>/",
    "book-list/",
    "book-create/",
    "book-detail/<int:pk>/",
    "book-update/<int:pk>/",
    "book-delete/<int:pk>/",
    "publisher-list/",
    "publisher-create/",
    "publisher-update/<int:pk>/",
    "publisher-delete/<int:pk>/",
    "members/",
    "members/<int:pk>",
)

_BOOK = {"author": "Ada", "title": "Guide", "description": "A short guide"}
_PUBLISHER = {"name": "Press", "city": "Paris"}
_CATEGORY = {"name": "Fiction"}
_MEMBER = {"name": "Pat", "city": "Paris", "phone_number": "0600000000"}

_WRITE_PAYLOADS = {
    "CategoryCreate": _CATEGORY,
    "BookCreate": _BOOK,
    "BookUpdate": _BOOK,
    "PublisherCreate": _PUBLISHER,
    "PublisherUpdate": _PUBLISHER,
    "MemberList": _MEMBER,
    "MemberDetail": _MEMBER,
}


def _api_view_patterns():
    """DRF views mounted under /api/, including format-suffix copies.

    ``/api/api-auth/`` is Django REST framework's browsable login and is
    not one of the library API views.
    """
    from Api.urls import urlpatterns

    found = []

    def walk(patterns):
        for entry in patterns:
            if isinstance(entry, URLResolver):
                if entry.namespace == "rest_framework":
                    continue
                walk(entry.url_patterns)
            elif isinstance(entry, URLPattern):
                found.append(entry)

    walk(urlpatterns)
    return found


def _http_methods(callback):
    view_cls = callback.cls
    methods = []
    for name in ("get", "post", "put", "patch", "delete"):
        if name in view_cls.http_method_names and name in view_cls.__dict__:
            methods.append(name)
    return methods


def _kind_for(route):
    if "<int:pk>" not in route:
        return None
    if route.startswith("category-"):
        return "category"
    if route.startswith("book-"):
        return "book"
    if route.startswith("publisher-"):
        return "publisher"
    if route.startswith("members"):
        return "member"
    raise AssertionError(f"No fixture model for API route {route}")


def _create(kind):
    if kind == "category":
        return Category.objects.create(name="Fiction")
    if kind == "book":
        return Book.objects.create(
            author="Ada", title="Guide", description="A short guide"
        )
    if kind == "publisher":
        return Publisher.objects.create(name="Press", city="Paris")
    if kind == "member":
        return Member.objects.create(
            name="Pat", city="Paris", phone_number="0600000000"
        )
    raise AssertionError(kind)


def _request_path(route):
    """Turn a URL route into a concrete /api/ path."""
    kind = _kind_for(route)
    if kind is not None:
        route = route.replace("<int:pk>", str(_create(kind).pk))
    route = route.replace("<drf_format_suffix:format>", ".json")
    return "/api/" + route


def _success_status(view_name, method):
    """Status the view already returns after the permission check passes.

    Member create is 201 and member delete is 204. Every other method,
    including GET on those same routes, returns 200.
    """
    if view_name == "MemberList" and method == "post":
        return 201
    if view_name == "MemberDetail" and method == "delete":
        return 204
    return 200


class ApiGroupPermissionTests(TestCase):
    def setUp(self):
        self.api_group = Group.objects.create(name="api")
        self.superuser = User.objects.create_superuser(
            username="root", email="root@example.com", password="root-pass-1"
        )
        self.api_staff = User.objects.create_user(
            username="api-staff", password="api-pass-1", is_staff=True
        )
        self.api_staff.groups.add(self.api_group)
        self.outsider = User.objects.create_user(
            username="outsider", password="out-pass-1", is_staff=True
        )
        self.clients = {
            "superuser": APIClient(),
            "api_staff": APIClient(),
            "outsider": APIClient(),
            "anonymous": APIClient(),
        }
        self.clients["superuser"].force_login(self.superuser)
        self.clients["api_staff"].force_login(self.api_staff)
        self.clients["outsider"].force_login(self.outsider)

    def test_default_permission_is_the_api_group_rule(self):
        self.assertEqual(
            list(api_settings.DEFAULT_PERMISSION_CLASSES),
            [IsSuperuserOrApiGroup],
        )

    def test_every_registered_api_route_enforces_the_group(self):
        self.assertFalse(self.superuser.groups.filter(name="api").exists())
        self.assertTrue(self.api_staff.is_staff)
        self.assertFalse(self.api_staff.is_superuser)
        self.assertTrue(self.api_staff.groups.filter(name="api").exists())
        self.assertTrue(self.outsider.is_staff)
        self.assertFalse(self.outsider.is_superuser)
        self.assertFalse(self.outsider.groups.exists())

        patterns = _api_view_patterns()
        registered = {str(pattern.pattern) for pattern in patterns}
        missing = [route for route in REQUIRED_ROUTES if route not in registered]
        self.assertEqual(missing, [])
        self.assertGreaterEqual(len(patterns), len(REQUIRED_ROUTES))

        for pattern in patterns:
            view_cls = pattern.callback.cls
            self.assertIn(
                IsSuperuserOrApiGroup,
                view_cls.permission_classes,
                str(pattern.pattern),
            )
            methods = _http_methods(pattern.callback)
            self.assertTrue(methods, str(pattern.pattern))
            route = str(pattern.pattern)
            for method in methods:
                self._assert_method(view_cls.__name__, route, method)

    def _assert_method(self, view_name, route, method):
        payload = None
        if method in ("post", "put", "patch"):
            payload = _WRITE_PAYLOADS.get(view_name)
            self.assertIsNotNone(payload, f"No payload for {view_name} {method}")
        allowed = _success_status(view_name, method)

        for label in ("superuser", "api_staff", "outsider", "anonymous"):
            path = _request_path(route)
            client = self.clients[label]
            with self.subTest(view=view_name, route=route, method=method, user=label):
                if payload is None:
                    response = getattr(client, method)(path)
                else:
                    response = getattr(client, method)(path, payload, format="json")
                if label == "anonymous":
                    self.assertIn(response.status_code, (401, 403))
                elif label == "outsider":
                    self.assertEqual(response.status_code, 403)
                else:
                    self.assertEqual(response.status_code, allowed)


def _canonical_patterns():
    """Routes a client can call. Drops format-suffix copies and api-auth."""
    found = []
    for pattern in _api_view_patterns():
        route = str(pattern.pattern)
        if "drf_format_suffix" in route:
            continue
        found.append(pattern)
    return found


def _public_route(route):
    """Turn a URLconf route into the path the overview should publish."""
    simplified = re.sub(r"<(?:[^:>]+:)?([^>]+)>", r"<\1>", route)
    return "/api/" + simplified


class ApiOverviewTests(TestCase):
    def setUp(self):
        self.superuser = User.objects.create_superuser(
            username="overview-root",
            email="overview-root@example.com",
            password="root-pass-1",
        )
        self.client = APIClient()
        self.client.force_login(self.superuser)

    def test_overview_paths_match_registered_api_routes(self):
        response = self.client.get(reverse("api-overview"))
        self.assertEqual(response.status_code, 200)
        overview = response.json()
        self.assertIsInstance(overview, dict)

        patterns = _canonical_patterns()
        self.assertTrue(patterns)
        expected = {_public_route(str(pattern.pattern)) for pattern in patterns}
        published = set(overview.values())

        self.assertEqual(published, expected)
        self.assertEqual(len(overview), len(patterns))
        for path in published:
            self.assertIsInstance(path, str)
            self.assertTrue(path.startswith("/api/"), path)
            self.assertNotIn("drf_format_suffix", path)
            self.assertNotIn("api-auth", path)
            concrete = re.sub(r"<[^>]+>", "1", path)
            match = resolve(concrete)
            route = match.route.removeprefix("api/")
            self.assertIn(route, {str(pattern.pattern) for pattern in patterns})
            self.assertNotIn("drf_format_suffix", match.route)

        by_path = {path: label for label, path in overview.items()}
        for pattern in patterns:
            path = _public_route(str(pattern.pattern))
            label = by_path[path]
            for method in _http_methods(pattern.callback):
                self.assertIn(method.upper(), label)

        self.assertNotIn("/member-create/", published)
        self.assertNotIn("/member-update/<pk>/", published)
        self.assertNotIn("/member-delete/<pk>/", published)
        self.assertIn("/api/book-list/", published)
        self.assertIn("/api/members/", published)
        self.assertIn("/api/members/<pk>", published)
