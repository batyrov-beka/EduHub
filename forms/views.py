
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


@login_required
def apply_to_vacancy(request, job_id):
    job = get_object_or_404(Job, id=job_id)
    resume = Resume.objects.filter(user=request.user).first()

    if not resume:
        messages.error(request, "Сначала создайте резюме!")
        return redirect('my_resume')

    already_applied = Application.objects.filter(vacancy=job, student=request.user).exists()

    if already_applied:
        messages.warning(request, "Вы уже подавали заявку на эту вакансию.")
    else:
        Application.objects.create(
            vacancy=job,
            student=request.user,
            resume=resume
        )

        try:
            if job.employer.email:
                subject = f"Новый кандидат на вакансию: {job.title}"
                message = (
                    f"Здравствуйте, {job.employer.username}!\n\n"
                    f"На вашу вакансию '{job.title}' поступил новый отклик.\n"
                    f"Кандидат: {request.user.get_full_name() or request.user.username}\n"
                    f"Email кандидата: {request.user.email}\n\n"
                    f"Детали можно посмотреть в личном кабинете на сайте."
                )
                send_mail(
                    subject,
                    message,
                    settings.EMAIL_HOST_USER,
                    [job.employer.email],
                    fail_silently=False
                )
                messages.success(request, "Отклик отправлен, работодатель уведомлен по почте!")
            else:
                messages.warning(request, "Отклик принят, но у работодателя не указан Email.")

        except Exception as e:
            print(f"Email Error: {e}")
            messages.error(request, "Отклик сохранен, но произошла ошибка при отправке почты.")

    return redirect('vacancy_detail', id=job_id)


def vacancy_detail(request, id):
    vacancy = get_object_or_404(Job, id=id)
    user_resumes = Resume.objects.filter(user=request.user) if request.user.is_authenticated else []

    return render(request, 'forms/vacancy_detail.html', {
        'vacancy': vacancy,
        'user_resumes': user_resumes
    })


@login_required
def update_status(request, pk, status):
    application = get_object_or_404(Application, pk=pk)

    if application.vacancy.posted_by != request.user:
        return HttpResponseForbidden("Вы не можете менять статус этой заявки.")

    application.status = status
    application.save()

    translations = {
        'accepted': 'принята',
        'rejected': 'отклонена',
        'pending': 'на рассмотрении'
    }

    ru_status = translations.get(status, status)
    messages.success(request, f"Статус заявки успешно изменен на: {ru_status}")

    return redirect('employer_dashboard')


@login_required
def employer_dashboard(request):
    if request.user.role != 'employer':
        return HttpResponseForbidden("Доступ только для работодателей!")

    applications = Application.objects.filter(
        vacancy__posted_by=request.user
    ).order_by('-created_at')

    return render(request, 'forms/employer_dashboard.html', {
        'applications': applications
    })


@login_required
def student_applications(request):
    applications = Application.objects.filter(student=request.user).order_by('-created_at')
    return render(request, 'forms/student_applications.html', {'applications': applications})






@login_required
def view_student_resume(request, resume_id):
    resume = get_object_or_404(Resume, id=resume_id)
    return render(request, 'resume/resume_detail.html', {'resume': resume}) # <---- бул работадатель чектоо









