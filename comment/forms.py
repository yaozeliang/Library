"""Comment forms for the Library Management System."""

from django import forms

from .models import Comment


class CommentForm(forms.ModelForm):
    """Form for creating and editing comments."""

    class Meta:
        """Meta class for CommentForm."""

        model = Comment
        fields = ["body"]
        widgets = {
            "body": forms.Textarea(attrs={"rows": 4, "class": "form-control"}),
        }
