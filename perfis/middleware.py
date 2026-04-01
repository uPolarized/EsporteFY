from django.conf import settings
from django.shortcuts import redirect
from django.urls import reverse
from django.utils import timezone

from .consent import has_required_consents


class RequireLgpdConsentMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = getattr(request, "user", None)
        if not user or not user.is_authenticated:
            return self.get_response(request)

        if self._is_exempt_path(request.path):
            return self.get_response(request)

        if has_required_consents(user):
            return self.get_response(request)

        return redirect(f"{reverse('lgpd_hub')}?tab=meus-dados")

    @staticmethod
    def _is_exempt_path(path):
        if path.startswith(settings.STATIC_URL) or path.startswith(settings.MEDIA_URL):
            return True

        exempt_prefixes = (
            "/accounts/",
            "/lgpd/",
            "/admin/",
        )
        return path.startswith(exempt_prefixes)


class TrackSessionSecurityMetadataMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = getattr(request, 'user', None)
        if user and user.is_authenticated:
            request.session['_device_ip'] = self._resolve_client_ip(request)
            request.session['_device_ua'] = (request.META.get('HTTP_USER_AGENT', '') or '')[:255]
            request.session['_device_last_seen'] = timezone.now().isoformat()

        return self.get_response(request)

    @staticmethod
    def _resolve_client_ip(request):
        forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if forwarded_for:
            return forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR', '')
