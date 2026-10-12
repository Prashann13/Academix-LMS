"""
Tests for the role-based access control layer.

Covers both entry points into a role check: the ``@role_required``
decorator for function-based views and ``RoleRequiredMixin`` for
class-based views. Both must deny anonymous users, allow any listed
role, and let superusers through regardless of their ``role`` value.
"""

from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse
from django.test import RequestFactory, TestCase
from django.views.generic import View

from accounts.decorators import RoleRequiredMixin, role_required
from accounts.models import User


class _AdminOnlyView(RoleRequiredMixin, View):
    """Minimal class-based view used to exercise the mixin."""

    allowed_roles = ["ADMIN"]


class RoleTestMixin:
    """Shared user fixtures for the tests below."""

    def setUp(self):
        super().setUp()
        self.factory = RequestFactory()
        self.admin = User.objects.create_user(
            username="admin1",
            email="admin1@example.com",
            password="TestPass123!",
            role=User.Role.ADMIN,
        )
        self.lecturer = User.objects.create_user(
            username="lecturer1",
            email="lecturer1@example.com",
            password="TestPass123!",
            role=User.Role.LECTURER,
        )
        self.student = User.objects.create_user(
            username="student1",
            email="student1@example.com",
            password="TestPass123!",
            role=User.Role.STUDENT,
        )
        self.superuser = User.objects.create_superuser(
            username="root",
            email="root@example.com",
            password="TestPass123!",
            role=User.Role.STUDENT,
        )


class RoleRequiredDecoratorTests(RoleTestMixin, TestCase):
    """@role_required(...) on function-based views."""

    def _call_view(self, user, *roles):
        @role_required(*roles)
        def view(request):
            return HttpResponse("allowed")

        request = self.factory.get("/")
        request.user = user
        return view(request)

    def test_listed_role_is_allowed(self):
        self.assertEqual(self._call_view(self.admin, "ADMIN").status_code, 200)

    def test_unlisted_role_is_denied(self):
        with self.assertRaises(PermissionDenied):
            self._call_view(self.student, "ADMIN")

    def test_anonymous_user_is_denied(self):
        with self.assertRaises(PermissionDenied):
            self._call_view(AnonymousUser(), "ADMIN")

    def test_every_listed_role_is_allowed(self):
        for user in (self.admin, self.lecturer):
            with self.subTest(role=user.role):
                response = self._call_view(user, "ADMIN", "LECTURER")
                self.assertEqual(response.status_code, 200)

    def test_superuser_bypasses_the_role_check(self):
        self.assertEqual(self._call_view(self.superuser, "ADMIN").status_code, 200)

    def test_decorator_preserves_view_metadata(self):
        @role_required("ADMIN")
        def named_view(request):
            return HttpResponse("allowed")

        self.assertEqual(named_view.__name__, "named_view")


class RoleRequiredMixinTests(RoleTestMixin, TestCase):
    """RoleRequiredMixin drives UserPassesTestMixin.test_func."""

    def _test_func(self, user, allowed_roles=None):
        view = _AdminOnlyView()
        if allowed_roles is not None:
            view.allowed_roles = allowed_roles
        request = self.factory.get("/")
        request.user = user
        view.setup(request)
        return view.test_func()

    def test_allowed_role_passes(self):
        self.assertTrue(self._test_func(self.admin))

    def test_unlisted_role_fails(self):
        self.assertFalse(self._test_func(self.student))

    def test_anonymous_user_fails(self):
        self.assertFalse(self._test_func(AnonymousUser()))

    def test_superuser_passes_without_a_matching_role(self):
        self.assertTrue(self._test_func(self.superuser))

    def test_multiple_allowed_roles(self):
        self.assertTrue(self._test_func(self.lecturer, ["ADMIN", "LECTURER"]))
        self.assertFalse(self._test_func(self.student, ["ADMIN", "LECTURER"]))

    def test_dispatch_raises_permission_denied(self):
        view = _AdminOnlyView()
        request = self.factory.get("/")
        request.user = self.student
        view.setup(request)
        with self.assertRaises(PermissionDenied):
            view.dispatch(request)


class UserRoleHelperTests(TestCase):
    """The is_*_role convenience properties on the custom user model."""

    def test_role_properties(self):
        admin = User.objects.create_user(
            username="a", email="a@example.com", password="TestPass123!",
            role=User.Role.ADMIN,
        )
        lecturer = User.objects.create_user(
            username="l", email="l@example.com", password="TestPass123!",
            role=User.Role.LECTURER,
        )
        student = User.objects.create_user(
            username="s", email="s@example.com", password="TestPass123!",
            role=User.Role.STUDENT,
        )

        self.assertTrue(admin.is_admin_role)
        self.assertTrue(lecturer.is_lecturer_role)
        self.assertTrue(student.is_student_role)
        self.assertFalse(student.is_admin_role)
        self.assertFalse(admin.is_lecturer_role)

    def test_default_role_is_student(self):
        user = User.objects.create_user(
            username="newbie", email="newbie@example.com", password="TestPass123!"
        )
        self.assertEqual(user.role, User.Role.STUDENT)
