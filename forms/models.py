from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from PIL import Image


class Resume(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='resume'
    )
    full_name = models.CharField(max_length=255, verbose_name=_("ФИО"))
    phone = models.CharField(max_length=20, verbose_name=_("Номер телефона"))
    education = models.TextField(verbose_name=_("Образование"))
    experience = models.TextField(verbose_name=_("Опыт работы"))
    skills = models.TextField(verbose_name=_("Навыки (Skills)"))
    about_me = models.TextField(verbose_name=_("О себе"), blank=True)
    github_link = models.URLField(verbose_name=_("Ссылка на GitHub"), blank=True, null=True)

    photo = models.ImageField(upload_to='resumes/photos/', blank=True, null=True, verbose_name=_("Фото профиля"))

    def __str__(self):
        return f"Резюме: {self.full_name}"

    def get_absolute_url(self):
        return reverse('view_student_resume', args=[self.pk])

    @property
    def is_complete(self):
        return bool(self.full_name and self.full_name.strip() and self.phone and self.skills)

    @property
    def skills_list(self):
        import re
        return [s.strip() for s in re.split(r'[,;\n]', self.skills or '') if s.strip()]

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        if self.photo:
            try:
                img_path = self.photo.path
                img = Image.open(img_path)
                if img.height > 400 or img.width > 400:
                    output_size = (400, 400)
                    img.thumbnail(output_size)

                    if img.mode in ("RGBA", "P"):
                        img = img.convert("RGB")

                    img.save(img_path, quality=85, optimize=True)
            except Exception as e:
                print(f"Ошибка обработки изображения: {e}")

    class Meta:
        verbose_name = "Резюме"
        verbose_name_plural = "Резюме"


STATUS_CHOICES = (
    ('pending', _('На рассмотрении')),
    ('accepted', _('Принят')),
    ('rejected', _('Отклонен')),
)


class Application(models.Model):
    vacancy = models.ForeignKey('jobs.Job', on_delete=models.CASCADE, related_name='applications')
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='applications')
    resume = models.ForeignKey('Resume', on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name=_("Статус"))
    cover_letter = models.TextField(blank=True, null=True, verbose_name=_("Сопроводительное письмо"))
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        constraints = [
            models.UniqueConstraint(fields=['vacancy', 'student'], name='unique_application_per_vacancy'),
        ]
        verbose_name = _("Отклик")
        verbose_name_plural = _("Отклики")

    def __str__(self):
        return f"{self.student.username} -> {self.vacancy.title}"


class Notification(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Notification for {self.user.username}"
