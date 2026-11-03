import csv
from datetime import timedelta

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Count, Q
from django.db.models.functions import TruncDate
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.translation import gettext as _
from django.views.decorators.http import require_POST

from forms.models import Application, Resume
from jobs.models import Job

from .models import Notification, notify

User = get_user_model()

superuser_required = user_passes_test(lambda u: u.is_active and u.is_superuser, login_url='login')


@superuser_required
def admin_control(request):
    students = User.objects.filter(role='student').order_by('-date_joined')
    employers = User.objects.filter(role='employer', is_verified=True).order_by('-date_joined')
    jobs = Job.objects.select_related('posted_by').annotate(app_count=Count('applications'))
    applications = Application.objects.all()

    since = timezone.now() - timedelta(days=13)
    daily = {
        row['day']: row['total']
        for row in applications.filter(created_at__gte=since)
        .annotate(day=TruncDate('created_at')).values('day').annotate(total=Count('id'))
    }
    activity = []
    for i in range(14):
        day = (since + timedelta(days=i)).date()
        activity.append({'day': day, 'total': daily.get(day, 0)})
    max_activity = max([a['total'] for a in activity] + [1])

    category_labels = dict(Job.CATEGORY_CHOICES)
    by_category = [
        {'label': category_labels.get(row['category'], row['category']), 'total': row['total']}
        for row in Job.objects.values('category').annotate(total=Count('id')).order_by('-total')
    ]
    max_category = max([c['total'] for c in by_category] + [1])

    context = {
        'total_students': students.count(),
        'total_employers': employers.count(),
        'total_jobs': jobs.count(),
        'active_jobs': jobs.filter(is_active=True).count(),
        'total_applications': applications.count(),
        'status_counts': {
            'pending': applications.filter(status='pending').count(),
            'accepted': applications.filter(status='accepted').count(),
            'rejected': applications.filter(status='rejected').count(),
        },
        'resumes_count': Resume.objects.exclude(full_name='').count(),
        'students': students,
        'employers': employers,
        'all_jobs': jobs.order_by('-created_at'),
        'pending_users': User.objects.filter(is_verified=False, role='employer', is_active=True),
        'activity': activity,
        'max_activity': max_activity,
        'by_category': by_category,
        'max_category': max_category,
        'tab': request.GET.get('tab', 'overview'),
    }
    return render(request, 'Dashboard/admin_control.html', context)


def waiting_approval(request):
    return render(request, 'verification/waiting_approval.html')


@require_POST
@superuser_required
def approve_user(request, user_id):
    user = get_object_or_404(User, id=user_id)
    user.is_verified = True
    user.save(update_fields=['is_verified'])
    notify(user, _("Ваш аккаунт работодателя подтверждён! Теперь вы можете публиковать вакансии."))
    messages.success(request, _("Пользователь {username} успешно подтвержден!").format(username=user.username))
    return redirect('admin_control')


@require_POST
@superuser_required
def reject_user(request, user_id):
    user = get_object_or_404(User, id=user_id, is_superuser=False)
    username = user.username
    user.delete()
    messages.warning(request, _("Пользователь {username} был отклонен и удален.").format(username=username))
    return redirect('admin_control')


@require_POST
@superuser_required
def delete_user(request, user_id):
    user = get_object_or_404(User, id=user_id, is_superuser=False)
    username = user.username
    user.delete()
    messages.success(request, _("Пользователь {username} успешно удален!").format(username=username))
    return redirect(request.POST.get('next') or 'admin_control')


@require_POST
@superuser_required
def toggle_user_block(request, user_id):
    user = get_object_or_404(User, id=user_id, is_superuser=False)
    user.is_blocked = not user.is_blocked
    user.save(update_fields=['is_blocked'])
    if user.is_blocked:
        messages.warning(request, _("Пользователь {username} заблокирован!").format(username=user.username))
    else:
        messages.success(request, _("Пользователь {username} разблокирован!").format(username=user.username))
    return redirect(request.POST.get('next') or 'admin_control')


@require_POST
@superuser_required
def send_broadcast(request):
    message_text = request.POST.get('message', '').strip()
    audience = request.POST.get('audience', 'all')
    if not message_text:
        messages.error(request, _("Сообщение не должно быть пустым!"))
        return redirect('admin_control')

    users = User.objects.filter(is_active=True)
    if audience in ('student', 'employer'):
        users = users.filter(role=audience)
    Notification.objects.bulk_create([Notification(user=u, message=message_text) for u in users])
    messages.success(request, _("Сообщение успешно отправлено {count} пользователям!").format(count=users.count()))
    return redirect('admin_control')


@superuser_required
def export_csv(request, kind):
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    filename = f"eduhub_{kind}_{timezone.localdate():%Y-%m-%d}.csv"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    response.write('﻿')
    writer = csv.writer(response, delimiter=';')

    if kind == 'students':
        writer.writerow([_('Логин'), _('ФИО'), 'Email', _('Телефон'), _('Университет'),
                         _('Резюме'), _('Откликов'), _('Принят'), _('Дата регистрации')])
        students = (
            User.objects.filter(role='student')
            .annotate(
                apps=Count('applications', distinct=True),
                accepted=Count('applications', filter=Q(applications__status='accepted'), distinct=True),
            )
            .order_by('username')
        )
        for s in students:
            resume = getattr(s, 'resume', None)
            writer.writerow([
                s.username, resume.full_name if resume else s.get_full_name(), s.email, s.phone or '',
                s.university or '', _('Да') if resume and resume.full_name else _('Нет'),
                s.apps, s.accepted, timezone.localtime(s.date_joined).strftime('%d.%m.%Y'),
            ])
    elif kind == 'jobs':
        writer.writerow([_('Должность'), _('Компания'), _('Категория'), _('Тип занятости'), _('Город'),
                         _('Зарплата'), _('Статус'), _('Откликов'), _('Дата публикации')])
        for j in Job.objects.annotate(apps=Count('applications')).order_by('-created_at'):
            writer.writerow([
                j.title, j.company, j.get_category_display(), j.get_job_type_display(), j.location,
                j.salary or _('Договорная'), _('Активна') if j.is_active else _('Закрыта'),
                j.apps, timezone.localtime(j.created_at).strftime('%d.%m.%Y'),
            ])
    elif kind == 'applications':
        writer.writerow([_('Студент'), 'Email', _('Вакансия'), _('Компания'), _('Статус'), _('Дата')])
        for a in Application.objects.select_related('student', 'resume', 'vacancy').order_by('-created_at'):
            writer.writerow([
                a.resume.full_name or a.student.username, a.student.email, a.vacancy.title,
                a.vacancy.company, a.get_status_display(),
                timezone.localtime(a.created_at).strftime('%d.%m.%Y %H:%M'),
            ])
    else:
        return HttpResponse(status=404)
    return response


@login_required
def notifications_view(request):
    items = list(request.user.admin_notifications.all()[:100])
    unread_ids = [n.id for n in items if not n.is_read]
    if unread_ids:
        Notification.objects.filter(id__in=unread_ids).update(is_read=True)
    return render(request, 'Dashboard/notifications.html', {
        'notifications': items,
        'unread_ids': unread_ids,
        'unread_notifications': 0,
    })


@require_POST
@login_required
def notifications_read_all(request):
    request.user.admin_notifications.filter(is_read=False).update(is_read=True)
    return redirect('notifications')
