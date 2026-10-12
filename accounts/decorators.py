from functools import wraps

from django.contrib.auth.mixins import UserPassesTestMixin
from django.core.exceptions import PermissionDenied


def role_required(*roles):
    """
    Function-based view decorator restricting access to users whose
    `role` is in `roles`. Superusers/Admins always pass.

    Usage:
        @role_required("ADMIN", "LECTURER")
        def my_view(request): ...
    """

    def decorator(view_func):
        @wraps(view_func)
        def _wrapped(request, *args, **kwargs):
            user = request.user
            if not user.is_authenticated:
                raise PermissionDenied("Please log in to continue.")
            if user.is_superuser or user.role in roles:
                return view_func(request, *args, **kwargs)
            raise PermissionDenied("You do not have permission to access this page.")

        return _wrapped

    return decorator


class RoleRequiredMixin(UserPassesTestMixin):
    """
    Class-based view mixin restricting access to users whose `role`
    is in `allowed_roles`. Set `allowed_roles = ["ADMIN", ...]` on the view.
    """

    allowed_roles = []
    raise_exception = True

    def test_func(self):
        user = self.request.user
        if not user.is_authenticated:
            return False
        return user.is_superuser or user.role in self.allowed_roles
