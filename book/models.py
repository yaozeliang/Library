from django.db import models
from django.contrib.auth.models import AbstractUser
from django.dispatch import receiver
from django.db.models.signals import post_save
from django.conf import settings
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from phonenumber_field.modelfields import PhoneNumberField


BOOK_STATUS =(
    (0, "On loan"),
    (1, "In Stock"),
)

FLOOR =(
    (1, "1st"),
    (2, "2nd"),
    (3, "3rd"),
)

OPERATION_TYPE =(
    ("success", "Create"),
    ("warning","Update"),
    ("danger","Delete")
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
    # created_at = models.DateTimeField(auto_now_add=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_by=models.CharField(max_length=20,default='yaozeliang')
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    def get_absolute_url(self): 
        return reverse('publisher_list')

class Book(models.Model):
    author = models.CharField("Author",max_length=20)
    title = models.CharField('Title',max_length=100)
    description = models.TextField()
    created = models.DateTimeField('Created Time',default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    total_borrow_times = models.PositiveIntegerField(default=0)
    quantity = models.PositiveIntegerField(default=10)
    category = models.ForeignKey(
        Category,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='category'
    )

    publisher=models.ForeignKey(
        Publisher,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='publisher'
    )

    status=models.IntegerField(choices=BOOK_STATUS,default=1)
    floor_number=models.IntegerField(choices=FLOOR,default=1)
    bookshelf_number=models.CharField('Bookshelf Number',max_length=10,default='0001')
    updated_by=models.CharField(max_length=20,default='yaozeliang')

    def get_absolute_url(self): 
        return reverse('book_list')
    
    def __str__(self):
        return self.title


class UserActivity(models.Model):
    created_by=models.CharField(default="",max_length=20)
    created_at =models.DateTimeField(auto_now_add=True)
    operation_type=models.CharField(choices=OPERATION_TYPE,default="success",max_length=20)
    target_model = models.CharField(default="",max_length=20)
    detail = models.CharField(default="",max_length=50)

    def get_absolute_url(self): 
        return reverse('user_activity_list')

class Member(models.Model):
    name = models.CharField(max_length=50, blank=False)
    age = models.PositiveIntegerField(default=0)
    city = models.CharField(max_length=50, blank=False)
    email = models.EmailField(max_length=50,blank=True)
    phone = PhoneNumberField()