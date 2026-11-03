from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db import IntegrityError, transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.translation import gettext as _
from django.views.decorators.http import require_POST

from Dashboard.models import notify
from jobs.models import Job
from users.decorators import employer_required, student_required
from users.views import safe_send_mail

from .forms import ApplyForm, ResumeForm
from .models import STATUS_CHOICES, Application, Resume


def absolute(path):
    return settings.SITE_URL.rstrip('/') + path


@student_required
def my_resume(request):
    resume = Resume.objects.filter(user=request.user).first()
    if request.method == 'POST':
        form = ResumeForm(request.POST, request.FILES, instance=resume)
        if form.is_valid():
            resume = form.save(commit=False)
            resume.user = request.user
            resume.save()
            messages.success(request, _("Резюме успешно сохранено!"))
            return redirect(request.GET.get('next') or 'view_resume')
    else:
        initial = {}
        if resume is None:
            initial = {
                'full_name': request.user.get_full_name(),
                'phone': request.user.phone,
                'education': request.user.university or '',
            }
        form = ResumeForm(instance=resume, initial=initial)
    return render(request, 'resume/resume_form.html', {'form': form, 'resume': resume})


@student_required
def view_resume(request):
    resume = Resume.objects.filter(user=request.user).first()
    if resume is None or not resume.full_name:
        return redirect('my_resume')
    return render(request, 'resume/resume_detail.html', {'resume': resume, 'is_owner': True})


@login_required
def view_student_resume(request, resume_id):
    resume = get_object_or_404(Resume, id=resume_id)
    user = request.user
    allowed = (
        user.is_superuser
        or resume.user_id == user.id
        or Application.objects.filter(resume=resume, vacancy__posted_by=user).exists()
    )
    if not allowed:
        messages.error(request, _("У вас нет доступа к этой странице."))
        return redirect('home')

    applications = []
    if user.role == 'employer':
        applications = Application.objects.filter(resume=resume, vacancy__posted_by=user).select_related('vacancy')
    return render(request, 'resume/resume_detail.html', {
        'resume': resume,
        'is_owner': resume.user_id == user.id,
        'applications': applications,
    })


def vacancy_detail(request, id):
    vacancy = get_object_or_404(Job.objects.select_related('posted_by'), id=id)
    is_owner = request.user.is_authenticated and vacancy.posted_by_id == request.user.id
    if not vacancy.is_active and not (is_owner or request.user.is_superuser):
        messages.info(request, _("Эта вакансия закрыта."))

    resume = None
    application = None
    if request.user.is_authenticated and request.user.role == 'student':
        resume = Resume.objects.filter(user=request.user).first()
        application = Application.objects.filter(vacancy=vacancy, student=request.user).first()

    similar = (
        Job.objects.filter(is_active=True, category=vacancy.category)
        .exclude(id=vacancy.id).order_by('-created_at')[:3]
    )
    return render(request, 'forms/vacancy_detail.html', {
        'vacancy': vacancy,
        'resume': resume,
        'application': application,
        'apply_form': ApplyForm(),
        'similar': similar,
        'is_owner': is_owner,
        'applications_count': vacancy.applications.count(),
    })


@require_POST
@student_required
def apply_to_vacancy(request, job_id):
    job = get_object_or_404(Job, id=job_id)
    if not job.is_active:
        messages.error(request, _("Эта вакансия закрыта."))
        return redirect('vacancy_detail', id=job_id)

    resume = Resume.objects.filter(user=request.user).first()
    if not resume or not resume.is_complete:
        messages.error(request, _("Ваше резюме не заполнено! Сначала заполните его."))
        return redirect(reverse('my_resume') + '?next=' + reverse('vacancy_detail', args=[job_id]))

    form = ApplyForm(request.POST)
    cover_letter = form.cleaned_data['cover_letter'] if form.is_valid() else ''

    try:
        with transaction.atomic():
            Application.objects.create(vacancy=job, student=request.user, resume=resume,
                                       cover_letter=cover_letter)
    except IntegrityError:
        messages.warning(request, _("Вы уже подавали заявку на эту вакансию."))
        return redirect('vacancy_detail', id=job_id)

    employer = job.posted_by
    dashboard_url = reverse('employer_dashboard')
    notify(employer, _("Новый отклик на вакансию «%(job)s» от %(name)s") % {
        'job': job.title, 'name': resume.full_name}, dashboard_url)
    if employer.email:
        safe_send_mail(
            _("Новый отклик: %(job)s") % {'job': job.title},
            _("Здравствуйте, %(user)s!\n\nНа вашу вакансию «%(job)s» поступил новый отклик.\n"
              "Кандидат: %(name)s\nПосмотреть отклики: %(url)s\n\nС уважением, команда EduHub") % {
                'user': employer.username, 'job': job.title, 'name': resume.full_name,
                'url': absolute(dashboard_url)},
            employer.email,
        )

    messages.success(request, _("Ваш отклик успешно отправлен!"))
    return redirect('vacancy_detail', id=job_id)


