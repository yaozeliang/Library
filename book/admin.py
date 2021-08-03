from django.contrib import admin

# Register your models here.
from.models import Category,Publisher,Profile,Member,BorrowRecord

from .forms import BorrowRecordCreateForm

# @admin.register(Member)
# class MemberAdmin(AjaxSelectAdmin):
#     form = BorrowRecordCreateForm

admin.site.register(Member)
admin.site.register(BorrowRecord)