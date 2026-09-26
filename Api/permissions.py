from django.core.exceptions import PermissionDenied
from rest_framework import permissions

from book.groups_permissions import check_user_group


class IsSuperuserOrApiGroup(permissions.BasePermission):
    """Authenticated superusers and members of the ``api`` group.

    This is the default permission for every DRF view, so a new ``/api/``
    endpoint picks it up without a per-view decorator. ``check_user_group``
    lets superusers through without the group and rejects other users.
    Anonymous users are rejected here, before that helper reads ``user.groups``.
    """

    message = "You do not have permission to access this Page"

    def has_permission(self, request, view):
        user = getattr(request, "user", None)
        if user is None or not user.is_authenticated:
            return False
        try:
            check_user_group(user, "api")
        except PermissionDenied:
            return False
        return True


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object to edit it.
    """

    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions are only allowed to the owner of the snippet.
        return obj.created_by == request.user
