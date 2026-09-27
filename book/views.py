import logging
from datetime import date

import pandas as pd
from django.apps import apps
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import Group, User
from django.contrib.messages.views import messages
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Count, F, Q, Sum
from django.db.models.functions import TruncMonth
from django.http import Http404, HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.generic import DetailView, ListView, TemplateView, View
from django.views.generic.edit import CreateView, UpdateView

from comment.forms import CommentForm
from comment.models import Comment

# from .utils import get_n_days_ago,create_clean_dir,change_col_format
from util.useful import get_n_days_ago

from .forms import (
    BookCreateEditForm,
    BorrowRecordCreateForm,
    MemberCreateEditForm,
    ProfileForm,
    PubCreateEditForm,
)
from .groups_permissions import (
    SuperUserRequiredMixin,
    allowed_groups,
    check_user_group,
    user_groups,
)
from .models import (
    Book,
    BorrowRecord,
    Category,
    Member,
    Profile,
    Publisher,
    UserActivity,
)
from .notification import send_notification
from .pagination import CATALOG_PAGE_SIZE, redirect_for_page

logger = logging.getLogger(__name__)


TODAY = get_n_days_ago(0, "%Y%m%d")
PAGINATOR_NUMBER = CATALOG_PAGE_SIZE


def borrow_record_listing_order():
    """Open loans first, then the newest borrow, then the highest id.

    ``order_by("-closed_at")`` puts NULL close dates first on Postgres and
    leaves those open rows in an arbitrary order. Spell the NULL placement
    out and break ties with the borrow record's created timestamp, then id.
    """
    return (
        F("closed_at").desc(nulls_first=True),
        F("created_at").desc(),
        "-id",
    )


def apply_ordering(queryset, requested, default):
    """Order by a real column. An unknown ``orderby`` falls back to ``default``.

    Passing the query string straight to ``order_by`` raised FieldError and
    the list view answered 500. The borrow-record default ``-closed_at``
    uses ``borrow_record_listing_order`` so open loans stay first in a
    stable order. The home page "Recent Closed" list does not use this
    helper; it only shows closed loans, newest close first.
    """
    candidate = (requested or "").strip() or default
    raw = candidate[1:] if candidate.startswith("-") else candidate
    field_names = {field.name for field in queryset.model._meta.fields}
    if raw not in field_names:
        candidate = default
    if candidate == "-closed_at" and queryset.model is BorrowRecord:
        return queryset.order_by(*borrow_record_listing_order()), candidate
    return queryset.order_by(candidate), candidate


