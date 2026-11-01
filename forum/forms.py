from django import forms
from django.utils.translation import gettext_lazy as _

from .models import Answer, Question


class QuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = ['title', 'content', 'tags']
        widgets = {
            'title': forms.TextInput(attrs={'placeholder': _('Например: Как подготовиться к первому собеседованию?')}),
            'content': forms.Textarea(attrs={'rows': 8, 'placeholder': _('Опишите ваш вопрос подробно...')}),
            'tags': forms.TextInput(attrs={'placeholder': 'python django карьера'}),
        }
        help_texts = {'tags': _('Через пробел, например: python карьера стажировка')}


class AnswerForm(forms.ModelForm):
    class Meta:
        model = Answer
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={'placeholder': _('Напишите ваш ответ здесь...'), 'rows': 4}),
        }
