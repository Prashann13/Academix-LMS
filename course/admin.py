from django.contrib import admin

from .models import Program, Course, CourseAllocation

admin.site.register(Program)
admin.site.register(Course)
admin.site.register(CourseAllocation)
