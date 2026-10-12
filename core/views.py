from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView

from accounts.decorators import RoleRequiredMixin
from .forms import AcademicSessionForm, SemesterForm
from .models import AcademicSession, Semester


class SessionListView(RoleRequiredMixin, ListView):
    allowed_roles = ["ADMIN"]
    model = AcademicSession
    template_name = "shared/generic_list.html"
    context_object_name = "object_list"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update(
            {
                "title": "Academic Sessions",
                "create_url": "session_create",
                "update_url": "session_update",
                "delete_url": "session_delete",
                "fields": ["name", "is_current"],
            }
        )
        return ctx


class SessionCreateView(RoleRequiredMixin, CreateView):
    allowed_roles = ["ADMIN"]
    model = AcademicSession
    form_class = AcademicSessionForm
    template_name = "shared/generic_form.html"
    success_url = reverse_lazy("session_list")
    extra_context = {"title": "Add Academic Session"}


class SessionUpdateView(RoleRequiredMixin, UpdateView):
    allowed_roles = ["ADMIN"]
    model = AcademicSession
    form_class = AcademicSessionForm
    template_name = "shared/generic_form.html"
    success_url = reverse_lazy("session_list")
    extra_context = {"title": "Edit Academic Session"}


class SessionDeleteView(RoleRequiredMixin, DeleteView):
    allowed_roles = ["ADMIN"]
    model = AcademicSession
    template_name = "shared/generic_confirm_delete.html"
    success_url = reverse_lazy("session_list")


class SemesterListView(RoleRequiredMixin, ListView):
    allowed_roles = ["ADMIN"]
    model = Semester
    template_name = "shared/generic_list.html"
    context_object_name = "object_list"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update(
            {
                "title": "Semesters",
                "create_url": "semester_create",
                "update_url": "semester_update",
                "delete_url": "semester_delete",
                "fields": ["session", "get_name_display", "is_current"],
            }
        )
        return ctx


class SemesterCreateView(RoleRequiredMixin, CreateView):
    allowed_roles = ["ADMIN"]
    model = Semester
    form_class = SemesterForm
    template_name = "shared/generic_form.html"
    success_url = reverse_lazy("semester_list")
    extra_context = {"title": "Add Semester"}


class SemesterUpdateView(RoleRequiredMixin, UpdateView):
    allowed_roles = ["ADMIN"]
    model = Semester
    form_class = SemesterForm
    template_name = "shared/generic_form.html"
    success_url = reverse_lazy("semester_list")
    extra_context = {"title": "Edit Semester"}


class SemesterDeleteView(RoleRequiredMixin, DeleteView):
    allowed_roles = ["ADMIN"]
    model = Semester
    template_name = "shared/generic_confirm_delete.html"
    success_url = reverse_lazy("semester_list")
