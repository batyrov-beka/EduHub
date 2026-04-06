from django.db import models
from django.conf import settings
from jobs.models import Job

class Resume(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='resume'
    )
    full_name = models.CharField(max_length=255, verbose_name="ФИО")
    phone = models.CharField(max_length=20, verbose_name="Номер телефона")
    education = models.TextField(verbose_name="Образование")
    experience = models.TextField(verbose_name="Опыт работы")
    skills = models.TextField(verbose_name="Навыки (Skills)")
    about_me = models.TextField(verbose_name="О себе", blank=True)
    github_link = models.URLField(verbose_name="Ссылка на GitHub", blank=True, null=True)

    photo = models.ImageField(upload_to='resumes/photos/', blank=True, null=True, verbose_name="Фото профиля")

    def __str__(self):
        return f"Резюме: {self.full_name}"

    class Meta:
        verbose_name = "Резюме"
        verbose_name_plural = "Резюме"

STATUS_CHOICES = (
    ('pending', 'На рассмотрении'),
    ('accepted', 'Принят'),
    ('rejected', 'Отклонен'),
)

class Application(models.Model):
    vacancy = models.ForeignKey('jobs.Job', on_delete=models.CASCADE, related_name='applications')
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    resume = models.ForeignKey('Resume', on_delete=models.CASCADE)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name="Статус"
    )
    cover_letter = models.TextField(blank=True, null=True, verbose_name="Дополнительное уведомление")
    created_at = models.DateTimeField(auto_now_add=True)

class Meta:
        unique_together = ('vacancy', 'student')

def __str__(self):
        return f"{self.student.username} -> {self.vacancy.title}"


class Notification(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Notification for {self.user.username}"
