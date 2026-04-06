from django import forms
from django.contrib.auth.forms import UserCreationForm
from users.models import CustomUser
from .models import Resume


class SignUpForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = CustomUser
        fields = ("username", "email", "role", "university", "phone")

class ResumeForm(forms.ModelForm):
    class Meta:
        model = Resume
        fields = ['full_name', 'photo', 'phone', 'education', 'experience', 'skills', 'about_me', 'github_link']

        widgets = {
            'full_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ваше ФИО'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+996 ...'
            }),
            'github_link': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://github.com/username'
            }),
            'education': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Место обучения (ВУЗ, курсы)...'
            }),
            'experience': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Ваш опыт работы или проекты...'
            }),
            'skills': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Python, Django, SQL и др.'
            }),
            'about_me': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Кратко о себе...'
            }),

            'photo': forms.FileInput(attrs={'class': 'form-control'}),
        }



