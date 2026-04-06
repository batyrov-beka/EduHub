
from django.urls import path
from . import views



urlpatterns = [
path('my-resume/', views.my_resume, name='edit_resume'),
path('resume/view/', views.view_resume, name='view_resume'),
path('resume/view/<int:resume_id>/', views.view_student_resume, name='view_student_resume'),
path('employer/dashboard/', views.employer_dashboard, name='employer_dashboard'),
path('apply/<int:job_id>/', views.apply_to_vacancy, name='apply_to_vacancy'),
path('vacancy/<int:id>/', views.vacancy_detail, name='vacancy_detail'),
path('my-applications/', views.student_applications, name='student_applications'),
path('application/<int:pk>/update/<str:status>/', views.update_status, name='update_status'),



]