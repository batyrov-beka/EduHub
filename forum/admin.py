from django.contrib import admin

from .models import Answer, Question


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'tags', 'created_at')
    search_fields = ('title', 'content', 'tags')
    list_select_related = ('author',)
    date_hierarchy = 'created_at'
    list_per_page = 25


@admin.register(Answer)
class AnswerAdmin(admin.ModelAdmin):
    list_display = ('author', 'question', 'created_at', 'is_accepted')
    list_filter = ('is_accepted', 'created_at')
    search_fields = ('content', 'question__title', 'author__username')
    list_select_related = ('author', 'question')
    list_per_page = 25
