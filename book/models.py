from django.db import models
from django.contrib.auth.models import AbstractUser
from django.dispatch import receiver
from django.db.models.signals import post_save
from django.conf import settings
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone

BOOK_STATUS =(
    (0, "On loan"),
    (1, "In Stock"),
)

class Category(models.Model):
    
    name = models.CharField(max_length=50, blank=True)
    created = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.name
    def get_absolute_url(self): 
        return reverse('category_list')

class Publisher(models.Model):
    
    name = models.CharField(max_length=50, blank=True)
    city = models.CharField(max_length=50, blank=True)
    contact = models.EmailField(max_length=50,blank=True)
    created = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.name

    def get_absolute_url(self): 
        return reverse('publisher_list')

class Book(models.Model):
    author = models.CharField("Author",max_length=20)
    title = models.CharField('Title',max_length=100)
    description = models.TextField()
    created = models.DateTimeField('Created Time',default=timezone.now)
    updated = models.DateTimeField('Modified Time',auto_now=True)
    total_borrow_times = models.PositiveIntegerField(default=0)
    quantity = models.PositiveIntegerField(default=10)
    category = models.ForeignKey(
        Category,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name='category'
    )

    publisher=models.ForeignKey(
        Publisher,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name='publisher'
    )

    status=models.IntegerField(choices=BOOK_STATUS,default=1)

    def get_absolute_url(self): 
        return reverse('book_list')
    
    def __str__(self):
        return self.title