from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import User


class UserAdmin(BaseUserAdmin):
    list_display = ["username", "email", "first_name", "last_name", "role", "is_active"]
    list_filter = ["role", "is_active", "is_staff"]
    fieldsets = BaseUserAdmin.fieldsets + (
        ("Role & Contact", {"fields": ("role", "phone_number", "profile_picture")}),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ("Role & Contact", {"fields": ("role", "email", "phone_number")}),
    )


admin.site.register(User, UserAdmin)
