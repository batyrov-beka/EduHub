from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.utils.translation import gettext_lazy as _

from .models import CustomUser


class SignUpForm(UserCreationForm):
    email = forms.EmailField(label=_("Электронная почта"))
    role = forms.ChoiceField(choices=CustomUser.ROLE_CHOICES, label=_("Роль"))
    university = forms.CharField(label=_("Университет"), required=False)
    phone = forms.CharField(label=_("Номер телефона"), required=False)
    verification_data = forms.CharField(
        label=_("ИНН или Название компании"),
        required=False,
        widget=forms.Textarea(attrs={
            'placeholder': _('Если вы работодатель, введите ИНН или название вашей организации для проверки'),
            'rows': 2,
        }),
    )
    consent = forms.BooleanField(
        required=True,
        label=_("Я прочитал(а) политику конфиденциальности и согласен(на) на обработку моих персональных данных"),
        error_messages={'required': _("Чтобы зарегистрироваться, нужно дать согласие на обработку персональных данных.")},
    )

    class Meta(UserCreationForm.Meta):
        model = CustomUser
        fields = ("username", "email", "role", "university", "phone", "verification_data")

    def clean_email(self):
        email = self.cleaned_data.get('email', '').strip().lower()
        if CustomUser.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError(_("Этот адрес электронной почты уже зарегистрирован!"))
        return email

    def clean(self):
        cleaned = super().clean()
        if cleaned.get('role') == 'employer' and not cleaned.get('verification_data'):
            self.add_error('verification_data', _("Работодатель должен указать ИНН или название компании."))
        return cleaned

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.role = self.cleaned_data['role']
        user.university = self.cleaned_data.get('university')
        user.phone = self.cleaned_data.get('phone')
        user.verification_data = self.cleaned_data.get('verification_data')
        if commit:
            user.save()
        return user


class ProfileForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ('first_name', 'last_name', 'email', 'phone', 'university', 'profile_picture')
        labels = {
            'first_name': _("Имя"),
            'last_name': _("Фамилия"),
            'email': _("Электронная почта"),
            'phone': _("Номер телефона"),
            'university': _("Университет"),
            'profile_picture': _("Фото профиля"),
        }
        widgets = {'profile_picture': forms.FileInput()}
