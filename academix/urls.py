from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("accounts.urls")),
    path("core/", include("core.urls")),
    path("course/", include("course.urls")),
    path("students/", include("students.urls")),
    path("lecturers/", include("lecturers.urls")),
    path("news/", include("news_events.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
