from django.contrib import admin

from .models import Application, Resume


@admin.register(Resume)
class ResumeAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'user', 'phone')
    search_fields = ('full_name', 'skills', 'user__username', 'user__email')


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ('student', 'vacancy', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('student__username', 'vacancy__title', 'vacancy__company')
