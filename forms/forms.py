from django import forms
from django.utils.translation import gettext_lazy as _

from .models import Resume


class ResumeForm(forms.ModelForm):
    class Meta:
        model = Resume
        fields = ['full_name', 'photo', 'phone', 'github_link', 'education', 'experience', 'skills', 'about_me']
        widgets = {
            'full_name': forms.TextInput(attrs={'placeholder': _('Ваше ФИО')}),
            'phone': forms.TextInput(attrs={'placeholder': '+996 ...', 'type': 'tel'}),
            'github_link': forms.URLInput(attrs={'placeholder': 'https://github.com/username'}),
            'education': forms.Textarea(attrs={'rows': 3, 'placeholder': _('Место обучения (ВУЗ, курсы)...')}),
            'experience': forms.Textarea(attrs={'rows': 3, 'placeholder': _('Ваш опыт работы или проекты...')}),
            'skills': forms.Textarea(attrs={'rows': 2, 'placeholder': _('Python, Django, SQL и др.')}),
            'about_me': forms.Textarea(attrs={'rows': 3, 'placeholder': _('Кратко о себе...')}),
            'photo': forms.FileInput(attrs={'accept': 'image/*'}),
        }
        help_texts = {
            'skills': _('Перечислите навыки через запятую.'),
        }

    def clean_full_name(self):
        name = self.cleaned_data.get('full_name', '').strip()
        if len(name) < 3:
            raise forms.ValidationError(_("Укажите полное имя."))
        return name


class ApplyForm(forms.Form):
    cover_letter = forms.CharField(
        required=False,
        max_length=2000,
        widget=forms.Textarea(attrs={
            'rows': 4,
            'placeholder': _('Коротко расскажите, почему вы подходите на эту вакансию (необязательно)'),
        }),
    )
