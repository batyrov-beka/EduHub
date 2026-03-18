from django.urls import path
from . import views
urlpatterns = [
    path('', views.home, name='home'),
path('auth/register/', views.register_view, name='register'),
    path('auth/recovery/', views.password_reset_form, name='custom_reset_form'),
    path('auth/verify-code/', views.password_reset_otp, name='custom_reset_otp'),
    path('resend-otp/', views.resend_otp, name='resend_otp'),
    path('auth/set-new-pass/', views.password_reset_new, name='custom_reset_new'),

]