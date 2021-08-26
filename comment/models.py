from django.db import models
from book.models import Book,Category,Publisher,UserActivity,Profile,Member,BorrowRecord
from ckeditor.fields import RichTextField
from django.contrib.auth.models import User


class Comment(models.Model):
    book = models.ForeignKey(
        Book,
        on_delete=models.CASCADE,
        related_name='comments'
    )
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='comments'
    )
    
    body = RichTextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('created_at',)

    def __str__(self):
        return self.body[:20]