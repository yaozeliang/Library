from .models import Book,Category,Publisher,UserActivity,Profile,Member,BorrowRecord
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import PermissionDenied
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.http import HttpResponse


user_groups = ['logs','api','download_data']


def check_superuser(user):
    if not user.is_superuser:
        raise PermissionDenied("You do not have permission to access this Page")


def check_user_group(user,group_name):
    user_group = user.groups.all().values_list('name',flat=True)
    if group_name not in user_group:
        raise PermissionDenied("You do not have permission to access this Page")


def allowed_groups(group_name=[]):
	def decorator(view_func):
		def wrapper_func(request, *args, **kwargs):
            

			group = None
			if request.user.groups.exists():
				group = request.user.groups.all()[0].name

			if group in group_name:
				return view_func(request, *args, **kwargs)
			else:
				raise PermissionDenied("You do not have permission to access this Page")
		return wrapper_func
	return decorator



class SuperUserRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):

    def test_func(self):
        return self.request.user.is_superuser














# content_type = ContentType.objects.get_for_model(Book)
# content_type = ContentType.objects.get_for_model(BlogPost)
# permission = Permission.objects.create(
#     codename='can_publish',
#     name='Can Publish Posts',
#     content_type=content_type,
# )



# view_log = Permission.objects.get(codename='view_useractivity')
#  delete_log = Permission.objects.get(codename='delete_useractivity')
# logs_group = Group.objects.get(name='logs') 
# logs_group.permissions.add(view_log,delete_log)