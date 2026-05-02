from django.contrib import admin
from .models import Question, Answer

@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'created_at')
    search_fields = ('title', 'content')

@admin.register(Answer)
class AnswerAdmin(admin.ModelAdmin):
    list_display = ('author', 'question', 'created_at', 'is_accepted')