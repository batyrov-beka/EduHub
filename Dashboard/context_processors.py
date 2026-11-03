from django.conf import settings


def notifications(request):
    """Навбардагы окулбаган билдирүүлөрдүн саны (бардык барактарда)."""
    user = getattr(request, 'user', None)
    if user is None or not user.is_authenticated:
        return {}
    return {'unread_notifications': user.admin_notifications.filter(is_read=False).count()}


def telegram_channel(request):
    """Telegram каналына шилтеме (футер жана башкы бет үчүн)."""
    return {'TELEGRAM_CHANNEL_URL': getattr(settings, 'TELEGRAM_CHANNEL_URL', '')}
