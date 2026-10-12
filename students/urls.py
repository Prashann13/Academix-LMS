from django.urls import path

from . import views

urlpatterns = [
    path("", views.StudentListView.as_view(), name="student_list"),
    path("import/", views.StudentCSVImportView.as_view(), name="student_import"),
    path("<int:pk>/", views.StudentDetailView.as_view(), name="student_detail"),
    path("<int:pk>/edit/", views.StudentUpdateView.as_view(), name="student_update"),
    path("<int:pk>/delete/", views.StudentDeleteView.as_view(), name="student_delete"),

    path("records/", views.TakenCourseListView.as_view(), name="record_list"),
    path("records/create/", views.TakenCourseCreateView.as_view(), name="record_create"),
    path("records/<int:pk>/edit/", views.TakenCourseUpdateView.as_view(), name="record_update"),
    path("records/<int:pk>/delete/", views.TakenCourseDeleteView.as_view(), name="record_delete"),
]
