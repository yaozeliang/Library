from django.urls import path
from . import views

app_name = 'comment'

urlpatterns = [
    path('post-comment/<int:book_id>/', views.post_comment, name='post_comment'),
]