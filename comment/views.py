from django.shortcuts import render
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .forms import CommentForm
from . models import Comment
from book.models import Book,Category,Publisher,UserActivity,Profile,Member,BorrowRecord
from django.http import HttpResponse



@login_required(login_url='login')
def post_comment(request, book_id):
    book = get_object_or_404(Book, id=book_id)

    if request.method == 'POST':
        comment_form = CommentForm(request.POST)
        if comment_form.is_valid():
            new_comment = comment_form.save(commit=False)
            new_comment.book = book
            new_comment.user = request.user
            new_comment.save()
            return redirect('book_detail', pk=book_id)
        else:
            return HttpResponse("Error in form, please rewrite")
    # 处理错误请求
    else:
        return HttpResponse("Comment only accept POST request")