from django.db import models
from django.contrib.auth.models import AbstractUser
from django.dispatch import receiver
from django.db.models.signals import post_save
from django.conf import settings
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
# from phonenumber_field.modelfields import PhoneNumberField
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import uuid
from PIL import Image


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
    ("danger","Delete"),
    ("info",'Close')
)

GENDER=(
    ("m","Male"),
    ("f","Female"),
)

BORROW_RECORD_STATUS=(
    (0,'Open'),
    (1,'Closed')
)

class Category(models.Model):
    
    name = models.CharField(max_length=50, blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.name
    def get_absolute_url(self): 
        return reverse('category_list')

    # class Meta:
    #     db_table='category'

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
    created_at = models.DateTimeField('Created Time',default=timezone.now)
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
    age = models.PositiveIntegerField(default=20)
    gender = models.CharField(max_length=10,choices=GENDER,default='m')

    city = models.CharField(max_length=20, blank=False)
    email = models.EmailField(max_length=50,blank=True)
    phone_number = models.CharField(max_length=30,blank=False)

    created_at= models.DateTimeField(default=timezone.now)
    created_by = models.CharField(max_length=20,default="")
    updated_by = models.CharField(max_length=20,default="")
    updated_at = models.DateTimeField(auto_now=True)

    card_id = models.UUIDField(unique=True, default=uuid.uuid4, editable=False)
    card_number = models.CharField(max_length=8,default="")
    expired_at = models.DateTimeField(default=timezone.now)

    def get_absolute_url(self): 
        return reverse('member_list')
    
    def save(self, *args, **kwargs):
        self.card_number = str(self.card_id)[:8]
        self.expired_at = timezone.now()+relativedelta(years=1)
        return super(Member, self).save(*args, **kwargs)

    def __str__(self):
        return self.name


# UserProfile
class Profile(models.Model):
    user = models.OneToOneField(User,null=True,on_delete=models.CASCADE)
    bio = models.TextField()
    profile_pic = models.ImageField(upload_to="profile/%Y%m%d/", blank=True,null=True)
    phone_number = models.CharField(max_length=30,blank=True)
    email = models.EmailField(max_length=50,blank=True)

    def save(self, *args, **kwargs):
        # 调用原有的 save() 的功能
        profile = super(Profile, self).save(*args, **kwargs)

        # 固定宽度缩放图片大小
        if self.profile_pic and not kwargs.get('update_fields'):
            image = Image.open(self.profile_pic)
            (x, y) = image.size
            new_x = 400
            new_y = int(new_x * (y / x))
            resized_image = image.resize((new_x, new_y), Image.ANTIALIAS)
            resized_image.save(self.profile_pic.path)

        return profile

    def __str__(self):
        return str(self.user)

    def get_absolute_url(self): 
        return reverse('home')


# Borrow Record

class BorrowRecord(models.Model):

    borrower = models.CharField(blank=False,max_length=20)
    borrower_card = models.CharField(max_length=8,blank=True)
    borrower_email = models.EmailField(max_length=50,blank=True)
    borrower_phone_number  = models.CharField(max_length=30,blank=True)
    book = models.CharField(blank=False,max_length=20)
    quantity = models.PositiveIntegerField(default=1)

    start_day = models.DateTimeField(default=timezone.now)
    end_day = models.DateTimeField(default=timezone.now()+timedelta(days=7))
    periode = models.PositiveIntegerField(default=0)

    open_or_close = models.IntegerField(choices=BORROW_RECORD_STATUS,default=0)
    delay_days = models.IntegerField(default=0)
    final_status = models.CharField(max_length=10,default="Unknown")

    created_at= models.DateTimeField(default=timezone.now)
    created_by = models.CharField(max_length=20,blank=True)
    closed_by = models.CharField(max_length=20,default="")
    closed_at = models.DateTimeField(auto_now=True)

    @property
    def return_status(self):
        if self.final_status!="Unknown":
            return self.final_status
        elif self.end_day.replace(tzinfo=None) > datetime.now()-timedelta(hours=24):
            return 'On time'
        else:
            return 'Delayed'

    @property
    def get_delay_number_days(self):
        
        if self.delay_days!=0:
            return self.delay_days
        elif self.return_status=='Delayed':
            return (datetime.now()-self.end_day.replace(tzinfo=None)).days
        else:
            return 0


    def get_absolute_url(self): 
        return reverse('record_list')

    def __str__(self):
        return self.borrower+"->"+self.book
    
    def save(self, *args, **kwargs):
        # profile = super(Profile, self).save(*args, **kwargs)
        self.periode =(self.end_day - self.start_day).days+1
        return super(BorrowRecord, self).save(*args, **kwargs)







