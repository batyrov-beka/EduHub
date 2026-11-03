"""Админкага EduHub брендин жана башкы бетке статистика карточкаларын кошот."""
from django.contrib import admin
from django.urls import reverse


def _stats():
    from forms.models import Application
    from jobs.models import Job
    from users.models import CustomUser

    users_url = reverse('admin:users_customuser_changelist')
    jobs_url = reverse('admin:jobs_job_changelist')
    apps_url = reverse('admin:forms_application_changelist')
    return [
        {'label': 'Студенттер', 'value': CustomUser.objects.filter(role='student').count(),
         'url': f'{users_url}?role__exact=student', 'tone': 'blue'},
        {'label': 'Иш берүүчүлөр', 'value': CustomUser.objects.filter(role='employer').count(),
         'url': f'{users_url}?role__exact=employer', 'tone': 'blue'},
        {'label': 'Тастык күтүүдө', 'value': CustomUser.objects.filter(role='employer', is_verified=False).count(),
         'url': f'{users_url}?role__exact=employer&is_verified__exact=0', 'tone': 'yellow'},
        {'label': 'Активдүү вакансиялар', 'value': Job.objects.filter(is_active=True).count(),
         'url': f'{jobs_url}?is_active__exact=1', 'tone': 'green'},
        {'label': 'Жаңы өтүнмөлөр', 'value': Application.objects.filter(status='pending').count(),
         'url': f'{apps_url}?status__exact=pending', 'tone': 'green'},
    ]


def setup():
    admin.site.site_header = 'EduHub'
    admin.site.site_title = 'EduHub башкаруу'
    admin.site.index_title = 'Башкаруу панели'

    original_index = admin.site.index

    def index(request, extra_context=None):
        extra_context = dict(extra_context or {})
        try:
            extra_context['eduhub_stats'] = _stats()
        except Exception:  # статистика кыйрабасын — админка дайыма ачылсын
            extra_context['eduhub_stats'] = []
        return original_index(request, extra_context)

    admin.site.index = index
