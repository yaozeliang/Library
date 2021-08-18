from django.urls import include, path
from rest_framework import routers
from Api import views
from rest_framework.urlpatterns import format_suffix_patterns



urlpatterns = [

    #Home
    path('', views.apiOverview, name="api-overview"),
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),

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

    # Publisher API    
    path('publisher-list/', views.PublisherList, name="api_publisher_list"),
    path('publisher-create/', views.PublisherCreate, name="api_publisher_create"),
    path('publisher-update/<int:pk>/', views.PublisherUpdate, name="api_publisher_update"),
    path('publisher-delete/<int:pk>/', views.PublisherDelete, name="api_publisher_delete"),

    # Member API
    path('members/', views.MemberList.as_view()),
    path('members/<int:pk>', views.MemberDetail.as_view()),
]


urlpatterns = format_suffix_patterns(urlpatterns)
