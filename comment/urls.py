"""URL configuration for the comment app."""

from django.urls import path

from . import views

app_name = "comment"

urlpatterns = [
    path("", views.CommentListView.as_view(), name="comment_list"),
    path("create/", views.CommentCreateView.as_view(), name="comment_create"),
    path("<int:pk>/", views.comment_detail, name="comment_detail"),
    path("<int:pk>/edit/", views.CommentUpdateView.as_view(), name="comment_update"),
    path("<int:pk>/delete/", views.CommentDeleteView.as_view(), name="comment_delete"),
    path("post-comment/<int:book_id>/", views.post_comment, name="post_comment"),
]
