
from django.shortcuts import render,get_object_or_404,redirect
from  django.urls import  reverse_lazy,reverse
from django.views.decorators.csrf import csrf_protect
from django.views.generic import ListView,DetailView,DeleteView,View
from django.views.generic.edit import CreateView,UpdateView
from django.core.paginator import Paginator
# 引入 Q 对象
from django.db.models import Q

# Create your views here.
from django.http import HttpResponse,HttpResponseRedirect
from .models import Book,Category,Publisher
# import markdown
# 引入刚才定义的ArticlePostForm表单类

# 引入User模型
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied # new
from django.contrib.auth.mixins import LoginRequiredMixin 


from django.contrib.messages.views import SuccessMessageMixin
from django.core.files.storage import FileSystemStorage
from django.contrib.messages.views import messages
from django.views.decorators.csrf import csrf_exempt
from .forms import BookPostForm

class BookListView(LoginRequiredMixin,ListView):
    login_url = 'login'
    model=Book
    context_object_name = 'books'
    template_name = 'book/booklist.html'
    search_value=""
    order_field="id"

    def get_queryset(self):
        search =self.request.GET.get("search") 
        order_by=self.request.GET.get("orderby")

        if order_by:
            all_books = Book.objects.all().order_by(order_by)
            self.order_field=order_by
        else:
            all_books = Book.objects.all().order_by(self.order_field)

        if search:
            all_books = all_books.filter(
                Q(title__icontains=search)|Q(author__icontains=search)
            )
            self.search_value=search
        self.count_total = all_books.count()
        paginator = Paginator(all_books, 6)
        page = self.request.GET.get('page')
        books = paginator.get_page(page)
        return books

    def get_context_data(self, *args, **kwargs):
        context = super(BookListView, self).get_context_data(*args, **kwargs)
        context['count_total'] = self.count_total
        context['search'] = self.search_value
        context['order'] = self.order_field
        return context

class BookDetailView(LoginRequiredMixin,DetailView):
    model = Book
    context_object_name = 'book'
    template_name = 'book/book_detail.html'
    login_url = 'login'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context

class BookCreateView(LoginRequiredMixin,CreateView):
    model=Book
    login_url = 'login'
    fields=['title','author','description','category','publisher','quantity','floor_number','bookshelf_number'] 
    template_name='book/book_create.html'

    def post(self,request, *args, **kwargs):
        super(BookCreateView,self).post(request)
        new_book_name = request.POST['title']
        messages.success(request, f"New Book << {new_book_name} >> Added")
        return redirect('book_list')





class BookUpdateView(LoginRequiredMixin,UpdateView):
    model = Book
    login_url = 'login'
    # fields = ['title','avatar','category','tags','body']
    form_class=BookPostForm
    template_name = 'book/book_update.html'

    # def dispatch(self, request, *args, **kwargs):
    #     obj = self.get_object()
    #     if obj.author != self.request.user:
    #         return HttpResponse("Sorry, you don't have right to update")
    #         # raise PermissionDenied
    #     return super().dispatch(request, *args, **kwargs)




class BookDeleteView(LoginRequiredMixin,View):
    login_url = 'login'
    def get(self,request,*args,**kwargs):
        book_pk=kwargs["pk"]
        delete_book=Book.objects.get(pk=book_pk)
        messages.success(request, f"Book << {delete_book.title} >> Removed")
        delete_book.delete()
        return HttpResponseRedirect(reverse("book_list"))


class CategoryListView(LoginRequiredMixin,ListView):
    login_url = 'login'
    model=Category
    context_object_name = 'categories'
    template_name = 'book/categorylist.html'
    count_total = 0
    search_value = ''

    def get_queryset(self):
        search =self.request.GET.get("search")  
        order_by=self.request.GET.get("orderby","id")
        all_categories = Category.objects.all().order_by(order_by)
        if search:
            all_categories = all_categories.filter(
                Q(name__icontains=search)  
            )
        else:
            search = ''
        self.search_value=search
        self.count_total = all_categories.count()
        paginator = Paginator(all_categories, 6)
        page = self.request.GET.get('page')
        categories = paginator.get_page(page)
        return categories

    def get_context_data(self, *args, **kwargs):
        context = super(CategoryListView, self).get_context_data(*args, **kwargs)
        context['count_total'] = self.count_total
        context['search'] = self.search_value
        # context["all_table_fields"]=Category._meta.get_fields()
        # print(list(context["all_table_fields"]))
        return context

    # class CategoryCreateView(SuccessMessageMixin,CreateView):
    #     model=Category
    #     success_message="Category Added!"
    #     fields=['name']
    #     template_name='book/category_create.html'

class CategoryCreateView(LoginRequiredMixin,CreateView):
    login_url = 'login'
    model=Category
    fields=['name']
    template_name='book/category_create.html'


    def post(self,request, *args, **kwargs):
        super(CategoryCreateView,self).post(request)
        new_cat_name = request.POST['name']
        messages.success(request, f"Category << {new_cat_name} >> Added")
        return redirect('category_list')

# class CategoryDeleteView(SuccessMessageMixin,DeleteView):
#     model = Category
#     # success_message="Category Removed!"
#     # template_name='book/categorylist.html'
#     # http_method_names = ['POST']
#     success_url = reverse_lazy("category_list")
    

#     def dispatch(self, request, *args, **kwargs):
#         obj = self.get_object()
#         return super().dispatch(request, *args, **kwargs)

class CategoryDeleteView(LoginRequiredMixin,View):
    login_url = 'login'
    def get(self,request,*args,**kwargs):
        cat_pk=kwargs["pk"]
        delete_cat=Category.objects.get(pk=cat_pk)
        messages.success(request, f"Category << {delete_cat.name} >> Removed")
        delete_cat.delete()
        return HttpResponseRedirect(reverse("category_list"))





# Publisher 
class PublisherListView(LoginRequiredMixin,ListView):
    login_url = 'login'
    model=Publisher
    context_object_name = 'publishers'
    template_name = 'book/publisherlist.html'
    count_total = 0
    search_value = ''

    def get_queryset(self):
        search =self.request.GET.get("search")  
        order_by=self.request.GET.get("orderby","id")
        all_publishers = Publisher.objects.all().order_by(order_by)
        if search:
            all_publishers = all_publishers.filter(
                Q(name__icontains=search) | Q(city__icontains=search) | Q(contact__icontains=search)
            )
        else:
            search = ''
        self.search_value=search
        self.count_total = all_publishers.count()
        paginator = Paginator(all_publishers, 6)
        page = self.request.GET.get('page')
        publishers = paginator.get_page(page)
        return publishers

    def get_context_data(self, *args, **kwargs):
        context = super(PublisherListView, self).get_context_data(*args, **kwargs)
        context['count_total'] = self.count_total
        context['search'] = self.search_value
        # context["all_table_fields"]=Categories._meta.get_fields()
        return context

class PublisherCreateView(LoginRequiredMixin,CreateView):
    login_url = 'login'
    model=Publisher
    fields=['name','city','contact']
    # fields="__all__"
    template_name='book/publisher_create.html'


class PublisherDeleteView(LoginRequiredMixin,View):
    login_url = 'login'

    def get(self,request,*args,**kwargs):
        pub_pk=kwargs["pk"]
        delete_pub=Publisher.objects.get(pk=pub_pk)
        messages.success(request, f"Publisher << {delete_pub.name} >> Removed")
        delete_pub.delete()
        return HttpResponseRedirect(reverse("publisher_list"))