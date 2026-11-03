from django.contrib import admin, messages

from .models import Job


@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = ('title', 'company', 'category', 'job_type', 'location', 'salary', 'is_active', 'created_at')
    list_filter = ('is_active', 'category', 'job_type', 'created_at')
    search_fields = ('title', 'phone', 'company', 'description')
    list_editable = ('is_active',)
    list_select_related = ('posted_by',)
    date_hierarchy = 'created_at'
    list_per_page = 25
    actions = ['activate', 'deactivate']

    @admin.action(description='Тандалган вакансияларды активдештирүү')
    def activate(self, request, queryset):
        n = queryset.update(is_active=True)
        self.message_user(request, f'{n} вакансия активдештирилди.', messages.SUCCESS)

    @admin.action(description='Тандалган вакансияларды жабуу (активсиз кылуу)')
    def deactivate(self, request, queryset):
        n = queryset.update(is_active=False)
        self.message_user(request, f'{n} вакансия жабылды.', messages.WARNING)

    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.posted_by = request.user
        super().save_model(request, obj, form, change)
