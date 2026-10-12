from django.contrib import messages
from django.contrib.auth import login as auth_login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView, LogoutView
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import ListView, UpdateView, DeleteView

from .decorators import role_required, RoleRequiredMixin
from .forms import UserRegisterForm, LoginForm, ProfileUpdateForm
from .models import User


class AcademixLoginView(LoginView):
    template_name = "registration/login.html"
    authentication_form = LoginForm
    redirect_authenticated_user = True


class AcademixLogoutView(LogoutView):
    next_page = "login"


@login_required
def dashboard(request):
    """
    Single entry point after login. Renders different context/blocks
    depending on the logged-in user's role.
    """
    user = request.user
    context = {"user": user}

    if user.is_admin_role:
        from course.models import Program, Course
        from students.models import Student
        from lecturers.models import Lecturer
        from core.models import AcademicSession, Semester
        from news_events.models import NewsAndEvents

        context.update(
            {
                "template": "dashboard/admin_dashboard.html",
                "total_students": Student.objects.count(),
                "total_lecturers": Lecturer.objects.count(),
                "total_courses": Course.objects.count(),
                "total_programs": Program.objects.count(),
                "current_session": AcademicSession.objects.filter(is_current=True).first(),
                "current_semester": Semester.objects.filter(is_current=True).first(),
                "news": NewsAndEvents.objects.order_by("-updated_date")[:5],
            }
        )
    elif user.is_lecturer_role:
        from course.models import CourseAllocation
        from news_events.models import NewsAndEvents

        lecturer = getattr(user, "lecturer_profile", None)
        allocations = (
            CourseAllocation.objects.filter(lecturer=lecturer) if lecturer else []
        )
        context.update(
            {
                "template": "dashboard/lecturer_dashboard.html",
                "lecturer": lecturer,
                "allocations": allocations,
                "news": NewsAndEvents.objects.order_by("-updated_date")[:5],
            }
        )
    else:
        from students.models import Student, TakenCourse
        from news_events.models import NewsAndEvents

        student = getattr(user, "student_profile", None)
        taken_courses = (
            TakenCourse.objects.filter(student=student) if student else []
        )
        context.update(
            {
                "template": "dashboard/student_dashboard.html",
                "student": student,
                "taken_courses": taken_courses,
                "news": NewsAndEvents.objects.order_by("-updated_date")[:5],
            }
        )

    return render(request, context["template"], context)


@role_required("ADMIN")
def register_user(request):
    """Admin-only: create a new Admin / Lecturer / Student account."""
    if request.method == "POST":
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            role = form.cleaned_data["role"]
            user.role = role
            user.save()

            if role == User.Role.STUDENT:
                from students.models import Student

                Student.objects.create(user=user)
            elif role == User.Role.LECTURER:
                from lecturers.models import Lecturer

                Lecturer.objects.create(user=user)

            messages.success(request, f"Account created for {user.username}.")
            return redirect("user_list")
    else:
        form = UserRegisterForm()

    return render(request, "accounts/register.html", {"form": form, "title": "Create User"})


class UserListView(RoleRequiredMixin, ListView):
    allowed_roles = ["ADMIN"]
    model = User
    template_name = "accounts/user_list.html"
    context_object_name = "users"
    paginate_by = 20

    def get_queryset(self):
        return User.objects.all().order_by("role", "username")


class UserDeleteView(RoleRequiredMixin, DeleteView):
    allowed_roles = ["ADMIN"]
    model = User
    template_name = "shared/generic_confirm_delete.html"
    success_url = reverse_lazy("user_list")
    context_object_name = "object"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["title"] = f"Delete user: {self.object}"
        return ctx


@login_required
def profile(request):
    if request.method == "POST":
        form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated successfully.")
            return redirect("profile")
    else:
        form = ProfileUpdateForm(instance=request.user)
    return render(request, "accounts/profile.html", {"form": form})
