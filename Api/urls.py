from django.urls import include, path
from rest_framework import routers
from Api import views



urlpatterns = [
    # Category API    
    path('category-list/', views.CategoryList, name="api_category_list"),
    path('category-create/', views.CategoryCreate, name="api_category_create"),
    path('category-detail/<int:pk>/', views.CategoryDetail, name="api_category_detail"),
    path('category-delete/<int:pk>/', views.CategoryDelete, name="api_category_delete"),
    
    # Book API    
    path('book-list/', views.BookList, name="api_book_list"),
    path('book-create/', views.BookCreate, name="api_book_create"),
    path('book-detail/<int:pk>/', views.BookDetail, name="api_book_detail"),
    path('book-update/<int:pk>/', views.BookUpdate, name="api_book_update"),
    path('book-delete/<int:pk>/', views.BookDelete, name="api_book_delete"),

    path('', views.apiOverview, name="api-overview"),
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework'))
]