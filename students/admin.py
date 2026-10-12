from django.contrib import admin

from .models import Student, TakenCourse

admin.site.register(Student)
admin.site.register(TakenCourse)
