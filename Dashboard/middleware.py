from django.shortcuts import render


class VerificationMiddleware:

    ALLOWED_PARTS = ('/admin/', '/static/', '/media/', '/i18n/', '/logout/', '/waiting-approval/', '/privacy/', '/account/')

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = request.user
        if (
            user.is_authenticated
            and not user.is_superuser
            and user.role == 'employer'
            and not user.is_verified
            and not any(part in request.path for part in self.ALLOWED_PARTS)
        ):
            return render(request, 'verification/waiting_approval.html')
        return self.get_response(request)
