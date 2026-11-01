from django.urls import path

from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('verify-email/', views.verify_otp, name='verify_otp'),
    path('verify-email/resend/', views.resend_registration_otp, name='resend_registration_otp'),
    path('auth/recovery/', views.password_reset_form, name='custom_reset_form'),
    path('auth/verify-code/', views.password_reset_otp, name='custom_reset_otp'),
    path('auth/resend-code/', views.resend_otp, name='resend_otp'),
    path('auth/set-new-pass/', views.password_reset_new, name='custom_reset_new'),
    path('account/settings/', views.account_settings, name='account_settings'),
]
