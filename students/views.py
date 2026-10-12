from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, UpdateView, DeleteView, CreateView, View

from accounts.decorators import RoleRequiredMixin
from .forms import StudentForm, TakenCourseForm, StudentCSVImportForm
from .models import Student, TakenCourse
from .services import import_students_csv


class StudentListView(RoleRequiredMixin, ListView):
    allowed_roles = ["ADMIN", "LECTURER"]
    model = Student
    template_name = "shared/generic_list.html"
    context_object_name = "object_list"
    paginate_by = 25

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        is_admin = self.request.user.is_admin_role
        ctx.update(
            {
                "title": "Students",
                "detail_url": "student_detail",
                "update_url": "student_update" if is_admin else None,
                "delete_url": "student_delete" if is_admin else None,
                "fields": ["matric_number", "user", "program", "get_level_display"],
            }
        )
        return ctx


class StudentDetailView(LoginRequiredMixin, DetailView):
    model = Student
    template_name = "shared/generic_detail.html"
    context_object_name = "object"

    def dispatch(self, request, *args, **kwargs):
        self.object_check = self.get_object()
        user = request.user
        if not (
            user.is_admin_role
            or user.is_lecturer_role
            or self.object_check.user_id == user.id
        ):
            raise PermissionDenied("You may only view your own student record.")
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        s = self.object
        ctx["title"] = str(s)
        ctx["fields"] = [
            ("Matric Number", s.matric_number),
            ("Name", s.user.get_full_name()),
            ("Email", s.user.email),
            ("Program", s.program),
            ("Level", s.get_level_display()),
            ("Session Admitted", s.session_admitted),
            ("Date of Birth", s.date_of_birth),
            ("Address", s.address),
        ]
        return ctx


class StudentUpdateView(RoleRequiredMixin, UpdateView):
    allowed_roles = ["ADMIN"]
    model = Student
    form_class = StudentForm
    template_name = "shared/generic_form.html"
    extra_context = {"title": "Edit Student Record"}

    def get_success_url(self):
        return reverse_lazy("student_detail", kwargs={"pk": self.object.pk})


class StudentDeleteView(RoleRequiredMixin, DeleteView):
    allowed_roles = ["ADMIN"]
    model = Student
    template_name = "shared/generic_confirm_delete.html"
    success_url = reverse_lazy("student_list")


class TakenCourseListView(LoginRequiredMixin, ListView):
    model = TakenCourse
    template_name = "shared/generic_list.html"
    context_object_name = "object_list"
    paginate_by = 25

    def get_queryset(self):
        user = self.request.user
        qs = TakenCourse.objects.select_related("student", "course", "session")
        if user.is_student_role:
            qs = qs.filter(student__user=user)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        can_edit = self.request.user.is_admin_role or self.request.user.is_lecturer_role
        ctx.update(
            {
                "title": "Academic Records",
                "create_url": "record_create" if can_edit else None,
                "update_url": "record_update" if can_edit else None,
                "delete_url": "record_delete" if can_edit else None,
                "fields": ["student", "course", "session", "get_semester_display", "score", "grade"],
            }
        )
        return ctx


class TakenCourseCreateView(RoleRequiredMixin, CreateView):
    allowed_roles = ["ADMIN", "LECTURER"]
    model = TakenCourse
    form_class = TakenCourseForm
    template_name = "shared/generic_form.html"
    success_url = reverse_lazy("record_list")
    extra_context = {"title": "Add Academic Record"}


class TakenCourseUpdateView(RoleRequiredMixin, UpdateView):
    allowed_roles = ["ADMIN", "LECTURER"]
    model = TakenCourse
    form_class = TakenCourseForm
    template_name = "shared/generic_form.html"
    success_url = reverse_lazy("record_list")
    extra_context = {"title": "Edit Academic Record"}


class TakenCourseDeleteView(RoleRequiredMixin, DeleteView):
    allowed_roles = ["ADMIN", "LECTURER"]
    model = TakenCourse
    template_name = "shared/generic_confirm_delete.html"
    success_url = reverse_lazy("record_list")


class StudentCSVImportView(RoleRequiredMixin, View):
    """
    Admin page that uploads a CSV of students and hands it to
    students/services.import_students_csv() (the same engine the
    management command uses). After the import it re-renders the page
    with a per-row result table so the admin sees exactly what happened
    to every line of the file.
    """

    allowed_roles = ["ADMIN"]
    template_name = "students/student_import.html"

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name, {
            "form": StudentCSVImportForm(),
            "title": "Import Students from CSV",
        })

    def post(self, request, *args, **kwargs):
        form = StudentCSVImportForm(request.POST, request.FILES)
        if not form.is_valid():
            return render(request, self.template_name, {
                "form": form,
                "title": "Import Students from CSV",
            })

        csv_file = form.cleaned_data["csv_file"]
        csv_file.seek(0)

        try:
            result = import_students_csv(
                csv_file,
                default_password=form.cleaned_data.get("default_password") or None,
                skip_duplicates=form.cleaned_data.get("skip_duplicates", True),
            )
        except ValueError as e:
            form.add_error("csv_file", str(e))
            return render(request, self.template_name, {
                "form": form,
                "title": "Import Students from CSV",
            })

        s = result["summary"]
        if s["failed"]:
            messages.warning(
                request,
                f"Import finished with issues: {s['created']} created, "
                f"{s['updated']} updated, {s['skipped']} skipped, "
                f"{s['failed']} failed.",
            )
        else:
            messages.success(
                request,
                f"Import complete: {s['created']} created, "
                f"{s['updated']} updated, {s['skipped']} skipped.",
            )

        if result["generated_password"]:
            messages.info(
                request,
                f"All imported students use the generated password: "
                f"{result['generated_password']} — save it now, it is not "
                f"shown again.",
            )

        return render(request, self.template_name, {
            "form": StudentCSVImportForm(),
            "title": "Import Students from CSV",
            "result": result,
            "summary": s,
        })
