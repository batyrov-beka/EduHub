from django.shortcuts import render
from django.urls import reverse


class VerificationMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:

            if request.user.is_superuser:
                return self.get_response(request)

            if request.user.role == 'employer' and not request.user.is_verified:

                allowed_urls = [
                    reverse('logout'),

                ]

                if request.path not in allowed_urls and not request.path.startswith('/admin/'):
                    return render(request, 'verification/waiting_approval.html')

        response = self.get_response(request)
        return response