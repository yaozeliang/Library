
from django.contrib import admin
from django.urls import path, include  # add this
from .views import BookListView,BookCreateView,BookDeleteView,BookDetailView,BookUpdateView
from .views import CategoryListView,CategoryCreateView,CategoryDeleteView
from .views import PublisherListView,PublisherCreateView,PublisherDeleteView,PublisherUpdateView
from .views import ActivityListView,ActivityDeleteView
urlpatterns = [
    # Book
    path('book-list',BookListView.as_view(),name="book_list"),
    path('book-create',BookCreateView.as_view(),name="book_create"),
    path('book-update/<int:pk>/',BookUpdateView.as_view(),name="book_update"),
    path('book-delete/<int:pk>/',BookDeleteView.as_view(),name="book_delete"),
    path('book-detail/<int:pk>/',BookDetailView.as_view(),name="book_detail"),

    # Category
    path('category-list',CategoryListView.as_view(),name="category_list"),
    path('category-create',CategoryCreateView.as_view(),name="category_create"),  
    path('category-delete/<int:pk>/',CategoryDeleteView.as_view(),name="category_delete"), 

    # Publisher
    path('publisher-list',PublisherListView.as_view(),name="publisher_list"),
    path('publisher-create',PublisherCreateView.as_view(),name="publisher_create"),  
    path('publisher-delete/<int:pk>/',PublisherDeleteView.as_view(),name="publisher_delete"), 
    path('publisher-update/<int:pk>/',PublisherUpdateView.as_view(),name="publisher_update"),

    # User Activity
    path('user-activity-list',ActivityListView.as_view(),name="user_activity_list"),
    path('user-activity-list/<int:pk>/',ActivityDeleteView.as_view(),name="user_activity_delete"),

]
