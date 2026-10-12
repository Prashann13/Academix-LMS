from django.urls import path

from . import views

urlpatterns = [
    path("", views.LecturerListView.as_view(), name="lecturer_list"),
    path("<int:pk>/", views.LecturerDetailView.as_view(), name="lecturer_detail"),
    path("<int:pk>/edit/", views.LecturerUpdateView.as_view(), name="lecturer_update"),
    path("<int:pk>/delete/", views.LecturerDeleteView.as_view(), name="lecturer_delete"),
]
