from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include

import materials
from users.views import register_view
from django.conf.urls.i18n import i18n_patterns


urlpatterns = [
    path('i18n/', include('django.conf.urls.i18n')),
]
urlpatterns += i18n_patterns(
    path('admin/', admin.site.urls),
    path('', include('users.urls')),
    path('', include('django.contrib.auth.urls')),

    path('forms/', include('forms.urls')),
    path('jobs/', include('jobs.urls')),
    path('register/', register_view, name='register'),

path('Dashboard/', include('Dashboard.urls')),

    path('materials/',include('materials.urls')),
    path('forum/',include('forum.urls')),


    prefix_default_language=True
)

if settings.DEBUG or True:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)