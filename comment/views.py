"""Comment views for the Library Management System."""

from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from book.models import Book

from .forms import CommentForm
from .models import Comment


class CommentListView(ListView):
    """View for displaying a list of comments."""

    model = Comment
    template_name = "comment/comment_list.html"
    context_object_name = "comments"
    paginate_by = 10


class CommentCreateView(LoginRequiredMixin, CreateView):
    """View for creating new comments."""

    model = Comment
    form_class = CommentForm
    template_name = "comment/comment_form.html"
    success_url = reverse_lazy("comment_list")

    def form_valid(self, form):
        """Set the user before saving the form."""
        form.instance.user = self.request.user
        return super().form_valid(form)


class CommentUpdateView(LoginRequiredMixin, UpdateView):
    """View for updating existing comments."""

    model = Comment
    form_class = CommentForm
    template_name = "comment/comment_form.html"
    success_url = reverse_lazy("comment_list")

    def get_queryset(self):
        """Only allow users to edit their own comments."""
        return Comment.objects.filter(user=self.request.user)


class CommentDeleteView(LoginRequiredMixin, DeleteView):
    """View for deleting comments."""

    model = Comment
    template_name = "comment/comment_confirm_delete.html"
    success_url = reverse_lazy("comment_list")

    def get_queryset(self):
        """Only allow users to delete their own comments."""
        return Comment.objects.filter(user=self.request.user)


@login_required
def comment_detail(request, pk):
    """View for displaying comment details."""
    comment = get_object_or_404(Comment, pk=pk)
    return render(request, "comment/comment_detail.html", {"comment": comment})


@login_required
def post_comment(request, book_id):
    """Handle posting comments on books."""
    book = get_object_or_404(Book, id=book_id)

    if request.method == "POST":
        comment_form = CommentForm(request.POST)
        if comment_form.is_valid():
            new_comment = comment_form.save(commit=False)
            new_comment.book = book
            new_comment.user = request.user
            new_comment.save()
            return redirect("book_detail", pk=book_id)
        else:
            return HttpResponse("Error in form, please rewrite")
    # Handle non-POST requests
    else:
        return HttpResponse("Comment only accepts POST requests")