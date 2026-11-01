import re

from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from .models import Job


class JobForm(forms.ModelForm):
    class Meta:
        model = Job
        fields = ['title', 'company', 'category', 'job_type', 'location', 'salary', 'phone', 'description']
        widgets = {
            'title': forms.TextInput(attrs={'placeholder': _('Например: Junior Python-разработчик')}),
            'company': forms.TextInput(attrs={'placeholder': _('Название компании')}),
            'phone': forms.TextInput(attrs={'placeholder': '+996700123456', 'type': 'tel'}),
            'location': forms.TextInput(attrs={'placeholder': _('Например: г. Ош')}),
            'description': forms.Textarea(attrs={
                'rows': 7,
                'placeholder': _('Обязанности, требования, условия работы...'),
            }),
            'salary': forms.NumberInput(attrs={'placeholder': '30000', 'min': 0}),
        }
        help_texts = {
            'salary': _('Оставьте пустым, если зарплата договорная.'),
        }

    def clean_phone(self):
        phone = re.sub(r'[^\d+]', '', str(self.cleaned_data.get('phone', '')))
        if len(phone.lstrip('+')) < 9:
            raise ValidationError(_("Номер слишком короткий! Например: +996700123456"))
        return phone

    def clean_salary(self):
        salary = self.cleaned_data.get('salary')
        if salary is not None and salary < 1000:
            raise ValidationError(_("Ежемесячная зарплата должна составлять не менее 1000 сомов!"))
        return salary

    def clean_location(self):
        location = self.cleaned_data.get('location', '').strip()
        if len(location) < 2:
            raise ValidationError(_("Укажите полное местоположение (например: Бишкек)"))
        return location


class JobFilterForm(forms.Form):
    SORT_CHOICES = (
        ('new', _('Сначала новые')),
        ('salary_desc', _('По зарплате (убыв.)')),
        ('salary_asc', _('По зарплате (возр.)')),
    )
    search = forms.CharField(required=False)
    category = forms.ChoiceField(required=False, choices=[('', _('Все категории'))] + list(Job.CATEGORY_CHOICES))
    job_type = forms.ChoiceField(required=False, choices=[('', _('Любой тип'))] + list(Job.JOB_TYPE))
    location = forms.CharField(required=False)
    salary_min = forms.IntegerField(required=False, min_value=0)
    sort = forms.ChoiceField(required=False, choices=SORT_CHOICES)
