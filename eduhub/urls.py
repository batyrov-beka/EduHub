
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path,include
from users .views import home
from users.views import register_view

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('users.urls')),
    path('', include('django.contrib.auth.urls')),

    # path('materials/', include('materials.urls')),

    path('forms/', include('forms.urls')),
    path('jobs/', include('jobs.urls')),
    path('register/', register_view, name='register'),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
