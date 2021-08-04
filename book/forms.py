from django import forms
from .models import Book,Publisher,Member,Profile,BorrowRecord
from django.contrib.admin.widgets import AutocompleteSelect
from django.contrib import admin
from dal import autocomplete
from django.urls import reverse


class BookCreateEditForm(forms.ModelForm):
    class Meta:
        model = Book
        fields = ('author',
                  'title',
                  'description',
                  'quantity', 
                  'category',
                  'publisher',
                  'floor_number',
                  "bookshelf_number")


class PubCreateEditForm(forms.ModelForm):
    class Meta:
        model = Publisher
        fields = ('name',
                  'city',
                  'contact',
                  )
        # fields="__all__"

class MemberCreateEditForm(forms.ModelForm):
    class Meta:
        model = Member
        fields = ('name',
                  'gender',
                  'age',
                  'email',
                  'city', 
                  'phone_number',)


class ProfileForm(forms.ModelForm):

    
    class Meta:
        model = Profile
        fields = ( 'profile_pic',
                  'bio', 
                  'phone_number',
                  'email')


class BorrowRecordCreateForm(forms.ModelForm):

    borrower = forms.CharField(label='Borrrower', 
                    widget=forms.TextInput(attrs={'placeholder': 'Search Member...'}))
    
    book = forms.CharField(help_text='type book name')

    class Meta:
        model = BorrowRecord
        fields=['borrower','book','quantity','start_day','end_day']

        # widgets = {
        #     'start_day': DateTimePickerInput(format='%Y-%m-%d'),
        #     'end_day': DateTimePickerInput(format='%Y-%m-%d'),
        # }