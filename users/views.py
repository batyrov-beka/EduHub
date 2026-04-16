import random
from datetime import datetime, timedelta
from django.shortcuts import render, redirect ,get_object_or_404
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth import get_user_model, login
from jobs.models import Job
from .forms import SignUpForm
from django.utils.translation import gettext as _
from .models import EmailOTP, User
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
CustomUser = get_user_model()
from django.contrib.auth import authenticate, login

User = get_user_model()



def home(request):
    latest_jobs = Job.objects.all().order_by('-created_at')
    return render(request, 'home.html', {'jobs': latest_jobs})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            if hasattr(user, 'is_blocked') and user.is_blocked:
                messages.error(request, _("Ваш профиль заблокирован администратором!"))
                return render(request, 'registration/login.html')

            login(request, user)
            messages.success(request, _("Добро пожаловать!"))

            next_url = request.GET.get('next', 'home')
            return redirect(next_url)
        else:
            messages.error(request, _("Неверное имя пользователя или пароль!"))

    return render(request, 'registration/login.html')


def register_view(request):
    if request.method == "POST":
        form = SignUpForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data.get('email')

            if User.objects.filter(email=email).exists():
                form.add_error('email', _("Этот адрес электронной почты уже зарегистрирован!"))
                return render(request, 'registration/register.html', {'form': form})

            user = form.save(commit=False)
            user.is_active = False
            user.is_verified = False
            user.save()

            send_otp(user)
            request.session['temp_user_id'] = user.id

            messages.info(request, _("На ваш электронный адрес отправлен код подтверждения."))
            return redirect('verify_otp')
    else:
        form = SignUpForm()
    return render(request, 'registration/register.html', {'form': form})


def send_otp(user):
    otp = str(random.randint(100000, 999999))
    from .models import EmailOTP
    EmailOTP.objects.update_or_create(user=user, defaults={'otp_code': otp})

    subject = 'EduHub - Проверочный код'
    message = f'Ваш код подтверждения: {otp}'

    print(f"Почта отправляется: {user.email} | Код: {otp}")

    send_mail(
        subject,
        message,
        settings.EMAIL_HOST_USER,
        [user.email],
        fail_silently=False
    )


def verify_otp(request):
    user_id = request.session.get('temp_user_id')
    if not user_id: return redirect('register')

    if request.method == 'POST':
        entered_code = request.POST.get('otp')
        try:
            user = User.objects.get(id=user_id)
            user_otp = EmailOTP.objects.get(user=user)

            if user_otp.otp_code == entered_code:
                user.is_active = True
                role_name = str(user.role).lower()

                if 'студент' in role_name or 'student' in role_name:
                    user.is_verified = True
                    msg = _("Регистрация успешно завершена!")
                    target_url = 'home'
                else:
                    user.is_verified = False
                    msg = _("Ваша заявка принята! Пожалуйста, дождитесь одобрения администратора.")
                    target_url = 'waiting_approval'

                user.save()
                user_otp.delete()
                login(request, user)

                if 'temp_user_id' in request.session:
                    del request.session['temp_user_id']

                messages.success(request, msg)
                return redirect(target_url)
            else:
                messages.error(request, _("Неверный код!"))
        except Exception as e:
            return redirect('register')

    return render(request, 'registration/verify_email.html')

def home(request):
    context = {}
    if request.user.is_authenticated and request.user.is_superuser:
        context['total_students'] = CustomUser.objects.filter(role='student').count()
        context['total_employers'] = CustomUser.objects.filter(role='employer').count()
        context['pending_users'] = CustomUser.objects.filter(is_verified=False).exclude(is_superuser=True)

    return render(request, 'home.html', context)



def resend__otp(request):
    user_id = request.session.get('temp_user_id')

    if user_id:
        try:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            user = User.objects.get(id=user_id)

            send_otp(user)

            messages.success(request, "На ваш электронный адрес отправлен новый код.!")
            return redirect('verify_otp')
        except User.DoesNotExist:
            messages.error(request, "Пользователь не найден.")
            return redirect('register')

    messages.error(request, "Срок действия сессии истек, пожалуйста, попробуйте войти снова..")
    return redirect('register')



def password_reset_form(request):
    if request.method == "POST":
        email = request.POST.get('email', '').strip()
        user = User.objects.filter(email=email).first()
        if not user:
            messages.error(request, '')
            return render(request, 'password/password_reset_form.html')
        otp = str(random.randint(100000, 999999))
        request.session['reset_otp'] = otp
        request.session['reset_email'] = email
        request.session['otp_time'] = datetime.now().isoformat()

        send_mail('Код подтверждения', f'Ваш код: {otp}', settings.EMAIL_HOST_USER, [email])
        return redirect('custom_reset_otp')

    return render(request, 'password/password_reset_form.html')



def password_reset_otp(request):
    if request.method == 'POST':
        user_code = request.POST.get('otp_code', '').strip()
        server_code = request.session.get('reset_otp')

        if user_code and str(user_code) == str(server_code):
            request.session['reset_verified'] = True
            return redirect('custom_reset_new')
        else:
            messages.error(request, '')

    return render(request, 'password/password_reset_otp.html')



def resend_otp(request):
    email = request.session.get('reset_email')
    if email:
        otp = str(random.randint(100000, 999999))
        request.session['reset_otp'] = otp
        request.session['otp_time'] = datetime.now().isoformat()
        send_mail('Новый код', f'Код: {otp}', settings.EMAIL_HOST_USER, [email])
        messages.success(request, '')
    return redirect('custom_reset_otp')


def password_reset_new(request):
    if not request.session.get('reset_verified'):
        return redirect('custom_reset_otp')

    if request.method == 'POST':
        p1 = request.POST.get('password1', '').strip()
        p2 = request.POST.get('password2', '').strip()

        if p1 == p2 and len(p1) >= 8:
            user = User.objects.get(email=request.session.get('reset_email'))
            user.set_password(p1)
            user.save()
            request.session.flush()
            messages.success(request, '')
            return redirect('login')
        else:
            messages.error(request, '')

    return render(request, 'password/password_reset_new.html')

