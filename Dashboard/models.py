from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _


class Notification(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='admin_notifications',
    )
    message = models.TextField(verbose_name=_("Сообщение"))
    link = models.CharField(max_length=255, blank=True, verbose_name=_("Ссылка"))
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']
        verbose_name = _("Уведомление")
        verbose_name_plural = _("Уведомления")

    def __str__(self):
        return f"Билдирүү: {self.user.username}"


def notify(user, message, link=''):
    """Колдонуучуга сайттын ичиндеги билдирүү түзүү."""
    return Notification.objects.create(user=user, message=str(message), link=link)