class OrderedPageMixin:
    """Shared search, sort, and redirected pagination for catalog list views.

    Subclasses implement ``listing()`` and return the filtered queryset
    before it is sliced. ``get`` sends a bad ``?page=`` back as a 302
    before the template renders.
    """

    default_order = "-id"
    search_value = ""
    order_field = ""
    count_total = 0

    def order_queryset(self, queryset):
        search = self.request.GET.get("search") or ""
        self.search_value = search
        ordered, self.order_field = apply_ordering(
            queryset, self.request.GET.get("orderby"), self.default_order
        )
        return ordered, search

    def listing(self):
        raise NotImplementedError

    def get(self, request, *args, **kwargs):
        redirect_to = redirect_for_page(
            request, self.listing(), per_page=PAGINATOR_NUMBER
        )
        if redirect_to is not None:
            return redirect_to
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        return self.page_queryset(self.listing())

    def page_queryset(self, queryset):
        self.count_total = queryset.count()
        # ``get`` already rejected a page that is not in range, so the
        # remaining value is a real page or absent (page 1).
        return Paginator(queryset, PAGINATOR_NUMBER).get_page(
            self.request.GET.get("page")
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["count_total"] = self.count_total
        context["search"] = self.search_value
        context["orderby"] = self.order_field
        context["objects"] = self.object_list
        return context


allowed_models = [
    "Category",
    "Publisher",
    "Book",
    "Member",
    "UserActivity",
    "BorrowRecord",
]


# HomePage


def _avatar_url(username):
    """Return a profile picture URL, or '' when the user has none.

    An empty ImageField has no file; reading ``.url`` raises ValueError.
    """
    profile = Profile.objects.filter(user__username=username).first()
    if profile is None or not profile.profile_pic:
        return ""
    return profile.profile_pic.url


class HomeView(LoginRequiredMixin, TemplateView):
    login_url = "login"
    template_name = "index.html"
    context = {}

    # users = User.objects.all()
    # for user in users:
    #     print(user.get_username(),user.is_superuser)

    def get(self, request, *args, **kwargs):
        book_count = Book.objects.aggregate(Sum("quantity"))["quantity__sum"]

        data_count = {
            "book": book_count,
            "member": Member.objects.all().count(),
            "category": Category.objects.all().count(),
            "publisher": Publisher.objects.all().count(),
        }

        user_activities = UserActivity.objects.order_by("-created_at")[:5]
        user_avatar = {
            activity.created_by: _avatar_url(activity.created_by)
            for activity in user_activities
        }
        short_inventory = Book.objects.order_by("quantity")[:5]

        current_week = date.today().isocalendar()[1]
        new_members = Member.objects.order_by("-created_at")[:5]
        new_members_thisweek = Member.objects.filter(
            created_at__week=current_week
        ).count()
        lent_books_thisweek = BorrowRecord.objects.filter(
            created_at__week=current_week
        ).count()

        books_return_thisweek = BorrowRecord.objects.filter(end_day__week=current_week)
        number_books_return_thisweek = books_return_thisweek.count()
        # Closed loans only, newest close first. Open loans are excluded, so
        # this does not use the record-list NULLS FIRST ordering.
        new_closed_records = BorrowRecord.objects.filter(
            open_or_close=1, closed_at__isnull=False
        ).order_by("-closed_at")[:5]

        self.context["data_count"] = data_count
        self.context["recent_user_activities"] = user_activities
        self.context["user_avatar"] = user_avatar
        self.context["short_inventory"] = short_inventory
        self.context["new_members"] = new_members
        self.context["new_members_thisweek"] = new_members_thisweek
        self.context["lent_books_thisweek"] = lent_books_thisweek
        self.context["books_return_thisweek"] = books_return_thisweek
        self.context["number_books_return_thisweek"] = number_books_return_thisweek
        self.context["new_closed_records"] = new_closed_records

        return render(request, self.template_name, self.context)


# Global Serch
@login_required(login_url="login")
def global_serach(request):
    # GET and a missing field yield None. icontains rejects None and 500s.
    search_value = request.POST.get("global_search") or ""
    if search_value == "":
        return HttpResponseRedirect("/")

    r_category = Category.objects.filter(Q(name__icontains=search_value))
    r_publisher = Publisher.objects.filter(
        Q(name__icontains=search_value) | Q(contact__icontains=search_value)
    )
    r_book = Book.objects.filter(
        Q(author__icontains=search_value) | Q(title__icontains=search_value)
    )
    r_member = Member.objects.filter(
        Q(name__icontains=search_value)
        | Q(card_number__icontains=search_value)
        | Q(phone_number__icontains=search_value)
    )
    r_borrow = BorrowRecord.objects.filter(
        Q(borrower__icontains=search_value)
        | Q(borrower_card__icontains=search_value)
        | Q(book__icontains=search_value)
    )

    context = {
        "categories": r_category,
        "publishers": r_publisher,
        "books": r_book,
        "members": r_member,
        "records": r_borrow,
    }

    return render(request, "book/global_search.html", context=context)


# Chart
class ChartView(LoginRequiredMixin, TemplateView):
    template_name = "book/charts.html"
    login_url = "login"
    context = {}

    def get(self, request, *args, **kwargs):
        top_5_book = Book.objects.order_by("-quantity")[:5].values_list(
            "title", "quantity"
        )
        top_5_book_titles = [b[0] for b in top_5_book]
        top_5_book__quantities = [b[1] for b in top_5_book]
        # print(top_5_book_titles,top_5_book__quantities)

        top_borrow = Book.objects.order_by("-total_borrow_times")[:5].values_list(
            "title", "total_borrow_times"
        )
        top_borrow_titles = [b[0] for b in top_borrow]
        top_borrow_times = [b[1] for b in top_borrow]

        r_open = BorrowRecord.objects.filter(open_or_close=0).count()
        r_close = BorrowRecord.objects.filter(open_or_close=1).count()

        m = (
            Member.objects.annotate(month=TruncMonth("created_at"))
            .values("month")
            .annotate(c=Count("id"))
        )
        months_member = [e["month"].strftime("%m/%Y") for e in m]
        count_monthly_member = [e["c"] for e in m]

        self.context["top_5_book_titles"] = top_5_book_titles
        self.context["top_5_book__quantities"] = top_5_book__quantities
        self.context["top_borrow_titles"] = top_borrow_titles
        self.context["top_borrow_times"] = top_borrow_times
        self.context["r_open"] = r_open
        self.context["r_close"] = r_close
        self.context["months_member"] = months_member
        self.context["count_monthly_member"] = count_monthly_member

        return render(request, self.template_name, self.context)


# Book
class BookListView(LoginRequiredMixin, OrderedPageMixin, ListView):
    login_url = "login"
    model = Book
    context_object_name = "books"
    template_name = "book/book_list.html"
    default_order = "-updated_at"

    def listing(self):
        books, search = self.order_queryset(Book.objects.all())
        if search:
            books = books.filter(
                Q(title__icontains=search) | Q(author__icontains=search)
            )
        return books


class BookDetailView(LoginRequiredMixin, DetailView):
    model = Book
    context_object_name = "book"
    template_name = "book/book_detail.html"
    login_url = "login"
    comment_form = CommentForm()

    # def get_object(self, queryset=None):
    #     obj = super(BookDetailView, self).get_object(queryset=queryset)
    #     return obj

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        current_book_name = self.get_object().title
        logger.info(f"Book  <<{current_book_name}>> retrieved from db")
        comments = Comment.objects.filter(book=self.get_object().id)
        related_records = BorrowRecord.objects.filter(book=current_book_name)
        context["related_records"] = related_records
        context["comments"] = comments
        context["comment_form"] = self.comment_form
        return context


class BookCreateView(LoginRequiredMixin, CreateView):
    model = Book
    login_url = "login"
    form_class = BookCreateEditForm
    template_name = "book/book_create.html"
    success_url = reverse_lazy("book_list")

    def form_valid(self, form):
        response = super().form_valid(form)
        new_book_name = form.cleaned_data["title"]
        messages.success(self.request, f"New Book << {new_book_name} >> Added")
        UserActivity.objects.create(
            created_by=self.request.user.username,
            target_model=self.model.__name__,
            detail=f"Create {self.model.__name__} << {new_book_name} >>",
        )
        return response


class BookUpdateView(LoginRequiredMixin, UpdateView):
    model = Book
    login_url = "login"
    form_class = BookCreateEditForm
    template_name = "book/book_update.html"

    def form_valid(self, form):
        form.instance.updated_by = self.request.user.username
        title = form.cleaned_data["title"]
        messages.warning(self.request, f"Update << {title} >> success")
        UserActivity.objects.create(
            created_by=self.request.user.username,
            operation_type="warning",
            target_model=self.model.__name__,
            detail=f"Update {self.model.__name__} << {title} >>",
        )
        return super().form_valid(form)


class BookDeleteView(LoginRequiredMixin, View):
    login_url = "login"

    def post(self, request, *args, **kwargs):
        book_pk = kwargs["pk"]
        delete_book = get_object_or_404(Book, pk=book_pk)
        model_name = delete_book.__class__.__name__
        messages.error(request, f"Book << {delete_book.title} >> Removed")
        delete_book.delete()
        UserActivity.objects.create(
            created_by=self.request.user.username,
            operation_type="danger",
            target_model=model_name,
            detail=f"Delete {model_name} << {delete_book.title} >>",
        )
        return HttpResponseRedirect(reverse("book_list"))


# Categorty


class CategoryListView(LoginRequiredMixin, OrderedPageMixin, ListView):
    login_url = "login"
    model = Category
    context_object_name = "categories"
    template_name = "book/category_list.html"
    default_order = "-created_at"

    def listing(self):
        categories, search = self.order_queryset(Category.objects.all())
        if search:
            categories = categories.filter(Q(name__icontains=search))
        return categories


class CategoryCreateView(LoginRequiredMixin, CreateView):
    login_url = "login"
    model = Category
    fields = ["name"]
    template_name = "book/category_create.html"
    success_url = reverse_lazy("category_list")

    def form_valid(self, form):
        new_cat = form.save(commit=False)
        new_cat.save()
        send_notification(
            self.request.user, new_cat, verb=f"Add New Category << {new_cat.name} >>"
        )
        logger.info(f"{self.request.user} created Category {new_cat.name}")
        UserActivity.objects.create(
            created_by=self.request.user.username,
            target_model=self.model.__name__,
            detail=f"Create {self.model.__name__} << {new_cat.name} >>",
        )
        return super(CategoryCreateView, self).form_valid(form)


class CategoryDeleteView(LoginRequiredMixin, View):
    login_url = "login"

    def post(self, request, *args, **kwargs):
        cat_pk = kwargs["pk"]
        delete_cat = get_object_or_404(Category, pk=cat_pk)
        model_name = delete_cat.__class__.__name__
        messages.error(request, f"Category << {delete_cat.name} >> Removed")
        delete_cat.delete()
        send_notification(
            self.request.user,
            delete_cat,
            verb=f"Delete Category << {delete_cat.name} >>",
        )
        UserActivity.objects.create(
            created_by=self.request.user.username,
            operation_type="danger",
            target_model=model_name,
            detail=f"Delete {model_name} << {delete_cat.name} >>",
        )

        logger.info(f"{self.request.user} delete Category {delete_cat.name}")

        return HttpResponseRedirect(reverse("category_list"))


# Publisher


class PublisherListView(LoginRequiredMixin, OrderedPageMixin, ListView):
    login_url = "login"
    model = Publisher
    context_object_name = "publishers"
    template_name = "book/publisher_list.html"
    default_order = "-created_at"

    def listing(self):
        publishers, search = self.order_queryset(Publisher.objects.all())
        if search:
            publishers = publishers.filter(
                Q(name__icontains=search)
                | Q(city__icontains=search)
                | Q(contact__icontains=search)
            )
        return publishers


class PublisherCreateView(LoginRequiredMixin, CreateView):
    model = Publisher
    login_url = "login"
    form_class = PubCreateEditForm
    template_name = "book/publisher_create.html"
    success_url = reverse_lazy("publisher_list")

    def form_valid(self, form):
        new_pub = form.save(commit=False)
        new_pub.save()
        messages.success(self.request, f"New Publisher << {new_pub.name} >> Added")
        send_notification(
            self.request.user, new_pub, verb=f"Add New Publisher << {new_pub.name} >>"
        )
        logger.info(f"{self.request.user} created Publisher {new_pub.name}")

        UserActivity.objects.create(
            created_by=self.request.user.username,
            target_model=self.model.__name__,
            detail=f"Create {self.model.__name__} << {new_pub.name} >>",
        )
        return super(PublisherCreateView, self).form_valid(form)

    # def post(self,request, *args, **kwargs):
    #     super(PublisherCreateView,self).post(request)
    #     new_publisher_name = request.POST['name']
    #     messages.success(request, f"New Publisher << {new_publisher_name} >> Added")
    #     UserActivity.objects.create(created_by=self.request.user.username,
    #                                 target_model=self.model.__name__,
    #                                 detail =f"Create {self.model.__name__} << {new_publisher_name} >>")
    #     return redirect('publisher_list')


class PublisherUpdateView(LoginRequiredMixin, UpdateView):
    model = Publisher
    login_url = "login"
    form_class = PubCreateEditForm
    template_name = "book/publisher_update.html"

    def form_valid(self, form):
        form.instance.updated_by = self.request.user.username
        title = form.cleaned_data["name"]
        messages.warning(self.request, f"Update << {title} >> success")
        UserActivity.objects.create(
            created_by=self.request.user.username,
            operation_type="warning",
            target_model=self.model.__name__,
            detail=f"Update {self.model.__name__} << {title} >>",
        )
        return super().form_valid(form)


class PublisherDeleteView(LoginRequiredMixin, View):
    login_url = "login"

    def post(self, request, *args, **kwargs):
        pub_pk = kwargs["pk"]
        delete_pub = get_object_or_404(Publisher, pk=pub_pk)
        model_name = delete_pub.__class__.__name__
        messages.error(request, f"Publisher << {delete_pub.name} >> Removed")
        delete_pub.delete()
        send_notification(
            self.request.user,
            delete_pub,
            verb=f"Delete Publisher << {delete_pub.name} >>",
        )
        logger.info(f"{self.request.user} delete Publisher {delete_pub.name}")
        UserActivity.objects.create(
            created_by=self.request.user.username,
            operation_type="danger",
            target_model=model_name,
            detail=f"Delete {model_name} << {delete_pub.name} >>",
        )
        return HttpResponseRedirect(reverse("publisher_list"))


# User Logs
# @method_decorator(user_passes_test(lambda u: u.has_perm("book.view_useractivity")), name='dispatch')
@method_decorator(allowed_groups(group_name=["logs"]), name="dispatch")
class ActivityListView(LoginRequiredMixin, ListView):
    login_url = "login"
    model = UserActivity
    context_object_name = "activities"
    template_name = "book/user_activity_list.html"
    count_total = 0
    search_value = ""
    created_by = ""
    order_field = "-created_at"

    # def dispatch(self, *args, **kwargs):
    #     return super(ActivityListView, self).dispatch(*args, **kwargs)

    def listing(self):
        search = self.request.GET.get("search") or ""
        filter_user = self.request.GET.get("created_by") or ""
        self.search_value = search
        self.created_by = filter_user

        all_activities, self.order_field = apply_ordering(
            UserActivity.objects.all(),
            self.request.GET.get("orderby"),
            "-created_at",
        )

        if filter_user:
            all_activities = all_activities.filter(created_by=filter_user)

        if search:
            all_activities = all_activities.filter(Q(target_model__icontains=search))
        return all_activities

    def get(self, request, *args, **kwargs):
        redirect_to = redirect_for_page(
            request, self.listing(), per_page=PAGINATOR_NUMBER
        )
        if redirect_to is not None:
            return redirect_to
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        all_activities = self.listing()
        self.count_total = all_activities.count()
        return Paginator(all_activities, PAGINATOR_NUMBER).get_page(
            self.request.GET.get("page")
        )

    def get_context_data(self, *args, **kwargs):
        context = super(ActivityListView, self).get_context_data(*args, **kwargs)
        context["count_total"] = self.count_total
        context["search"] = self.search_value
        context["user_list"] = list(
            User.objects.values_list("username", flat=True)
        )
        context["created_by"] = self.created_by
        return context


# @method_decorator(user_passes_test(lambda u: u.has_perm("book.delete_useractivity")), name='dispatch')
@method_decorator(allowed_groups(group_name=["logs"]), name="dispatch")
class ActivityDeleteView(LoginRequiredMixin, View):
    login_url = "login"

    def post(self, request, *args, **kwargs):
        log_pk = kwargs["pk"]
        delete_log = get_object_or_404(UserActivity, pk=log_pk)
        messages.error(request, "Activity Removed")
        delete_log.delete()

        return HttpResponseRedirect(reverse("user_activity_list"))


# Membership
class MemberListView(LoginRequiredMixin, OrderedPageMixin, ListView):
    login_url = "login"
    model = Member
    context_object_name = "members"
    template_name = "book/member_list.html"
    default_order = "-updated_at"

    def listing(self):
        members, search = self.order_queryset(Member.objects.all())
        if search:
            members = members.filter(
                Q(name__icontains=search) | Q(card_number__icontains=search)
            )
        return members


class MemberCreateView(LoginRequiredMixin, CreateView):
    model = Member
    login_url = "login"
    form_class = MemberCreateEditForm
    template_name = "book/member_create.html"

    def form_valid(self, form):
        self.object = form.save()
        self.object.created_by = self.request.user.username
        self.object.save(update_fields=["created_by"])
        send_notification(
            self.request.user, self.object, f"Add new memeber {self.object.name}"
        )
        messages.success(
            self.request, f"New Member << {self.object.name} >> Added"
        )
        UserActivity.objects.create(
            created_by=self.request.user.username,
            target_model=self.model.__name__,
            detail=f"Create {self.model.__name__} << {self.object.name} >>",
        )
        return HttpResponseRedirect(self.get_success_url())

    # def form_valid(self, form):
    #     response = super(CourseCreate, self).form_valid(form)
    #     # do something with self.object
    #     return response


class MemberUpdateView(LoginRequiredMixin, UpdateView):
    model = Member
    login_url = "login"
    form_class = MemberCreateEditForm
    template_name = "book/member_update.html"

    def form_valid(self, form):
        form.instance.updated_by = self.request.user.username
        member_name = form.cleaned_data["name"]
        messages.warning(self.request, f"Update << {member_name} >> success")
        UserActivity.objects.create(
            created_by=self.request.user.username,
            operation_type="warning",
            target_model=self.model.__name__,
            detail=f"Update {self.model.__name__} << {member_name} >>",
        )
        return super().form_valid(form)


class MemberDeleteView(LoginRequiredMixin, View):
    login_url = "login"

    def post(self, request, *args, **kwargs):
        member_pk = kwargs["pk"]
        delete_member = get_object_or_404(Member, pk=member_pk)
        model_name = delete_member.__class__.__name__
        messages.error(request, f"Member << {delete_member.name} >> Removed")
        delete_member.delete()
        send_notification(
            self.request.user, delete_member, f"Delete member {delete_member.name} "
        )

        UserActivity.objects.create(
            created_by=self.request.user.username,
            operation_type="danger",
            target_model=model_name,
            detail=f"Delete {model_name} << {delete_member.name} >>",
        )
        return HttpResponseRedirect(reverse("member_list"))


class MemberDetailView(LoginRequiredMixin, DetailView):
    model = Member
    context_object_name = "member"
    template_name = "book/member_detail.html"
    login_url = "login"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        current_member_name = self.get_object().name
        related_records = BorrowRecord.objects.filter(borrower=current_member_name)
        context["related_records"] = related_records
        context["card_number"] = str(self.get_object().card_id)[:8]
        return context


# Profile View


class ProfileDetailView(LoginRequiredMixin, DetailView):
    model = Profile
    context_object_name = "profile"
    template_name = "profile/profile_detail.html"
    login_url = "login"

    def get_context_data(self, *args, **kwargs):
        current_user = get_object_or_404(Profile, pk=self.kwargs["pk"])
        # current_user= Profile.get(pk=kwargs['pk'])
        context = super(ProfileDetailView, self).get_context_data(*args, **kwargs)
        context["current_user"] = current_user
        return context


class ProfileCreateView(LoginRequiredMixin, CreateView):
    model = Profile
    template_name = "profile/profile_create.html"
    login_url = "login"
    form_class = ProfileForm

    def dispatch(self, request, *args, **kwargs):
        # A user already has a OneToOne profile (the signup signal creates it).
        # Posting the create form again raises IntegrityError.
        if request.user.is_authenticated:
            existing = Profile.objects.filter(user=request.user).first()
            if existing is not None:
                return redirect("profile_update", pk=existing.pk)
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form) -> HttpResponse:
        form.instance.user = self.request.user
        return super().form_valid(form)


