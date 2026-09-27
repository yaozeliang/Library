"""Book management forms for the Library Management System."""

from django import forms
from django_flatpickr.widgets import DatePickerInput

from .models import Book, BorrowRecord, Member, Profile, Publisher


class BookCreateEditForm(forms.ModelForm):
    """Form for creating and editing books."""

    class Meta:
        """Meta class for BookCreateEditForm."""

        model = Book
        fields = (
            "author",
            "title",
            "description",
            "quantity",
            "category",
            "publisher",
            "floor_number",
            "bookshelf_number",
        )


class PubCreateEditForm(forms.ModelForm):
    """Form for creating and editing publishers."""

    class Meta:
        """Meta class for PubCreateEditForm."""

        model = Publisher
        fields = (
            "name",
            "city",
            "contact",
        )
        # fields="__all__"


class MemberCreateEditForm(forms.ModelForm):
    """Form for creating and editing members."""

    class Meta:
        """Meta class for MemberCreateEditForm."""

        model = Member
        fields = (
            "name",
            "gender",
            "age",
            "email",
            "city",
            "phone_number",
        )


class ProfileForm(forms.ModelForm):
    """Form for editing user profiles."""

    class Meta:
        """Meta class for ProfileForm."""

        model = Profile
        fields = (
            "profile_pic",
            "bio",
            "phone_number",
            "email",
        )


class BorrowRecordCreateForm(forms.ModelForm):
    """Form for creating borrow records."""

    borrower = forms.CharField(
        label="Borrower",
        widget=forms.TextInput(attrs={"placeholder": "Search Member..."}),
    )

    book = forms.CharField(
        max_length=BorrowRecord._meta.get_field("book").max_length,
        help_text="type book name",
        widget=forms.TextInput(
            attrs={
                "placeholder": "Book title",
                "aria-label": "Book title",
                "class": "form-control",
            }
        ),
    )

    class Meta:
        """Meta class for BorrowRecordCreateForm."""

        model = BorrowRecord
        fields = ["borrower", "book", "quantity", "start_day", "end_day"]
        # widgets = {
        #     'start_day': DatePickerInput().start_of('event datetime'),
        #     'end_day': DatePickerInput().end_of('event datetime'),
        # }
        widgets = {
            "start_day": DatePickerInput(),
            "end_day": DatePickerInput(),
        }

    def clean(self):
        """Reject a zero quantity and a return date before the borrow date."""
        cleaned = super().clean()
        start_day = cleaned.get("start_day")
        end_day = cleaned.get("end_day")
        if start_day and end_day and end_day < start_day:
            self.add_error(
                "end_day", "Return date must be on or after the borrow date."
            )
        quantity = cleaned.get("quantity")
        if quantity is not None and quantity < 1:
            self.add_error("quantity", "Borrow at least one copy.")
        return cleaned
        # widgets = {'start_day': forms.DateTimeInput(attrs={'class': 'datepicker'}),
        #            'end_day': forms.DateTimeInput(attrs={'class': 'datepicker'})}

        # widgets = {
        #     'start_day': DateTimePickerInput(format='%Y-%m-%d'),
        #     'end_day': DateTimePickerInput(format='%Y-%m-%d'),
        # }


# from  django.forms.widgets import SelectDateWidget

# class BorrowRecordCreateForm(forms.ModelForm):

#     def __init__(self, *args, **kwargs):
#         super(BorrowRecordCreateForm, self).__init__(*args, **kwargs)
#         #Change date field's widget here
#         self.fields['start_day'].widget = SelectDateWidget()
#         self.fields['end_day'].widget = SelectDateWidget()

#     class Meta:
#         model = BorrowRecord
#         fields=['borrower','book','quantity','start_day','end_day']
