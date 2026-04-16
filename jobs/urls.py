from django.urls import path
from .views import job_list,post_job
from .import views

urlpatterns = [
    path('', views.vacancy_list, name='vacancy_list'),
    path('jobs/job_list/', views.vacancy_list, name='job_list'),
    path('post/', views.post_job, name='post_job'),
    path('profile/', views.profile_view, name='profile'),
    path('close-vacancy/<int:pk>/', views.close_vacancy, name='close_vacancy'),
path('reopen-vacancy/<int:pk>/', views.reopen_vacancy, name='reopen_vacancy'),
path('edit-vacancy/<int:pk>/', views.edit_vacancy, name='edit_vacancy'),
path('delete-job/<int:pk>/', views.delete_job, name='delete_job'),
]