class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    model = Profile
    login_url = "login"
    form_class = ProfileForm
    template_name = "profile/profile_update.html"

    def get_queryset(self):
        """Limit updates to the signed-in user's own profile."""
        return Profile.objects.filter(user=self.request.user)


# Borrow Records


class BorrowRecordCreateView(LoginRequiredMixin, CreateView):
    model = BorrowRecord
    template_name = "borrow_records/create.html"
    form_class = BorrowRecordCreateForm
    login_url = "login"

    def get_form(self):
        form = super().get_form()
        return form

    def form_valid(self, form):
        borrower_name = form.cleaned_data["borrower"]
        book_title = form.cleaned_data["book"]
        quantity = form.cleaned_data["quantity"]

        try:
            selected_member = Member.objects.get(name=borrower_name)
        except Member.DoesNotExist:
            form.add_error("borrower", "Select a member that exists.")
            return self.form_invalid(form)

        matches = Book.objects.filter(title=book_title)
        if not matches.exists():
            form.add_error("book", "Select a book that exists.")
            return self.form_invalid(form)
        if matches.count() > 1:
            form.add_error("book", "More than one book has that title.")
            return self.form_invalid(form)
        selected_book = matches.get()

        if quantity > selected_book.quantity:
            form.add_error("quantity", "Not enough copies in stock.")
            return self.form_invalid(form)

        form.instance.borrower_card = selected_member.card_number
        form.instance.borrower_email = selected_member.email
        form.instance.borrower_phone_number = selected_member.phone_number
        form.instance.created_by = self.request.user.username

        with transaction.atomic():
            self.object = form.save()
            selected_book.status = 0
            selected_book.total_borrow_times += 1
            selected_book.quantity -= quantity
            selected_book.save()

        messages.success(
            self.request, f" '{selected_member.name}' borrowed <<{selected_book.title}>>"
        )
        UserActivity.objects.create(
            created_by=self.request.user.username,
            target_model=self.model.__name__,
            detail=f" '{selected_member.name}' borrowed <<{selected_book.title}>>",
        )
        return HttpResponseRedirect(reverse("record_list"))

    # def post(self,request, *args, **kwargs):

    #     return redirect('record_list')


