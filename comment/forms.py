"""Comment forms for the Library Management System."""

from django import forms

from .models import Comment


class CommentForm(forms.ModelForm):
    """Form for creating and editing comments."""

    class Meta:
        """Meta class for CommentForm."""

        model = Comment
        fields = ["body"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # RichTextFormField replaces any Meta widget with CKEditorWidget.
        self.fields["body"].widget.attrs.update(
            {
                "rows": 4,
                "class": "form-control",
                "placeholder": "Comment",
                "aria-label": "Comment",
            }
        )
