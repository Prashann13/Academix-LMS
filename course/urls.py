from django.urls import path

from . import views

urlpatterns = [
    path("programs/", views.ProgramListView.as_view(), name="program_list"),
    path("programs/create/", views.ProgramCreateView.as_view(), name="program_create"),
    path("programs/<int:pk>/edit/", views.ProgramUpdateView.as_view(), name="program_update"),
    path("programs/<int:pk>/delete/", views.ProgramDeleteView.as_view(), name="program_delete"),

    path("", views.CourseListView.as_view(), name="course_list"),
    path("create/", views.CourseCreateView.as_view(), name="course_create"),
    path("<int:pk>/", views.CourseDetailView.as_view(), name="course_detail"),
    path("<int:pk>/edit/", views.CourseUpdateView.as_view(), name="course_update"),
    path("<int:pk>/delete/", views.CourseDeleteView.as_view(), name="course_delete"),

    path("allocations/", views.AllocationListView.as_view(), name="allocation_list"),
    path("allocations/create/", views.AllocationCreateView.as_view(), name="allocation_create"),
    path("allocations/<int:pk>/edit/", views.AllocationUpdateView.as_view(), name="allocation_update"),
    path("allocations/<int:pk>/delete/", views.AllocationDeleteView.as_view(), name="allocation_delete"),
]
