from django.urls import path

from . import views

urlpatterns = [
    path("sessions/", views.SessionListView.as_view(), name="session_list"),
    path("sessions/create/", views.SessionCreateView.as_view(), name="session_create"),
    path("sessions/<int:pk>/edit/", views.SessionUpdateView.as_view(), name="session_update"),
    path("sessions/<int:pk>/delete/", views.SessionDeleteView.as_view(), name="session_delete"),

    path("semesters/", views.SemesterListView.as_view(), name="semester_list"),
    path("semesters/create/", views.SemesterCreateView.as_view(), name="semester_create"),
    path("semesters/<int:pk>/edit/", views.SemesterUpdateView.as_view(), name="semester_update"),
    path("semesters/<int:pk>/delete/", views.SemesterDeleteView.as_view(), name="semester_delete"),
]
