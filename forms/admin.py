from django.contrib import admin, messages

from .models import Application, Resume


@admin.register(Resume)
class ResumeAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'user', 'phone')
    search_fields = ('full_name', 'skills', 'user__username', 'user__email')
    list_select_related = ('user',)
    list_per_page = 25


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ('student', 'vacancy', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('student__username', 'vacancy__title', 'vacancy__company')
    list_select_related = ('student', 'vacancy')
    date_hierarchy = 'created_at'
    list_per_page = 25
    actions = ['accept', 'reject']

    @admin.action(description='Тандалган өтүнмөлөрдү КАБЫЛ алуу')
    def accept(self, request, queryset):
        n = queryset.update(status='accepted')
        self.message_user(request, f'{n} өтүнмө кабыл алынды.', messages.SUCCESS)

    @admin.action(description='Тандалган өтүнмөлөрдү ЧЕТКЕ кагуу')
    def reject(self, request, queryset):
        n = queryset.update(status='rejected')
        self.message_user(request, f'{n} өтүнмө четке кагылды.', messages.WARNING)
