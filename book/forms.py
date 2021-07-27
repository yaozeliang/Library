from django import forms
from .models import Book,Publisher,Member


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