def _autocomplete_json(queryset, field, term):
    """JSON array of matching names for jQuery UI autocomplete.

    ``HttpRequest.is_ajax()`` was removed in Django 4, so these views crashed
    with AttributeError on every request (and left ``data`` unset otherwise).
    """
    results = list(
        queryset.filter(**{f"{field}__icontains": term}).values_list(field, flat=True)
    )
    return JsonResponse(results, safe=False)


@login_required(login_url="login")
def auto_member(request):
    return _autocomplete_json(
        Member.objects.all(), "name", request.GET.get("term", "")
    )


@login_required(login_url="login")
def auto_book(request):
    return _autocomplete_json(
        Book.objects.all(), "title", request.GET.get("term", "")
    )


class BorrowRecordDetailView(LoginRequiredMixin, DetailView):
    model = BorrowRecord
    context_object_name = "record"
    template_name = "borrow_records/detail.html"
    login_url = "login"

    # def get_queryset(self):
    #     return BorrowRecord.objects.filter(pk=self.kwargs['pk'])

    # Not recommanded
    def get_context_data(self, **kwargs):
        context = super(BorrowRecordDetailView, self).get_context_data(**kwargs)
        # A renamed or removed member must not turn the record page into a 500.
        context["related_member"] = Member.objects.filter(
            name=self.object.borrower
        ).first()
        return context


