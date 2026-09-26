
# Create your views here.
# Access control is REST_FRAMEWORK["DEFAULT_PERMISSION_CLASSES"]
# (IsSuperuserOrApiGroup). Do not set permission_classes on these views.
import re

from django.http import Http404
from django.urls import NoReverseMatch, URLPattern, URLResolver, get_resolver, reverse
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.views import APIView

from book.models import Book, Category, Member, Publisher

from .serializers import (
    BookSerializer,
    CategorySerializer,
    MemberSerializer,
    PublisherSerializer,
)

# Placeholder substituted back out of reverse() so the catalog shows <pk>
# rather than a concrete id. Only the int converter is used on these routes.
_REVERSE_SAMPLE = 987654321
_CRUD_METHODS = ("get", "post", "put", "patch", "delete")
_CONVERTER = re.compile(r"<(?:[^:>]+:)?([^>]+)>")
_CAMEL = re.compile(r"(?<=[a-z0-9])(?=[A-Z])")


def _mount_prefix():
    """Prefix where Api.urls is included, taken from the root resolver."""
    import Api.urls as api_urls

    for entry in get_resolver().url_patterns:
        if isinstance(entry, URLResolver) and entry.urlconf_module is api_urls:
            route = str(entry.pattern).strip("/")
            return f"/{route}/" if route else "/"
    mounted = reverse("api-overview")
    return mounted if mounted.endswith("/") else mounted + "/"


def _canonical_api_patterns(patterns):
    """Library routes only: no format-suffix copies and no browsable login."""
    for entry in patterns:
        if isinstance(entry, URLResolver):
            route = str(entry.pattern)
            if entry.namespace == "rest_framework" or route.startswith("api-auth"):
                continue
            yield from _canonical_api_patterns(entry.url_patterns)
        elif isinstance(entry, URLPattern):
            if "drf_format_suffix" in str(entry.pattern):
                continue
            yield entry


def _supported_methods(view_cls):
    """HTTP methods the view implements. OPTIONS/HEAD stay off the catalog."""
    if view_cls is None:
        return []
    methods = []
    for name in _CRUD_METHODS:
        if name in view_cls.http_method_names and name in view_cls.__dict__:
            methods.append(name.upper())
    return methods


def _endpoint_label(callback):
    view_cls = getattr(callback, "cls", None)
    raw = view_cls.__name__ if view_cls is not None else callback.__name__
    title = _CAMEL.sub(" ", raw)
    title = title[:1].upper() + title[1:]
    methods = _supported_methods(view_cls)
    if methods:
        return f"{title} ({', '.join(methods)})"
    return title


def _public_path(pattern, prefix):
    """Full path for one route. Named routes come from reverse()."""
    route = str(pattern.pattern)
    param_names = _CONVERTER.findall(route)
    if pattern.name:
        kwargs = {name: _REVERSE_SAMPLE for name in param_names}
        try:
            resolved = reverse(pattern.name, kwargs=kwargs)
        except NoReverseMatch:
            resolved = None
        if resolved is not None:
            for name in param_names:
                resolved = resolved.replace(str(_REVERSE_SAMPLE), f"<{name}>", 1)
            return resolved
    simplified = _CONVERTER.sub(r"<\1>", route)
    return prefix + simplified


def _api_overview():
    """Name-to-path map of every real /api/ route, built from the URLconf."""
    import Api.urls as api_urls

    prefix = _mount_prefix()
    catalog = {}
    for pattern in _canonical_api_patterns(api_urls.urlpatterns):
        path = _public_path(pattern, prefix)
        label = _endpoint_label(pattern.callback)
        if label in catalog:
            label = f"{label} {path}"
        catalog[label] = path
    return catalog


@api_view(["GET"])
def apiOverview(request, format=None):
    return Response(_api_overview())


# Category API View


@api_view(["GET"])
def CategoryList(request, format=None):
    cats = Category.objects.all().order_by("-created_at")
    serializer = CategorySerializer(cats, many=True)
    return Response(serializer.data)


# One function with CRUD , including type "PUT","GET","POST","DELETE"
# class CategoryList(viewsets.ModelViewSet):
#     serializer_class = CategorySerializer
#     queryset = Category.objects.all().order_by('-created_at')


@api_view(["POST"])
def CategoryCreate(request, format=None):
    serializer = CategorySerializer(data=request.data)

    if serializer.is_valid():
        serializer.save()
    return Response(serializer.data)


@api_view(["GET"])
def CategoryDetail(request, pk, format=None):
    cat = Category.objects.get(id=pk)
    serializer = CategorySerializer(cat, many=False)
    return Response(serializer.data)


@api_view(["DELETE"])
def CategoryDelete(request, pk, format=None):
    cat = Category.objects.get(id=pk)
    cat.delete()
    return Response(f"{cat.name} succsesfully delete!")


# Book Api View
@api_view(["GET"])
def BookList(request, format=None):
    books = Book.objects.all().order_by("-updated_by")
    serializer = BookSerializer(books, many=True)
    return Response(serializer.data)


@api_view(["POST"])
def BookCreate(request, format=None):
    serializer = BookSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
    return Response(serializer.data)


@api_view(["GET"])
def BookDetail(request, pk, format=None):
    book = Book.objects.get(id=pk)
    serializer = BookSerializer(book, many=False)
    return Response(serializer.data)


@api_view(["POST"])
def BookUpdate(request, pk, format=None):
    book = Book.objects.get(id=pk)
    serializer = BookSerializer(instance=book, data=request.data)
    if serializer.is_valid():
        serializer.save()
    return Response(serializer.data)


@api_view(["DELETE"])
def BookDelete(request, pk, format=None):
    book = Book.objects.get(id=pk)
    book.delete()
    return Response(f"{book.title} succsesfully delete!")


# Publisher Api View
@api_view(["GET"])
def PublisherList(request, format=None):
    pubs = Publisher.objects.all().order_by("-created_at")
    serializer = PublisherSerializer(pubs, many=True)
    return Response(serializer.data)


@api_view(["POST"])
def PublisherCreate(request, format=None):
    serializer = PublisherSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
    return Response(serializer.data)


@api_view(["POST"])
def PublisherUpdate(request, pk, format=None):
    pub = Publisher.objects.get(id=pk)
    serializer = PublisherSerializer(instance=pub, data=request.data)
    if serializer.is_valid():
        serializer.save()
    return Response(serializer.data)


@api_view(["DELETE"])
def PublisherDelete(request, pk, format=None):
    pub = Publisher.objects.get(id=pk)
    pub.delete()
    return Response(f"{pub.name} succsesfully delete!")


# Member API


class MemberList(APIView):
    def get(self, request, format=None):
        members = Member.objects.all()
        serializer = MemberSerializer(members, many=True)
        return Response(serializer.data)

    def post(self, request, format=None):
        serializer = MemberSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class MemberDetail(APIView):
    def get_object(self, pk):
        try:
            return Member.objects.get(pk=pk)
        except Member.DoesNotExist:
            return Http404

    def get(self, request, pk, format=None):
        member = self.get_object(pk)
        serializer = MemberSerializer(member)
        return Response(serializer.data)

    def put(self, request, pk, format=None):
        member = self.get_object(pk)
        serializer = MemberSerializer(member, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk, format=None):
        member = self.get_object(pk)
        member.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# User Api
