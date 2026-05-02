from django.db import models
from django.conf import settings
from django.core.validators import RegexValidator

phone_regex = RegexValidator(
    regex=r'^\+?1?\d{9,13}$',
    message="Номер телефона указан в неправильном формате. Например:+996700123456"
)

class Job(models.Model):
    JOB_TYPE = (
        ('Full-time', 'Полный рабочий день'),
        ('Part-time', 'Пол дня работы'),
        ('Internship', 'Стажировка'),
        ('Remote', 'Работайте удаленно'),
    )

    CATEGORY_CHOICES = [
        ('it', 'IT / Программирование'),
        ('marketing', 'Маркетинг'),
        ('admin', 'Администрация'),
        ('design', 'Дизайн '),
        ('other', 'Другие'),
    ]

    title = models.CharField(max_length=200, verbose_name="Должность")
    phone = models.CharField(validators=[phone_regex], max_length=15)
    # phone = models.CharField(max_length=20, verbose_name="Номер телефона")
    company = models.CharField(max_length=100, verbose_name="Компания")
    location = models.CharField(max_length=100, verbose_name="Город/Местоположение")
    description = models.TextField(verbose_name="Информация о вакансии")
    job_type = models.CharField(max_length=20, choices=JOB_TYPE, default='Internship',verbose_name="Категория")
    salary = models.PositiveIntegerField(verbose_name="Зарплата (сом)")

    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='it', verbose_name="Категория")

    is_active = models.BooleanField(default=True)
    posted_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} - {self.company}"