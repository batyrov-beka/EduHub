from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser


class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ['username', 'email', 'role', 'university', 'is_staff']

    fieldsets = UserAdmin.fieldsets + (
        (None, {'fields': ('role', 'university', 'phone', 'profile_picture')}),
    )


admin.site.register(CustomUser, CustomUserAdmin)