class BorrowRecordListView(LoginRequiredMixin, OrderedPageMixin, ListView):
    model = BorrowRecord
    template_name = "borrow_records/list.html"
    login_url = "login"
    context_object_name = "records"
    default_order = "-closed_at"

    def listing(self):
        records, search = self.order_queryset(BorrowRecord.objects.all())
        if search:
            records = records.filter(
                Q(borrower__icontains=search)
                | Q(book__icontains=search)
                | Q(borrower_card__icontains=search)
            )
        return records


class BorrowRecordDeleteView(LoginRequiredMixin, View):
    login_url = "login"

    def post(self, request, *args, **kwargs):
        record_pk = kwargs["pk"]
        delete_record = get_object_or_404(BorrowRecord, pk=record_pk)
        model_name = delete_record.__class__.__name__
        messages.error(
            request, f"Record {delete_record.borrower} => {delete_record.book} Removed"
        )
        delete_record.delete()
        UserActivity.objects.create(
            created_by=self.request.user.username,
            operation_type="danger",
            target_model=model_name,
            detail=f"Delete {model_name} {delete_record.borrower}",
        )
        return HttpResponseRedirect(reverse("record_list"))


class BorrowRecordClose(LoginRequiredMixin, View):
    login_url = "login"

    def post(self, request, *args, **kwargs):
        close_record = get_object_or_404(BorrowRecord, pk=self.kwargs["pk"])
        if close_record.open_or_close == 0:
            close_record.closed_by = request.user.username
            close_record.final_status = close_record.return_status
            close_record.delay_days = close_record.get_delay_number_days
            close_record.open_or_close = 1
            close_record.closed_at = timezone.now()
            with transaction.atomic():
                close_record.save()
                matches = Book.objects.filter(title=close_record.book)
                if matches.count() == 1:
                    borrowed_book = matches.get()
                    borrowed_book.quantity += close_record.quantity
                    still_open = BorrowRecord.objects.filter(
                        book=close_record.book, open_or_close=0
                    ).exists()
                    if not still_open:
                        borrowed_book.status = 1
                    borrowed_book.save()

            UserActivity.objects.create(
                created_by=request.user.username,
                operation_type="info",
                target_model=close_record.__class__.__name__,
                detail=(
                    f"Close {close_record.__class__.__name__} "
                    f"'{close_record.borrower}'=>{close_record.book}"
                ),
            )
        return HttpResponseRedirect(reverse("record_list"))


