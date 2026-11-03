from django.conf import settings
from django.conf.urls.i18n import i18n_patterns
from django.contrib import admin
from django.urls import include, path, re_path
from django.views.static import serve

from eduhub import admin_site

admin_site.setup()

urlpatterns = [
    path('i18n/', include('django.conf.urls.i18n')),
]

urlpatterns += i18n_patterns(
    path('admin/', admin.site.urls),
    path('', include('users.urls')),
    path('', include('django.contrib.auth.urls')),
    path('forms/', include('forms.urls')),
    path('jobs/', include('jobs.urls')),
    path('Dashboard/', include('Dashboard.urls')),
    path('materials/', include('materials.urls')),
    path('forum/', include('forum.urls')),
    prefix_default_language=True,
)

urlpatterns += [
    re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),
]
