from django.contrib import admin

from .models import Job


@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = ('title', 'company', 'category', 'job_type', 'location', 'salary', 'is_active', 'created_at')
    list_filter = ('is_active', 'category', 'job_type', 'created_at')
    search_fields = ('title', 'phone', 'company', 'description')
    list_editable = ('is_active',)

    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.posted_by = request.user
        super().save_model(request, obj, form, change)