# Data center
@method_decorator(allowed_groups(group_name=["download_data"]), name="dispatch")
class DataCenterView(LoginRequiredMixin, TemplateView):
    template_name = "book/download_data.html"
    login_url = "login"

    def get(self, request, *args, **kwargs):
        # check_user_group(request.user,"download_data")
        data = {
            m.objects.model._meta.db_table: {
                "source": pd.DataFrame(list(m.objects.all().values())),
                "path": f"{settings.BASE_DIR!s}/datacenter/{m.__name__}_{TODAY}.csv",
                "file_name": f"{m.__name__}_{TODAY}.csv",
            }
            for m in apps.get_models()
            if m.__name__ in allowed_models
        }

        count_total = {k: v["source"].shape[0] for k, v in data.items()}
        return render(request, self.template_name, context={"model_list": count_total})


def _export_frame(model):
    """Stored field values for a data-center CSV, in model field order.

    Open borrow loans write ``get_delay_number_days`` (the same live calendar
    delay the record list shows). Closed loans keep the stored ``delay_days``.
    Other models are unchanged.
    """
    rows = list(model.objects.all().values())
    if model is BorrowRecord and rows:
        open_ids = [row["id"] for row in rows if row["open_or_close"] == 0]
        if open_ids:
            live_delay = {
                record.pk: record.get_delay_number_days
                for record in BorrowRecord.objects.filter(pk__in=open_ids)
            }
            for row in rows:
                if row["open_or_close"] == 0:
                    row["delay_days"] = live_delay[row["id"]]
    return pd.DataFrame(rows)


