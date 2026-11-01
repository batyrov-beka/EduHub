from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.utils.translation import gettext as _


def role_required(role):
    """Бетке белгилүү ролдогу колдонуучу гана кире алат (student / employer)."""
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def wrapper(request, *args, **kwargs):
            if request.user.role != role and not request.user.is_superuser:
                messages.error(request, _("У вас нет доступа к этой странице."))
                return redirect('home')
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


student_required = role_required('student')
employer_required = role_required('employer')
