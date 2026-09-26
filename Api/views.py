
# Create your views here.
# Access control is REST_FRAMEWORK["DEFAULT_PERMISSION_CLASSES"]
# (IsSuperuserOrApiGroup). Do not set permission_classes on these views.
from django.http import Http404
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


@api_view(["GET"])
def apiOverview(request, format=None):
    api_urls = {
        "Category List": "/category-list/",
        "Category Create": "/category-create/",
        "Category Delete": "/category-delete/<int:pk>/",
        "Publisher List": "/publisher-list/",
        "Publisher Create": "/publisher-create/",
        "Publisher Update": "/publisher-update/<int:pk>/",
        "Publisher Delete": "/publisher-delete/<int:pk>/",
        "Book List": "/book-list/",
        "Book Detail": "/book-detail/<int:pk>/",
        "Book Create": "/book-create/",
        "Book Update": "/book-update/<int:pk>/",
        "Book Delete": "/book-delete/<int:pk>/",
        "Member List": "/member-list/",
        "Member Detail": "/member-detail/<int:pk>/",
        "Member Create": "/member-create/",
        "Member Update": "/member-update/<int:pk>/",
        "Member Delete": "/member-delete/<int:pk>/",
    }

    return Response(api_urls)


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