@login_required(login_url="login")
@allowed_groups(group_name=["download_data"])
def download_data(request, model_name):
    check_user_group(request.user, "download_data")

    download = {
        m.objects.model._meta.db_table: {
            "source": _export_frame(m),
            "path": f"{settings.BASE_DIR!s}/datacenter/{m.__name__}_{TODAY}.csv",
            "file_name": f"{m.__name__}_{TODAY}.csv",
        }
        for m in apps.get_models()
        if m.__name__ in allowed_models
    }

    if model_name not in download:
        raise Http404

    download[model_name]["source"].to_csv(
        download[model_name]["path"], index=False, encoding="utf-8"
    )
    download_file = pd.read_csv(download[model_name]["path"], encoding="utf-8")
    response = HttpResponse(download_file, content_type="text/csv")
    response = HttpResponse(
        open(download[model_name]["path"], encoding="utf-8"),
        content_type="text/csv",
    )
    response["Content-Disposition"] = (
        f"attachment;filename={download[model_name]['file_name']}"
    )
    return response


# Handle Errors


def page_not_found(request, exception):
    context = {}
    response = render(request, "errors/404.html", context=context)
    response.status_code = 404
    return response


def server_error(request, exception=None):
    context = {}
    response = render(request, "errors/500.html", context=context)
    response.status_code = 500
    return response


