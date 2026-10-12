from django.contrib import admin

from .models import AcademicSession, Semester

admin.site.register(AcademicSession)
admin.site.register(Semester)
