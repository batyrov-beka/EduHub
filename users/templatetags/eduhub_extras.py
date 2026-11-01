from django import template
from django.utils.translation import gettext as _

register = template.Library()


@register.filter
def color_index(value):
    """Компаниянын атына жараша туруктуу түс (логотип плиткасы үчүн)."""
    return sum(ord(c) for c in str(value)) % 6


@register.filter
def initials(value):
    parts = str(value).split()
    if not parts:
        return '?'
    if len(parts) == 1:
        return parts[0][:1].upper()
    return (parts[0][:1] + parts[1][:1]).upper()


@register.filter
def money(value):
    """30000 -> «30 000 сом», бош болсо «Договорная»."""
    if value in (None, ''):
        return _("Договорная")
    try:
        return f"{int(value):,}".replace(',', ' ') + ' ' + _("сом")
    except (TypeError, ValueError):
        return value


@register.filter
def percent(value, total):
    try:
        return round(int(value) * 100 / int(total)) if int(total) else 0
    except (TypeError, ValueError, ZeroDivisionError):
        return 0


@register.simple_tag(takes_context=True)
def active(context, *prefixes):
    path = context['request'].path
    return 'active' if any(p in path for p in prefixes) else ''


@register.filter
def ago(value):
    """«3 дня назад» — бир гана бирдик менен (timesince'тин кыскасы)."""
    from django.utils.timesince import timesince
    if not value:
        return ''
    return _("%(time)s назад") % {'time': timesince(value, depth=1)}
