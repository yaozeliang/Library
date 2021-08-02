
from django.contrib import admin
from django.urls import path, include  # add this
from .views import HomeView,BookListView,BookCreateView,BookDeleteView,BookDetailView,BookUpdateView
from .views import CategoryListView,CategoryCreateView,CategoryDeleteView
from .views import PublisherListView,PublisherCreateView,PublisherDeleteView,PublisherUpdateView
from .views import ActivityListView,ActivityDeleteView
from .views import MemberCreateView,MemberUpdateView,MemberDeleteView,MemberListView,MemberDetailView
from .views import ProfileDetailView,ProfileCreateView,ProfileUpdateView
from django.conf import settings
from django.conf.urls.static import static
# from .views import BorrowRecordCreateView,BorrowRecordListView




urlpatterns = [

    # HomePage
    path("",HomeView.as_view(), name='home'),
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

    # Membership
    path('member-list',MemberListView.as_view(),name="member_list"),
    path('member-create',MemberCreateView.as_view(),name="member_create"),  
    path('member-delete/<int:pk>/',MemberDeleteView.as_view(),name="member_delete"), 
    path('member-update/<int:pk>/',MemberUpdateView.as_view(),name="member_update"),
    path('member-detail/<int:pk>/',MemberDetailView.as_view(),name="member_detail"),

    # UserProfile
    path('user/profile-create/',ProfileCreateView.as_view(),name="profile_create"),
    path('user/<int:pk>/profile/',ProfileDetailView.as_view(),name="profile_detail"),
    path('user/<int:pk>/profile-update/',ProfileUpdateView.as_view(),name="profile_update"),


    # BorrowRecords
    # path('record-create/',BorrowRecordCreateView.as_view(),name="record_create"),
    # path('record-list/',BorrowRecordListView.as_view(),name="record_list"),

]



