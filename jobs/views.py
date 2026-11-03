import logging

import requests
from django.conf import settings
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.translation import gettext as _
from django.views.decorators.http import require_POST

from users.decorators import employer_required

from .forms import JobFilterForm, JobForm
from .models import Job

logger = logging.getLogger(__name__)


def filter_jobs(queryset, data):
    form = JobFilterForm(data)
    if not form.is_valid():
        return queryset, form

    cd = form.cleaned_data
    if cd.get('search'):
        q = cd['search']
        queryset = queryset.filter(
            Q(title__icontains=q) | Q(company__icontains=q) | Q(description__icontains=q)
        )
    if cd.get('category'):
        queryset = queryset.filter(category=cd['category'])
    if cd.get('job_type'):
        queryset = queryset.filter(job_type=cd['job_type'])
    if cd.get('location'):
        queryset = queryset.filter(location__icontains=cd['location'])
    if cd.get('salary_min'):
        queryset = queryset.filter(salary__gte=cd['salary_min'])

    sort = cd.get('sort') or 'new'
    if sort == 'salary_desc':
        queryset = queryset.order_by('-salary', '-created_at')
    elif sort == 'salary_asc':
        queryset = queryset.filter(salary__isnull=False).order_by('salary', '-created_at')
    else:
        queryset = queryset.order_by('-created_at')
    return queryset, form


def vacancy_list(request):
    jobs = Job.objects.filter(is_active=True).annotate(app_count=Count('applications'))
    jobs, filter_form = filter_jobs(jobs, request.GET)

    paginator = Paginator(jobs, 9)
    page = paginator.get_page(request.GET.get('page'))

    params = request.GET.copy()
    params.pop('page', None)

    context = {
        'jobs': page,
        'page_obj': page,
        'total': paginator.count,
        'filter_form': filter_form,
        'querystring': params.urlencode(),
    }
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return render(request, 'jobs/job_list_partial.html', context)
    return render(request, 'jobs/job_list.html', context)


def profile_view(request):
    if not request.user.is_authenticated:
        return redirect('login')
    if request.user.is_superuser:
        return redirect('admin_control')
    if request.user.role == 'student':
        return redirect('student_applications')

    vacancies = (
        Job.objects.filter(posted_by=request.user)
        .annotate(
            app_count=Count('applications'),
            pending_count=Count('applications', filter=Q(applications__status='pending')),
        )
        .order_by('-created_at')
    )
    paginator = Paginator(vacancies, 8)
    page = paginator.get_page(request.GET.get('page'))

    from forms.models import Application
    apps = Application.objects.filter(vacancy__posted_by=request.user)
    stats = {
        'active': vacancies.filter(is_active=True).count(),
        'closed': vacancies.filter(is_active=False).count(),
        'applications': apps.count(),
        'pending': apps.filter(status='pending').count(),
    }
    return render(request, 'vacancy/profile.html', {'user_vacancies': page, 'stats': stats})


@employer_required
def post_job(request):
    if request.method == "POST":
        form = JobForm(request.POST)
        if form.is_valid():
            job = form.save(commit=False)
            job.posted_by = request.user
            job.save()
            send_telegram_notification(job, request)
            messages.success(request, _("Вакансия успешно опубликована!"))
            return redirect('profile')
    else:
        initial = {}
        last_job = Job.objects.filter(posted_by=request.user).order_by('-created_at').first()
        if last_job:
            initial = {'company': last_job.company, 'phone': last_job.phone, 'location': last_job.location}
        form = JobForm(initial=initial)

    return render(request, 'jobs/post_job.html', {'form': form, 'is_edit': False})


@employer_required
def edit_vacancy(request, pk):
    job = get_object_or_404(Job, pk=pk, posted_by=request.user)
    if request.method == 'POST':
        form = JobForm(request.POST, instance=job)
        if form.is_valid():
            form.save()
            messages.success(request, _("Изменения сохранены."))
            return redirect('profile')
    else:
        form = JobForm(instance=job)
    return render(request, 'jobs/post_job.html', {'form': form, 'is_edit': True, 'job': job})


@require_POST
@employer_required
def close_vacancy(request, pk):
    job = get_object_or_404(Job, pk=pk, posted_by=request.user)
    job.is_active = False
    job.save(update_fields=['is_active'])
    messages.info(request, _("Вакансия закрыта."))
    return redirect('profile')


@require_POST
@employer_required
def reopen_vacancy(request, pk):
    job = get_object_or_404(Job, pk=pk, posted_by=request.user)
    job.is_active = True
    job.save(update_fields=['is_active'])
    messages.success(request, _("Вакансия снова открыта."))
    return redirect('profile')


@require_POST
def delete_job(request, pk):
    if not request.user.is_authenticated:
        return redirect('login')
    job = get_object_or_404(Job, pk=pk)
    if not (request.user.is_superuser or job.posted_by_id == request.user.id):
        messages.error(request, _("У вас нет доступа к этой странице."))
        return redirect('home')
    job.delete()
    messages.success(request, _("Вакансия удалена."))
    return redirect('admin_control' if request.user.is_superuser else 'profile')


# ---------------------------------------------------------------- Telegram

def send_telegram_notification(job, request=None):
    token = settings.TELEGRAM_BOT_TOKEN
    chat_id = settings.TELEGRAM_CHAT_ID
    if not token or not chat_id:
        return

    link = settings.SITE_URL.rstrip('/') + reverse('vacancy_detail', args=[job.pk])
    message = (
        f"🚀 <b>Жаңы вакансия / Новая вакансия</b>\n\n"
        f"📌 {job.title}\n"
        f"🏢 {job.company}\n"
        f"📍 {job.location}\n"
        f"💰 {job.salary or '—'}\n\n"
        f"🔗 <a href=\"{link}\">EduHub</a>"
    )
    try:
        response = requests.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            data={'chat_id': chat_id, 'text': message, 'parse_mode': 'HTML'},
            timeout=10,
        )
        if response.status_code != 200:
            logger.warning("Telegram error %s: %s", response.status_code, response.text)
    except requests.RequestException as exc:
        logger.warning("Telegram connection error: %s", exc)
