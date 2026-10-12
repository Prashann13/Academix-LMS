from django.urls import path

from . import views

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("login/", views.AcademixLoginView.as_view(), name="login"),
    path("logout/", views.AcademixLogoutView.as_view(), name="logout"),
    path("profile/", views.profile, name="profile"),
    path("users/", views.UserListView.as_view(), name="user_list"),
    path("users/create/", views.register_user, name="register_user"),
    path("users/<int:pk>/delete/", views.UserDeleteView.as_view(), name="user_delete"),
]
