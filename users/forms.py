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

    class Meta(UserCreationForm.Meta):
        model = CustomUser
        fields = ("username", "email", "role", "university", "phone")


def clean_email(self):
    email = self.cleaned_data.get('email')
    if User.objects.filter(email=email).exists():
        raise forms.ValidationError("Этот адрес электронной почты уже занят!")
    return email