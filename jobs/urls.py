from django.urls import path
from .views import job_list,post_job


urlpatterns = [
   path('job_list',job_list, name='job_list'),
path('post/', post_job, name='post_job'),
]