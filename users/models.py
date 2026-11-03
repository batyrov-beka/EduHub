
from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models


class CustomUser(AbstractUser):
    ROLE_CHOICES = (
        ('student', 'Студент'),
        ('employer', 'Работадатель'),
    )
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        null=True,
        blank=True
    )
    university = models.CharField(max_length=255, blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)

    is_verified = models.BooleanField(default=False)
    is_blocked = models.BooleanField(default=False)
    verification_data = models.TextField(blank=True, null=True, verbose_name="Маалыматтар (ИНН/Компания)")
    consent_at = models.DateTimeField(null=True, blank=True, verbose_name="Жеке маалыматка макулдук берилген убакыт")

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"

    @property
    def is_student(self):
        return self.role == 'student'

    @property
    def is_employer(self):
        return self.role == 'employer'

    @property
    def display_name(self):
        return self.get_full_name() or self.username


class PasswordResetOTP(models.Model):

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    otp_code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.email} - {self.otp_code}"


class EmailOTP(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='email_otp'
    )
    otp_code = models.CharField(max_length=6)
    attempts = models.PositiveSmallIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.email} - {self.otp_code}"
