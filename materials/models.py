from django.db import models

class Material(models.Model):
    title = models.CharField(max_length=255, verbose_name="Заголовок")
    slug = models.SlugField(unique=True, blank=True, verbose_name="Короткое имя для URL")
    image = models.ImageField(upload_to='materials/previews/', verbose_name="Фото")
    short_description = models.CharField(max_length=500, verbose_name="Краткая информация")
    content = models.TextField(verbose_name="Основной текст (статья)")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "Материал"
        verbose_name_plural = "Материал"
