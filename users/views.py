import logging
import secrets
from datetime import timedelta

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, get_user_model, login, logout
from django.contrib.auth.decorators import login_required
from django.core.mail import EmailMultiAlternatives
from django.db.models import Count
from django.shortcuts import redirect, render
from django.utils import timezone
from django.utils.html import escape
from django.utils.http import url_has_allowed_host_and_scheme
from django.utils.translation import gettext as _
from django.views.decorators.http import require_POST

from forms.models import Application
from jobs.models import Job
from materials.models import Material

from .forms import ProfileForm, SignUpForm
from .models import EmailOTP

User = get_user_model()
logger = logging.getLogger(__name__)


def generate_otp():
    return f"{secrets.randbelow(900000) + 100000}"


def otp_expired(created_at):
    return timezone.now() - created_at > timedelta(minutes=settings.OTP_LIFETIME_MINUTES)


def resend_wait_seconds(created_at):
    passed = (timezone.now() - created_at).total_seconds()
    return max(0, int(settings.OTP_RESEND_SECONDS - passed))


def warn_resend_wait(request, seconds):
    messages.warning(request, _("Новый код можно запросить через %(seconds)s сек.") % {'seconds': seconds})


def warn_too_many_attempts(request):
    messages.error(request, _("Слишком много неверных попыток. Запросите новый код."))


def safe_send_mail(subject, message, recipient, html_message=None):
    try:
        email = EmailMultiAlternatives(subject, message, settings.DEFAULT_FROM_EMAIL, [recipient])
        if html_message:
            email.attach_alternative(html_message, 'text/html')
        email.send(fail_silently=False)
        return True
    except Exception as exc:
        logger.warning("Email error (%s): %s", recipient, exc)
        return False


def send_otp_email(recipient, otp, reset=False):
    minutes = settings.OTP_LIFETIME_MINUTES
    if reset:
        subject = _('EduHub — код для сброса пароля')
        intro = _('Вы запросили сброс пароля на EduHub.')
    else:
        subject = _('EduHub — код подтверждения')
        intro = _('Добро пожаловать в EduHub! Подтвердите свою почту.')
    code_line = _('Ваш код: %(code)s') % {'code': otp}
    valid = _('Код действует %(minutes)s минут.') % {'minutes': minutes}
    warn = _('Никому не сообщайте этот код — даже сотрудникам EduHub. '
             'Если вы не запрашивали код, просто проигнорируйте это письмо.')
    text = f"{intro}\n\n{code_line}\n\n{valid}\n{warn}\n\n— EduHub"
    html = (
        '<div style="font-family:Arial,Helvetica,sans-serif;max-width:480px;margin:0 auto;padding:24px;'
        'background:#f4f6fa;color:#14213d">'
        '<div style="background:#fff;border-radius:14px;padding:28px;border-top:4px solid #f2b705">'
        f'<h2 style="margin:0 0 8px;color:#1f4fd8">EduHub</h2>'
        f'<p style="margin:0 0 18px;color:#33415c">{escape(intro)}</p>'
        f'<p style="margin:0 0 6px;color:#5f6c84;font-size:14px">{escape(_("Ваш код подтверждения"))}</p>'
        f'<div style="font-size:34px;font-weight:700;letter-spacing:8px;color:#14213d;background:#e8eefd;'
        f'border-radius:10px;padding:14px 18px;text-align:center">{escape(str(otp))}</div>'
        f'<p style="margin:18px 0 6px;color:#33415c;font-size:14px">{escape(valid)}</p>'
        f'<p style="margin:0;color:#c8332b;font-size:13px;font-weight:600">{escape(warn)}</p>'
        '</div></div>'
    )
    return safe_send_mail(subject, text, recipient, html_message=html)


def home(request):
    active_jobs = Job.objects.filter(is_active=True)
    context = {
        'latest_jobs': active_jobs.select_related('posted_by').order_by('-created_at')[:6],
        'latest_materials': Material.objects.order_by('-created_at')[:3],
        'stats': {
            'jobs': active_jobs.count(),
            'companies': active_jobs.values('company').distinct().count(),
            'students': User.objects.filter(role='student').count(),
            'applications': Application.objects.count(),
        },
        'categories': [
            {'key': row['category'], 'label': dict(Job.CATEGORY_CHOICES).get(row['category'], row['category']),
             'total': row['total']}
            for row in active_jobs.values('category').annotate(total=Count('id')).order_by('-total')
        ],
    }
    return render(request, 'home.html', context)


