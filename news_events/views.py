from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView

from accounts.decorators import RoleRequiredMixin
from .forms import NewsAndEventsForm
from .models import NewsAndEvents


class NewsListView(LoginRequiredMixin, ListView):
    model = NewsAndEvents
    template_name = "shared/generic_list.html"
    context_object_name = "object_list"
    paginate_by = 15

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        is_admin = self.request.user.is_admin_role
        ctx.update(
            {
                "title": "News & Events",
                "detail_url": "news_detail",
                "create_url": "news_create" if is_admin else None,
                "update_url": "news_update" if is_admin else None,
                "delete_url": "news_delete" if is_admin else None,
                "fields": ["title", "posted_as", "event_date", "updated_date"],
            }
        )
        return ctx


class NewsDetailView(LoginRequiredMixin, DetailView):
    model = NewsAndEvents
    template_name = "shared/generic_detail.html"
    context_object_name = "object"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        n = self.object
        ctx["title"] = n.title
        ctx["fields"] = [
            ("Type", n.posted_as),
            ("Summary", n.summary),
            ("Event Date", n.event_date or "-"),
            ("Last Updated", n.updated_date),
        ]
        return ctx


class NewsCreateView(RoleRequiredMixin, CreateView):
    allowed_roles = ["ADMIN"]
    model = NewsAndEvents
    form_class = NewsAndEventsForm
    template_name = "shared/generic_form.html"
    success_url = reverse_lazy("news_list")
    extra_context = {"title": "Post News / Event"}


class NewsUpdateView(RoleRequiredMixin, UpdateView):
    allowed_roles = ["ADMIN"]
    model = NewsAndEvents
    form_class = NewsAndEventsForm
    template_name = "shared/generic_form.html"
    success_url = reverse_lazy("news_list")
    extra_context = {"title": "Edit News / Event"}


class NewsDeleteView(RoleRequiredMixin, DeleteView):
    allowed_roles = ["ADMIN"]
    model = NewsAndEvents
    template_name = "shared/generic_confirm_delete.html"
    success_url = reverse_lazy("news_list")
