from django.urls import path
from . import views

urlpatterns = [
    path('', views.QuestionListView.as_view(), name='question_list'),
    path('question/<int:pk>/', views.question_detail, name='question_detail'),
    path('ask/', views.QuestionCreateView.as_view(), name='question_ask'),
path('answer/<int:pk>/accept/', views.accept_answer, name='accept_answer'),
path('answer/<int:pk>/like/', views.like_answer, name='like_answer'),
path('answer/<int:pk>/dislike/', views.dislike_answer, name='dislike_answer'),
path('question/<int:pk>/delete/', views.delete_question, name='delete_question'),
]