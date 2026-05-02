
from django.shortcuts import render, redirect ,get_object_or_404
from django.contrib.auth.decorators import login_required
from .forms import SignUpForm
from .forms import ResumeForm
from .models import Resume, Notification
from django.core.mail import send_mail
from django.contrib import messages
from .models import Job, Application
from jobs.models import Job
from django.http import HttpResponseForbidden
from django.conf import settings
from django.utils.translation import gettext as _
from django.core.paginator import Paginator
from django.urls import reverse



@login_required
def my_resume(request):
    resume, created = Resume.objects.get_or_create(user=request.user)
    if request.method == 'POST':
        form = ResumeForm(request.POST, request.FILES, instance=resume)
        if form.is_valid():
            form.save()
            messages.success(request, "Резюме успешно обновлено со всеми файлами!")
            return redirect('view_resume')
    else:
        form = ResumeForm(instance=resume)
    return render(request, 'resume/resume_form.html', {'form': form})



@login_required
def view_resume(request):
    if request.user.role != 'student':
        return HttpResponseForbidden("Доступ только для студентов.")

    try:
        resume = Resume.objects.get(user=request.user)
        return render(request, 'resume/resume_detail.html', {'resume': resume})
    except Resume.DoesNotExist:
        return redirect('my_resume')


def vacancy_detail(request, id):
    vacancy = get_object_or_404(Job, id=id)
    user_resumes = []
    if request.user.is_authenticated and request.user.role == 'student':
        user_resumes = Resume.objects.filter(user=request.user)

    return render(request, 'forms/vacancy_detail.html', {
        'vacancy': vacancy,
        'user_resumes': user_resumes,
    })


@login_required
def apply_to_vacancy(request, job_id):
    if request.method == 'POST':
        job = get_object_or_404(Job, id=job_id)
        resume = Resume.objects.filter(user=request.user).first()

        if not resume or not resume.full_name or resume.full_name.strip() == "":
            messages.error(request, _("Ваше резюме не заполнено! Сначала заполните его."))
            return redirect('my_resume')

        already_applied = Application.objects.filter(vacancy=job, student=request.user).exists()
        if already_applied:
            messages.warning(request, _("Вы уже подавали заявку на эту вакансию."))
            return redirect('vacancy_detail', id=job_id)

        Application.objects.create(
            vacancy=job,
            student=request.user,
            resume=resume
        )


        employer = job.posted_by
        if employer.email:
            full_name = request.user.get_full_name() or request.user.username

            dashboard_path = reverse('employer_dashboard')
            full_url = f"https://baiysh.pythonanywhere.com{dashboard_path}"

            subject = f"Новый отклик: {job.title}"
            message = (
                f"Здравствуйте, {employer.username}!\n\n"
                f"На вашу вакансию '{job.title}' поступил новый отклик.\n\n"
                f"👤 Кандидат: {full_name}\n"
                f"📂 Посмотреть отклики и резюме: {full_url}\n\n"
                f"С уважением, команда EduHub Jobs"
            )

            try:
                send_mail(
                    subject,
                    message,
                    settings.EMAIL_HOST_USER,
                    [employer.email],
                    fail_silently=False,
                )
            except Exception as e:
                print(f"Email Error: {e}")

        messages.success(request, _("Ваш отклик успешно отправлен!"))
        return redirect('vacancy_detail', id=job_id)

    return redirect('vacancy_list')


@login_required
def update_status(request, pk, status):
    application = get_object_or_404(Application, pk=pk)

    if application.vacancy.posted_by != request.user:
        return HttpResponseForbidden("Вы не можете менять статус этой заявки.")

    application.status = status
    application.save()

    student_email = application.student.email
    if student_email:
        student_dashboard_path = reverse('student_applications')
        full_url = f"https://baiysh.pythonanywhere.com{student_dashboard_path}"

        translations = {
            'accepted': 'Принята',
            'rejected': 'Отклонена',
            'pending': 'На рассмотрении'
        }
        status_text = translations.get(status, status)

        subject = f"Обновление статуса: {application.vacancy.title}"

        if status == 'accepted':
            body = f"Поздравляем! Ваша заявка на вакансию '{application.vacancy.title}' принята. Работодатель свяжется с вами."
        elif status == 'rejected':
            body = f"К сожалению, ваша заявка на вакансию '{application.vacancy.title}' отклонена."
        else:
            body = f"Статус вашей заявки на вакансию '{application.vacancy.title}' изменен на: {status_text}."

        message = (
            f"Здравствуйте, {application.student.username}!\n\n"
            f"{body}\n"
            f"Детали можете посмотреть в своем кабинете: {full_url}\n\n"
            f"С уважением, EduHub Jobs"
        )

        try:
            send_mail(
                subject,
                message,
                settings.EMAIL_HOST_USER,
                [student_email],
                fail_silently=True,
            )
        except Exception as e:
            print(f"Error sending email to student: {e}")

    messages.success(request, f"Статус заявки успешно изменен.")
    return redirect('employer_dashboard')


@login_required
def employer_dashboard(request):
    status_filter = request.GET.get('status')

    apps_list = Application.objects.filter(vacancy__posted_by=request.user).order_by('-created_at')
    if status_filter:
        apps_list = apps_list.filter(status=status_filter)
    paginator = Paginator(apps_list, 10)
    page_number = request.GET.get('page')

    applications = paginator.get_page(page_number)

    return render(request, 'forms/employer_dashboard.html', {
        'applications': applications,
        'current_status': status_filter
    })


@login_required
def student_applications(request):
    applications = Application.objects.filter(student=request.user).order_by('-created_at')
    return render(request, 'forms/student_applications.html', {'applications': applications})






@login_required
def view_student_resume(request, resume_id):
    resume = get_object_or_404(Resume, id=resume_id)
    return render(request, 'resume/resume_detail.html', {'resume': resume}) # <---- бул работадатель чектоо









