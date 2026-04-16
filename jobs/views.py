from django.shortcuts import render,redirect,get_object_or_404
from .models import Job
from .forms import JobForm
from django.db.models import Q
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.utils import translation



def job_list(request):
    jobs = Job.objects.all().order_by('-created_at')
    return render(request, 'jobs/job_list.html', {'jobs': jobs})




#
# def post_job(request):
#     if request.method == "POST":
#         form = JobForm(request.POST)
#         if form.is_valid():
#             job = form.save(commit=False)
#             if request.user.is_authenticated:
#                 job.posted_by = request.user
#             job.save() # Вакансия базага сакталды!
#
#             # --- МЫНА УШУЛ ЖЕРГЕ ТЕЛЕГРАМДЫ ЧАКЫРАБЫЗ ---
#             try:
#                 # job.company бул сенин Моделиңдеги компаниянын аты жазылган талаа болушу керек
#                 send_telegram_notification(job.title, job.company)
#             except:
#                 pass
#             # -------------------------------------------
#
#             return redirect('job_list')
#     else:
#         form = JobForm()
#     return render(request, 'jobs/post_job.html', {'form': form})


@login_required
def vacancy_list(request):
    user_language = translation.get_language_from_request(request)
    translation.activate(user_language)

    active_jobs = Job.objects.filter(is_active=True).order_by('-created_at')
    query = request.GET.get('search', '').strip()

    if query:
        jobs = active_jobs.filter(
            Q(title__icontains=query) | Q(company__icontains=query)
        )
    else:
        jobs = active_jobs

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return render(request, 'jobs/job_list_partial.html', {'jobs': jobs})

    return render(request, 'jobs/job_list.html', {'jobs': jobs})


@login_required
def close_vacancy(request, pk):
    job = get_object_or_404(Job, pk=pk, posted_by=request.user)
    job.is_active = False
    job.save()
    return redirect('profile')


@login_required
def profile_view(request):
    if request.user.role == 'student':
        return redirect('vacancy_list')

    vacancies_list = Job.objects.filter(posted_by=request.user).order_by('-created_at')
    paginator = Paginator(vacancies_list, 5)
    page_number = request.GET.get('page')
    user_vacancies = paginator.get_page(page_number)

    return render(request, 'vacancy/profile.html', {'user_vacancies': user_vacancies})



    

@login_required
def reopen_vacancy(request, pk):
    job = get_object_or_404(Job, pk=pk, posted_by=request.user)
    job.is_active = True
    job.save()
    return redirect('profile')




@login_required
def edit_vacancy(request, pk):
    job = get_object_or_404(Job, pk=pk, posted_by=request.user)

    if request.method == 'POST':
        job.title = request.POST.get('title')
        job.company = request.POST.get('company')
        job.location = request.POST.get('location')
        job.phone = request.POST.get('phone')
        job.salary = request.POST.get('salary')
        job.description = request.POST.get('description')
        new_job_type = request.POST.get('job_type')
        if new_job_type:
            job.job_type = new_job_type

        if request.FILES.get('company_logo'):
            job.company_logo = request.FILES.get('company_logo')

        job.save()
        return redirect('profile')

    return render(request, 'vacancy/edit_job.html', {'job': job})


def delete_job(request, pk):
    job = get_object_or_404(Job, pk=pk)
    if request.method == 'POST':
        job.delete()
    return redirect('admin_control')


import requests


def send_telegram_notification(job_title, company_name):
    token = "8671398522:AAF2pivRcTTAm6Ytl-77EExSFrxheNWZIt4"
    chat_id = "@eduhub_kg_jobs"

    message = (
        f"🚀 **НОВАЯ ВАКАНСИЯ!**\n\n"
        f"📌 Услуга: {job_title}\n"
        f"🏢 Компания: {company_name}\n\n"
        f"🔗 [Читать с сайта](http://127.0.0.1:8000/ru/jobs/)"
    )

    url = f"https://api.telegram.org/bot{token}/sendMessage"

    try:
        response = requests.post(url, data={'chat_id': chat_id, 'text': message, 'parse_mode': 'Markdown'}, timeout=10)
        print(f"TELEGRAM STATUS: {response.status_code}, RESPONSE: {response.text}")
    except Exception as e:
        print(f"TELEGRAM ERROR: {e}")


def post_job(request):
    if request.method == "POST":
        form = JobForm(request.POST)
        if form.is_valid():
            job = form.save(commit=False)
            if request.user.is_authenticated:
                job.posted_by = request.user
            job.save()
            try:

                comp = str(job.company) if hasattr(job, 'company') else "Неизвестная компания"
                send_telegram_notification(job.title, comp)
            except Exception as e:
                print(f"NOTIFICATION ERROR: {e}")

            return redirect('job_list')
    else:
        form = JobForm()
    return render(request, 'jobs/post_job.html', {'form': form})