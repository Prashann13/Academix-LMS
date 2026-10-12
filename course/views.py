from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView

from accounts.decorators import RoleRequiredMixin
from .forms import ProgramForm, CourseForm, CourseAllocationForm
from .models import Program, Course, CourseAllocation


class ProgramListView(LoginRequiredMixin, ListView):
    model = Program
    template_name = "shared/generic_list.html"
    context_object_name = "object_list"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        is_admin = self.request.user.is_admin_role
        ctx.update(
            {
                "title": "Programs",
                "create_url": "program_create" if is_admin else None,
                "update_url": "program_update" if is_admin else None,
                "delete_url": "program_delete" if is_admin else None,
                "fields": ["name", "summary"],
            }
        )
        return ctx


class ProgramCreateView(RoleRequiredMixin, CreateView):
    allowed_roles = ["ADMIN"]
    model = Program
    form_class = ProgramForm
    template_name = "shared/generic_form.html"
    success_url = reverse_lazy("program_list")
    extra_context = {"title": "Add Program"}


class ProgramUpdateView(RoleRequiredMixin, UpdateView):
    allowed_roles = ["ADMIN"]
    model = Program
    form_class = ProgramForm
    template_name = "shared/generic_form.html"
    success_url = reverse_lazy("program_list")
    extra_context = {"title": "Edit Program"}


class ProgramDeleteView(RoleRequiredMixin, DeleteView):
    allowed_roles = ["ADMIN"]
    model = Program
    template_name = "shared/generic_confirm_delete.html"
    success_url = reverse_lazy("program_list")


class CourseListView(LoginRequiredMixin, ListView):
    model = Course
    template_name = "shared/generic_list.html"
    context_object_name = "object_list"
    paginate_by = 25

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        is_admin = self.request.user.is_admin_role
        ctx.update(
            {
                "title": "Courses",
                "create_url": "course_create" if is_admin else None,
                "update_url": "course_update" if is_admin else None,
                "delete_url": "course_delete" if is_admin else None,
                "detail_url": "course_detail",
                "fields": ["code", "title", "program", "get_level_display", "get_semester_display", "credit_units"],
            }
        )
        return ctx


class CourseDetailView(LoginRequiredMixin, DetailView):
    model = Course
    template_name = "shared/generic_detail.html"
    context_object_name = "object"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["title"] = str(self.object)
        ctx["fields"] = [
            ("Code", self.object.code),
            ("Title", self.object.title),
            ("Program", self.object.program),
            ("Level", self.object.get_level_display()),
            ("Semester", self.object.get_semester_display()),
            ("Credit Units", self.object.credit_units),
            ("Elective", "Yes" if self.object.is_elective else "No"),
        ]
        return ctx


class CourseCreateView(RoleRequiredMixin, CreateView):
    allowed_roles = ["ADMIN"]
    model = Course
    form_class = CourseForm
    template_name = "shared/generic_form.html"
    success_url = reverse_lazy("course_list")
    extra_context = {"title": "Add Course"}


class CourseUpdateView(RoleRequiredMixin, UpdateView):
    allowed_roles = ["ADMIN"]
    model = Course
    form_class = CourseForm
    template_name = "shared/generic_form.html"
    success_url = reverse_lazy("course_list")
    extra_context = {"title": "Edit Course"}


class CourseDeleteView(RoleRequiredMixin, DeleteView):
    allowed_roles = ["ADMIN"]
    model = Course
    template_name = "shared/generic_confirm_delete.html"
    success_url = reverse_lazy("course_list")


class AllocationListView(RoleRequiredMixin, ListView):
    allowed_roles = ["ADMIN"]
    model = CourseAllocation
    template_name = "shared/generic_list.html"
    context_object_name = "object_list"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update(
            {
                "title": "Course Allocations",
                "create_url": "allocation_create",
                "update_url": "allocation_update",
                "delete_url": "allocation_delete",
                "fields": ["lecturer", "session"],
            }
        )
        return ctx


class AllocationCreateView(RoleRequiredMixin, CreateView):
    allowed_roles = ["ADMIN"]
    model = CourseAllocation
    form_class = CourseAllocationForm
    template_name = "shared/generic_form.html"
    success_url = reverse_lazy("allocation_list")
    extra_context = {"title": "Allocate Courses to Lecturer"}


class AllocationUpdateView(RoleRequiredMixin, UpdateView):
    allowed_roles = ["ADMIN"]
    model = CourseAllocation
    form_class = CourseAllocationForm
    template_name = "shared/generic_form.html"
    success_url = reverse_lazy("allocation_list")
    extra_context = {"title": "Edit Allocation"}


class AllocationDeleteView(RoleRequiredMixin, DeleteView):
    allowed_roles = ["ADMIN"]
    model = CourseAllocation
    template_name = "shared/generic_confirm_delete.html"
    success_url = reverse_lazy("allocation_list")
