
from django.contrib import admin
from django.urls import path,include
from users .views import home
from users.views import register_view

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('users.urls')),
    path('', include('django.contrib.auth.urls')),
    path('jobs/', include('jobs.urls')),
    path('register/', register_view, name='register'),
]
