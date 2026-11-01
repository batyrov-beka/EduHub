from django.conf import settings
from django.core.validators import RegexValidator
from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

phone_regex = RegexValidator(
    regex=r'^\+?\d{9,13}$',
    message=_("Номер телефона указан в неправильном формате. Например: +996700123456"),
)


class Job(models.Model):
    JOB_TYPE = (
        ('Full-time', _('Полный рабочий день')),
        ('Part-time', _('Пол дня работы')),
        ('Internship', _('Стажировка')),
        ('Remote', _('Работайте удаленно')),
    )

    CATEGORY_CHOICES = [
        ('it', _('IT / Программирование')),
        ('marketing', _('Маркетинг')),
        ('admin', _('Администрация')),
        ('design', _('Дизайн')),
        ('other', _('Другие')),
    ]

    title = models.CharField(max_length=200, verbose_name=_("Должность"))
    phone = models.CharField(validators=[phone_regex], max_length=15, verbose_name=_("Номер телефона"))
    company = models.CharField(max_length=100, verbose_name=_("Компания"))
    location = models.CharField(max_length=100, verbose_name=_("Город/Местоположение"))
    description = models.TextField(verbose_name=_("Информация о вакансии"))
    job_type = models.CharField(max_length=20, choices=JOB_TYPE, default='Internship', verbose_name=_("Тип занятости"))
    salary = models.PositiveIntegerField(null=True, blank=True, verbose_name=_("Зарплата (сом)"))
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='it', verbose_name=_("Категория"))

    is_active = models.BooleanField(default=True, verbose_name=_("Активна"))
    posted_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='jobs')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = _("Вакансия")
        verbose_name_plural = _("Вакансии")

    def __str__(self):
        return f"{self.title} - {self.company}"

    def get_absolute_url(self):
        return reverse('vacancy_detail', args=[self.pk])

    @property
    def whatsapp_phone(self):
        return ''.join(ch for ch in self.phone if ch.isdigit())
