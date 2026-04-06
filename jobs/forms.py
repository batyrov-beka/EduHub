from django import forms
from .models import Job


class JobForm(forms.ModelForm):
    class Meta:
        model = Job

        fields = ['title','phone', 'company', 'location', 'description', 'job_type', 'salary']


        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control',}),
            'phone': forms.TextInput(attrs={'class': 'form-control', }),
            'company': forms.TextInput(attrs={'class': 'form-control'}),
            'location': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'job_type': forms.Select(attrs={'class': 'form-select'}),
            'salary': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '30,000 сом'}),
        }