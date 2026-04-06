from django.shortcuts import render,redirect,get_object_or_404
from .models import Job
from .forms import JobForm
from django.db.models import Q
from django.contrib.auth.decorators import login_required



def job_list(request):
    jobs = Job.objects.all().order_by('-created_at')
    return render(request, 'jobs/job_list.html', {'jobs': jobs})





def post_job(request):
    if request.method == "POST":
        form = JobForm(request.POST)
        if form.is_valid():
            job = form.save(commit=False)
            if request.user.is_authenticated:
                job.posted_by = request.user
            job.save()
            return redirect('job_list')
    else:
        form = JobForm()
    return render(request, 'jobs/post_job.html', {'form': form})




def vacancy_list(request):
    active_jobs = Job.objects.filter(is_active=True)

    query = request.GET.get('search', '').strip()

    if query:
        jobs = active_jobs.filter(
            Q(title__icontains=query) | Q(company__icontains=query)
        ).order_by('-created_at')
    else:
        jobs = active_jobs.order_by('-created_at')

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

    user_vacancies = Job.objects.filter(posted_by=request.user).order_by('-created_at')
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