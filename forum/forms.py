from django import forms
from .models import Answer

class AnswerForm(forms.ModelForm):
    class Meta:
        model = Answer
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={
                'class': 'answer-input',
                'placeholder': 'Напишите ваш ответ здесь...',
                'rows': 4
            }),
        }