def login_view(request):
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')

        if '@' in username:
            found = User.objects.filter(email__iexact=username).first()
            if found:
                username = found.username

        user = authenticate(request, username=username, password=password)
        if user is None:
            messages.error(request, _("Неверное имя пользователя или пароль!"))
        elif user.is_blocked:
            messages.error(request, _("Ваш профиль заблокирован администратором!"))
        else:
            login(request, user)
            messages.success(request, _("Добро пожаловать!"))
            next_url = request.GET.get('next') or request.POST.get('next')
            if next_url and url_has_allowed_host_and_scheme(next_url, {request.get_host()}):
                return redirect(next_url)
            return redirect('home')

    return render(request, 'registration/login.html')


def send_registration_otp(user):
    otp = generate_otp()
    EmailOTP.objects.update_or_create(user=user, defaults={'otp_code': otp, 'attempts': 0, 'created_at': timezone.now()})
    if settings.DEBUG:
        print(f"[EduHub] OTP for {user.email}: {otp}")
    return send_otp_email(user.email, otp)


def register_view(request):
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == "POST":
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False
            user.is_verified = False
            user.consent_at = timezone.now()
            user.save()

            sent = send_registration_otp(user)
            request.session['temp_user_id'] = user.id
            if sent:
                messages.info(request, _("На ваш электронный адрес отправлен код подтверждения."))
            else:
                messages.warning(request, _("Не удалось отправить письмо. Попробуйте отправить код ещё раз."))
            return redirect('verify_otp')
    else:
        form = SignUpForm(initial={'role': request.GET.get('role', 'student')})
    return render(request, 'registration/register.html', {'form': form})


def verify_otp(request):
    user_id = request.session.get('temp_user_id')
    user = User.objects.filter(id=user_id).first() if user_id else None
    if not user:
        return redirect('register')

    if request.method == 'POST':
        entered_code = request.POST.get('otp', '').strip()
        user_otp = EmailOTP.objects.filter(user=user).first()

        if not user_otp:
            messages.error(request, _("Код не найден. Отправьте код ещё раз."))
        elif user_otp.attempts >= settings.OTP_MAX_ATTEMPTS:
            warn_too_many_attempts(request)
        elif otp_expired(user_otp.created_at):
            messages.error(request, _("Срок действия кода истёк. Отправьте код ещё раз."))
        elif user_otp.otp_code != entered_code:
            user_otp.attempts += 1
            user_otp.save(update_fields=['attempts'])
            if user_otp.attempts >= settings.OTP_MAX_ATTEMPTS:
                warn_too_many_attempts(request)
            else:
                messages.error(request, _("Неверный код!"))
        else:
            user.is_active = True
            user.is_verified = user.role == 'student'
            user.save()
            user_otp.delete()
            request.session.pop('temp_user_id', None)
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')

            if user.is_verified:
                messages.success(request, _("Регистрация успешно завершена!"))
                return redirect('home')
            messages.success(request, _("Ваша заявка принята! Пожалуйста, дождитесь одобрения администратора."))
            return redirect('waiting_approval')

    return render(request, 'registration/verify_email.html', {'email': user.email})


def resend_registration_otp(request):
    user_id = request.session.get('temp_user_id')
    user = User.objects.filter(id=user_id).first() if user_id else None
    if not user:
        messages.error(request, _("Срок действия сессии истек, пожалуйста, попробуйте снова."))
        return redirect('register')

    user_otp = EmailOTP.objects.filter(user=user).first()
    wait = resend_wait_seconds(user_otp.created_at) if user_otp else 0
    if wait:
        warn_resend_wait(request, wait)
        return redirect('verify_otp')

    if send_registration_otp(user):
        messages.success(request, _("На ваш электронный адрес отправлен новый код."))
    else:
        messages.error(request, _("Не удалось отправить письмо. Попробуйте позже."))
    return redirect('verify_otp')


def _start_reset(request, email):
    otp = generate_otp()
    request.session['reset_otp'] = otp
    request.session['reset_email'] = email
    request.session['otp_time'] = timezone.now().isoformat()
    request.session['reset_verified'] = False
    request.session['reset_attempts'] = 0
    if settings.DEBUG:
        print(f"[EduHub] Reset code for {email}: {otp}")
    return send_otp_email(email, otp, reset=True)


