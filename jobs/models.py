from django.db import models
from django.conf import settings


class Job(models.Model):

    JOB_TYPE = (
        ('Full-time', 'Полный рабочий день'),
        ('Part-time', 'Пол дня работы'),
        ('Internship', 'Стажировка'),
        ('Remote', 'Работайте удаленно'),
    )

    title = models.CharField(max_length=200, verbose_name="Должность")
    company = models.CharField(max_length=100, verbose_name="Компания")
    location = models.CharField(max_length=100, verbose_name="Город/Местоположение")
    description = models.TextField(verbose_name="Информация о вакансии")
    job_type = models.CharField(max_length=20, choices=JOB_TYPE, default='Internship')
    salary = models.CharField(max_length=50, blank=True, null=True, verbose_name="Зарплата (Например: 30к-50к)")


    posted_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} - {self.company}"