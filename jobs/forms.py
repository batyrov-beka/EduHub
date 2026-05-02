import re
from django import forms
from django.core.exceptions import ValidationError
from .models import Job

class JobForm(forms.ModelForm):
    class Meta:
        model = Job
        fields = ['title', 'phone', 'company', 'location', 'description', 'category', 'job_type', 'salary']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+996......', 'type': 'tel'}),
            'company': forms.TextInput(attrs={'class': 'form-control'}),
            'location': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Например: г. Ош'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'job_type': forms.Select(attrs={'class': 'form-select'}),
            'salary': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '30000', 'type': 'number'}),
        }

    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        clean_phone = re.sub(r'[^\d+]', '', str(phone))
        if len(clean_phone) < 9:
            raise ValidationError("Число слишком короткое! Например: 0700123456")
        return clean_phone

    def clean_salary(self):
        salary = self.cleaned_data.get('salary')
        try:
            salary_int = int(salary)
            if salary_int < 1000:
                raise ValidationError("Ежемесячная зарплата должна составлять не менее 1000 сомов!")
        except (ValueError, TypeError):
            raise ValidationError("Пожалуйста, пишите только цифры.")
        return salary

    def clean_location(self):
        location = self.cleaned_data.get('location')
        if len(location) < 3:
            raise ValidationError("Укажите полное местоположение (например:Бишкек)")
        return location