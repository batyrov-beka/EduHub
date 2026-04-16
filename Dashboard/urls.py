from django.urls import path
from . import views

urlpatterns = [
    path('control/', views.admin_control, name='admin_control'),

    path('approve/<int:user_id>/', views.approve_user, name='approve_user'),

    path('reject-user/<int:user_id>/', views.reject_user, name='reject_user'),

    path('waiting-approval/', views.waiting_approval, name='waiting_approval'),

path('send-broadcast/', views.send_broadcast, name='send_broadcast'),
path('delete-user/<int:user_id>/', views.delete_user, name='delete_user'),
path('toggle-block/<int:user_id>/', views.toggle_user_block, name='toggle_user_block'),



]