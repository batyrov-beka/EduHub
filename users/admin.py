from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser


class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ['username', 'email', 'role', 'is_verified', 'is_staff']

    list_filter = ['role', 'is_verified', 'is_staff']

    fieldsets = UserAdmin.fieldsets + (
        ('Кошумча маалымат', {'fields': ('role', 'university', 'phone', 'profile_picture')}),
        ('Текшерүү статусу', {'fields': ('is_verified', 'verification_data')}),
    )


admin.site.register(CustomUser, CustomUserAdmin)