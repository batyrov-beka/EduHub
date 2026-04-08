import random
from datetime import datetime, timedelta
from django.shortcuts import render, redirect ,get_object_or_404
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth import get_user_model, login
from jobs.models import Job
from .forms import SignUpForm
User = get_user_model()



def home(request):
    latest_jobs = Job.objects.all().order_by('-created_at')
    return render(request, 'home.html', {'jobs': latest_jobs})


def register_view(request):
    if request.method == "POST":
        form = SignUpForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data.get('email')
            if User.objects.filter(email=email).exists():
                form.add_error('email', "Этот адрес электронной почты уже зарегистрирован!")
                return render(request, 'registration/register.html', {'form': form})
            user = form.save()
            login(request, user)
            return redirect('home')
    else:
        form = SignUpForm()
    return render(request, 'registration/register.html', {'form': form})


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

