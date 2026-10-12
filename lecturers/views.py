from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, UpdateView, DeleteView

from accounts.decorators import RoleRequiredMixin
from .forms import LecturerForm
from .models import Lecturer


class LecturerListView(RoleRequiredMixin, ListView):
    allowed_roles = ["ADMIN"]
    model = Lecturer
    template_name = "shared/generic_list.html"
    context_object_name = "object_list"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update(
            {
                "title": "Lecturers",
                "detail_url": "lecturer_detail",
                "update_url": "lecturer_update",
                "delete_url": "lecturer_delete",
                "fields": ["staff_id", "user", "department", "office"],
            }
        )
        return ctx


class LecturerDetailView(LoginRequiredMixin, DetailView):
    model = Lecturer
    template_name = "shared/generic_detail.html"
    context_object_name = "object"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["title"] = str(self.object)
        ctx["fields"] = [
            ("Staff ID", self.object.staff_id),
            ("Name", self.object.user.get_full_name()),
            ("Email", self.object.user.email),
            ("Department", self.object.department),
            ("Office", self.object.office),
            ("Date Joined", self.object.date_joined),
        ]
        return ctx


class LecturerUpdateView(LoginRequiredMixin, UpdateView):
    model = Lecturer
    form_class = LecturerForm
    template_name = "shared/generic_form.html"
    extra_context = {"title": "Edit Lecturer Profile"}

    def get_success_url(self):
        return reverse_lazy("lecturer_detail", kwargs={"pk": self.object.pk})

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        user = self.request.user
        if not (user.is_admin_role or obj.user_id == user.id):
            raise PermissionDenied("You may only edit your own profile.")
        return obj


class LecturerDeleteView(RoleRequiredMixin, DeleteView):
    allowed_roles = ["ADMIN"]
    model = Lecturer
    template_name = "shared/generic_confirm_delete.html"
    success_url = reverse_lazy("lecturer_list")