def password_reset_form(request):
    if request.method == "POST":
        email = request.POST.get('email', '').strip()
        user = User.objects.filter(email__iexact=email).first()
        if not user:
            messages.error(request, _("Пользователь с такой почтой не найден."))
            return render(request, 'password/password_reset_form.html', {'email': email})
        if _start_reset(request, user.email):
            messages.info(request, _("Код отправлен на %(email)s") % {'email': user.email})
        else:
            messages.warning(request, _("Не удалось отправить письмо. Попробуйте позже."))
        return redirect('custom_reset_otp')

    return render(request, 'password/password_reset_form.html')


def password_reset_otp(request):
    if not request.session.get('reset_email'):
        return redirect('custom_reset_form')

    if request.method == 'POST':
        user_code = request.POST.get('otp_code', '').strip()
        server_code = request.session.get('reset_otp')
        created = request.session.get('otp_time')

        attempts = request.session.get('reset_attempts', 0)

        expired = True
        if created:
            expired = otp_expired(timezone.datetime.fromisoformat(created))

        if attempts >= settings.OTP_MAX_ATTEMPTS:
            warn_too_many_attempts(request)
        elif expired:
            messages.error(request, _("Срок действия кода истёк. Отправьте код ещё раз."))
        elif user_code and user_code == server_code:
            request.session['reset_verified'] = True
            return redirect('custom_reset_new')
        else:
            attempts += 1
            request.session['reset_attempts'] = attempts
            if attempts >= settings.OTP_MAX_ATTEMPTS:
                warn_too_many_attempts(request)
            else:
                messages.error(request, _("Неверный код!"))

    return render(request, 'password/password_reset_otp.html', {'email': request.session.get('reset_email')})


def resend_otp(request):
    email = request.session.get('reset_email')
    if not email:
        return redirect('custom_reset_form')

    created = request.session.get('otp_time')
    wait = resend_wait_seconds(timezone.datetime.fromisoformat(created)) if created else 0
    if wait:
        warn_resend_wait(request, wait)
        return redirect('custom_reset_otp')

    if _start_reset(request, email):
        messages.success(request, _("На ваш электронный адрес отправлен новый код."))
    else:
        messages.error(request, _("Не удалось отправить письмо. Попробуйте позже."))
    return redirect('custom_reset_otp')


def password_reset_new(request):
    if not request.session.get('reset_verified'):
        return redirect('custom_reset_otp')

    if request.method == 'POST':
        p1 = request.POST.get('password1', '')
        p2 = request.POST.get('password2', '')

        if p1 != p2:
            messages.error(request, _("Пароли не совпадают."))
        elif len(p1) < 8:
            messages.error(request, _("Пароль должен содержать не менее 8 символов."))
        else:
            user = User.objects.get(email__iexact=request.session.get('reset_email'))
            user.set_password(p1)
            user.save()
            for key in ('reset_otp', 'reset_email', 'otp_time', 'reset_verified'):
                request.session.pop(key, None)
            messages.success(request, _("Пароль успешно изменён. Теперь войдите в аккаунт."))
            return redirect('login')

    return render(request, 'password/password_reset_new.html')


@login_required
def account_settings(request):
    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, _("Данные профиля сохранены."))
            return redirect('account_settings')
    else:
        form = ProfileForm(instance=request.user)
    return render(request, 'users/account_settings.html', {'form': form})


@require_POST
@login_required
def delete_account(request):
    user = request.user
    if user.is_superuser:
        messages.error(request, _("Аккаунт администратора нельзя удалить здесь."))
        return redirect('account_settings')
    if not user.check_password(request.POST.get('password', '')):
        messages.error(request, _("Неверный пароль."))
        return redirect('account_settings')

    resume = getattr(user, 'resume', None)
    if resume and resume.photo:
        resume.photo.delete(save=False)
    if user.profile_picture:
        user.profile_picture.delete(save=False)

    logout(request)
    user.delete()
    messages.success(request, _("Ваш аккаунт и ваши данные удалены."))
    return redirect('home')


def privacy_policy(request):
    return render(request, 'users/privacy.html', {'contact_email': settings.EMAIL_HOST_USER})
