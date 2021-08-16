from django.shortcuts import render

# Create your views here.
from django.contrib.auth.models import User, Group
from rest_framework import viewsets
from rest_framework import permissions
from Api.serializers import UserSerializer, GroupSerializer
from django.http import JsonResponse
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework import permissions
from .serializers import CategorySerializer,BookSerializer
from book.models import Member,Category,Publisher,Book





@api_view(['GET'])
@permission_classes((permissions.AllowAny,))
def apiOverview(request):
	api_urls = {
		'Category List':'/category-list/',
		'Category Create':'/category-create/',
        'Category Delete':'/category-delete/<int:pk>/',
		'Publisher List':'/publisher-list/',
		'Publisher Create':'/publisher-create/',
        'Publisher Update':'/publisher-update/<int:pk>/',
        'Publisher Delete':'/publisher-delete/<int:pk>/',
		'Book List':'/book-list/',
        'Book Detail':'/book-detail/<int:pk>/',
		'Book Create':'/book-create/',
        'Book Update':'/book-update/<int:pk>/',
        'Book Delete':'/book-delete/<int:pk>/',
        'Member List':'/member-list/',
        'Member Detail':'/member-detail/<int:pk>/',
		'Member Create':'/member-create/',
        'Member Update':'/member-update/<int:pk>/',
        'Member Delete':'/member-delete/<int:pk>/',
		}

	return Response(api_urls)


@api_view(['GET'])
@permission_classes((permissions.IsAuthenticated,))
def CategoryList(request):
	cats = Category.objects.all().order_by('-id')
	serializer = CategorySerializer(cats, many=True)
	return Response(serializer.data)

# Category API View

@api_view(['POST'])
@permission_classes((permissions.IsAuthenticated,))
def CategoryCreate(request):
	serializer = CategorySerializer(data=request.data)

	if serializer.is_valid():
		serializer.save()
	return Response(serializer.data)


@api_view(['GET'])
@permission_classes((permissions.IsAuthenticated,))
def CategoryDetail(request,pk):
	cat = Category.objects.get(id=pk)
	serializer = CategorySerializer(cat, many=False)
	return Response(serializer.data)

@api_view(['DELETE'])
@permission_classes((permissions.IsAuthenticated,))
def CategoryDelete(request, pk):
	cat = Category.objects.get(id=pk)
	cat.delete()
	return Response(f'{cat.name} succsesfully delete!')


# Book Api View

@api_view(['GET'])
@permission_classes((permissions.IsAuthenticated,))
def BookList(request):
	books = Book.objects.all().order_by('-updated_by')
	serializer = BookSerializer(books, many=True)
	return Response(serializer.data)


@api_view(['POST'])
@permission_classes((permissions.IsAuthenticated,))
def BookCreate(request):
	serializer = BookSerializer(data=request.data)
	if serializer.is_valid():
		serializer.save()
	return Response(serializer.data)


@api_view(['GET'])
@permission_classes((permissions.IsAuthenticated,))
def BookDetail(request,pk):
	book = Book.objects.get(id=pk)
	serializer = BookSerializer(book, many=False)
	return Response(serializer.data)

@api_view(['POST'])
@permission_classes((permissions.IsAuthenticated,))
def BookUpdate(request, pk):
	book = Book.objects.get(id=pk)
	serializer = BookSerializer(instance=book, data=request.data)
	if serializer.is_valid():
		serializer.save()
	return Response(serializer.data)



@api_view(['DELETE'])
@permission_classes((permissions.IsAuthenticated,))
def BookDelete(request, pk):
	book = Book.objects.get(id=pk)
	book.delete()
	return Response(f'{book.title} succsesfully delete!')








class UserViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    queryset = User.objects.all().order_by('-date_joined')
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]


class GroupViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows groups to be viewed or edited.
    """
    queryset = Group.objects.all()
    serializer_class = GroupSerializer
    permission_classes = [permissions.IsAuthenticated]