@require_POST
@student_required
def withdraw_application(request, pk):
    application = get_object_or_404(Application, pk=pk, student=request.user, status='pending')
    application.delete()
    messages.info(request, _("Отклик отозван."))
    return redirect('student_applications')


@require_POST
@employer_required
def update_status(request, pk, status):
    application = get_object_or_404(Application.objects.select_related('vacancy', 'student'), pk=pk)
    if application.vacancy.posted_by_id != request.user.id:
        messages.error(request, _("Вы не можете менять статус этой заявки."))
        return redirect('employer_dashboard')
    if status not in dict(STATUS_CHOICES):
        messages.error(request, _("Неверный статус."))
        return redirect('employer_dashboard')

    application.status = status
    application.save(update_fields=['status'])

    job_title = application.vacancy.title
    if status == 'accepted':
        body = _("Поздравляем! Ваш отклик на вакансию «%(job)s» принят. Работодатель свяжется с вами.") % {'job': job_title}
    elif status == 'rejected':
        body = _("К сожалению, ваш отклик на вакансию «%(job)s» отклонён.") % {'job': job_title}
    else:
        body = _("Статус вашего отклика на вакансию «%(job)s» изменён на: %(status)s.") % {
            'job': job_title, 'status': application.get_status_display()}

    student_url = reverse('student_applications')
    notify(application.student, body, student_url)
    if application.student.email:
        safe_send_mail(
            _("Обновление статуса: %(job)s") % {'job': job_title},
            _("Здравствуйте, %(user)s!\n\n%(body)s\nПодробнее в личном кабинете: %(url)s\n\nС уважением, EduHub") % {
                'user': application.student.username, 'body': body, 'url': absolute(student_url)},
            application.student.email,
        )

    messages.success(request, _("Статус заявки успешно изменен."))
    return redirect(request.POST.get('next') or 'employer_dashboard')


@employer_required
def employer_dashboard(request):
    status_filter = request.GET.get('status', '')
    job_filter = request.GET.get('job', '')

    base = Application.objects.filter(vacancy__posted_by=request.user).select_related('vacancy', 'resume', 'student')
    apps_list = base
    if status_filter in dict(STATUS_CHOICES):
        apps_list = apps_list.filter(status=status_filter)
    if job_filter.isdigit():
        apps_list = apps_list.filter(vacancy_id=int(job_filter))

    paginator = Paginator(apps_list.order_by('-created_at'), 10)
    applications = paginator.get_page(request.GET.get('page'))

    params = request.GET.copy()
    params.pop('page', None)
    return render(request, 'forms/employer_dashboard.html', {
        'applications': applications,
        'querystring': params.urlencode(),
        'current_status': status_filter,
        'current_job': job_filter,
        'my_jobs': Job.objects.filter(posted_by=request.user, applications__isnull=False).distinct(),
        'counts': {
            'all': base.count(),
            'pending': base.filter(status='pending').count(),
            'accepted': base.filter(status='accepted').count(),
            'rejected': base.filter(status='rejected').count(),
        },
    })


@student_required
def student_applications(request):
    applications = Application.objects.filter(student=request.user).select_related('vacancy').order_by('-created_at')
    resume = Resume.objects.filter(user=request.user).first()

    recommended = Job.objects.filter(is_active=True).exclude(applications__student=request.user)
    if resume and resume.skills_list:
        query = Q()
        for skill in resume.skills_list[:8]:
            query |= Q(title__icontains=skill) | Q(description__icontains=skill)
        matched = recommended.filter(query)
        recommended = matched if matched.exists() else recommended

    return render(request, 'forms/student_applications.html', {
        'applications': applications,
        'resume': resume,
        'recommended': recommended.order_by('-created_at')[:3],
        'counts': {
            'all': applications.count(),
            'pending': applications.filter(status='pending').count(),
            'accepted': applications.filter(status='accepted').count(),
            'rejected': applications.filter(status='rejected').count(),
        },
    })
