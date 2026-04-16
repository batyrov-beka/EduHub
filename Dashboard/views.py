from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import user_passes_test
from django.contrib import messages
from django.contrib.auth import get_user_model
from .models import Notification
from users.models import CustomUser
from django.utils.translation import gettext as _
try:
    from apps.jobs.models import Job
except ImportError:
    from jobs.models import Job

User = get_user_model()


def is_admin(user):
    return user.is_superuser or user.is_staff


@user_passes_test(lambda u: u.is_superuser)
def admin_control(request):
    context = {
        'total_students': CustomUser.objects.filter(role='student').count(),
        'total_employers': CustomUser.objects.filter(role='employer', is_verified=True).count(),

        'total_jobs': Job.objects.count(),

        'students': CustomUser.objects.filter(role='student'),
        'employers': CustomUser.objects.filter(role='employer', is_verified=True),
        'all_jobs': Job.objects.all().order_by('-created_at'),

        'pending_users': CustomUser.objects.filter(is_verified=False, role='employer'),
    }
    return render(request, 'Dashboard/admin_control.html', context)

def waiting_approval(request):
    return render(request, 'verification/waiting_approval.html')



@user_passes_test(lambda u: u.is_superuser)
def delete_user(request, user_id):
    if request.method == 'POST':
        user = get_object_or_404(CustomUser, id=user_id)
        username = user.username
        user.delete()
        messages.success(request, _("Пользователь {username} успешно удален!").format(username=username))
    return redirect('admin_control')

@user_passes_test(lambda u: u.is_superuser)
def approve_user(request, user_id):
    user = get_object_or_404(User, id=user_id)
    user.is_verified = True
    user.save()
    messages.success(request, _("Пользователь {username} успешно подтвержден!").format(username=user.username))
    return redirect('admin_control')

@user_passes_test(is_admin, login_url='login')
def reject_user(request, user_id):
    user_to_reject = get_object_or_404(User, id=user_id)
    username = user_to_reject.username
    user_to_reject.delete()
    messages.warning(request, _("Пользователь {username} был отклонен и удален.").format(username=username))
    return redirect('admin_control')

@user_passes_test(lambda u: u.is_superuser)
def send_broadcast(request):
    if request.method == 'POST':
        message_text = request.POST.get('message')
        if message_text:
            users = User.objects.all()
            notifications = [Notification(user=u, message=message_text) for u in users]
            Notification.objects.bulk_create(notifications)
            messages.success(request, _("Сообщение успешно отправлено {count} пользователям!").format(count=users.count()))
        else:
            messages.error(request, _("Сообщение не должно быть пустым!"))
    return redirect('admin_control')

@user_passes_test(lambda u: u.is_superuser)
def toggle_user_block(request, user_id):
    user_to_block = get_object_or_404(CustomUser, id=user_id)
    user_to_block.is_blocked = not user_to_block.is_blocked
    user_to_block.save()

    if user_to_block.is_blocked:
        messages.warning(request, _("Пользователь {username} заблокирован!").format(username=user_to_block.username))
    else:
        messages.success(request, _("Пользователь {username} разблокирован!").format(username=user_to_block.username))

    return redirect('admin_control')