def permission_denied(request, exception=None):
    context = {}
    response = render(request, "errors/403.html", context=context)
    response.status_code = 403
    return response


def bad_request(request, exception=None):
    context = {}
    response = render(request, "errors/400.html", context=context)
    response.status_code = 400
    return response


# Employees
# @method_decorator(user_passes_test(lambda u: check_superuser(u)), name='dispatch')
class EmployeeView(SuperUserRequiredMixin, ListView):
    login_url = "login"
    model = User
    context_object_name = "employees"
    template_name = "book/employees.html"

    # def get(self, request):
    #     # check_superuser(request.user)
    #     return super(EmployeeView, self).get(self,request)


# @method_decorator(user_passes_test(lambda u: check_superuser(u)), name='dispatch')
class EmployeeDetailView(SuperUserRequiredMixin, DetailView):
    model = User
    context_object_name = "employee"
    template_name = "book/employee_detail.html"
    login_url = "login"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["groups"] = user_groups
        return context


@login_required(login_url="login")
def EmployeeUpdate(request, pk):
    # The group checkboxes live on the employee detail page and POST here.
    # A GET used to fall off the end and return None, which Django turns into 500.
    if not request.user.is_superuser:
        raise PermissionDenied("You do not have permission to access this Page")
    current_user = get_object_or_404(User, pk=pk)
    if request.method == "POST":
        chosen_groups = [g for g in user_groups if "on" in request.POST.getlist(g)]
        current_user.groups.clear()
        for each in chosen_groups:
            group, _created = Group.objects.get_or_create(name=each)
            current_user.groups.add(group)
        messages.success(
            request, f"Group for  << {current_user.username} >> has been updated"
        )
        return redirect("employees_detail", pk=pk)
    return render(
        request,
        "book/employee_detail.html",
        {"employee": current_user, "groups": user_groups},
    )


# Notice


class NoticeListView(SuperUserRequiredMixin, ListView):
    context_object_name = "notices"
    template_name = "notice_list.html"
    login_url = "login"

    # 未读通知的查询集
    def get_queryset(self):
        return self.request.user.notifications.unread()


class NoticeUpdateView(SuperUserRequiredMixin, View):
    """Update Status of Notification"""

    login_url = "login"

    def post(self, request):
        notice_id = request.POST.get("notice_id")
        if notice_id:
            notice = get_object_or_404(request.user.notifications, id=notice_id)
            notice.mark_as_read()
            return redirect("category_list")
        request.user.notifications.mark_all_as_read()
        return redirect("notice_list")
