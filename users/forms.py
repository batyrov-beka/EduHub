from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser


class SignUpForm(UserCreationForm):
    email = forms.EmailField(label="Электронная почта")
    role = forms.ChoiceField(
        choices=CustomUser.ROLE_CHOICES,
        label="Роль",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    university = forms.CharField(label="Университет", required=False)
    phone = forms.CharField(label="Номер телефона", required=False)
    verification_data = forms.CharField(
        label="ИНН или Название компании",
        required=False,
        widget=forms.Textarea(attrs={
            'placeholder': 'Если вы работодатель, введите ИНН или название вашей организации для проверки',
            'rows': 2,
            'class': 'form-control'
        })
    )

    class Meta(UserCreationForm.Meta):
        model = CustomUser
        fields = ("username", "email", "role", "university", "phone", "verification_data")

    def save(self, commit=True):
        user = super().save(commit=False)
        user.verification_data = self.cleaned_data.get('verification_data')
        if commit:
            user.save()
        return user


def clean_email(self):
    email = self.cleaned_data.get('email')
    if User.objects.filter(email=email).exists():
        raise forms.ValidationError("Этот адрес электронной почты уже занят!")
    return email