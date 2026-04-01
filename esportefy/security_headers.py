from django.conf import settings


class SecurityHeadersMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        if getattr(settings, 'CSP_REPORT_ONLY_ENABLED', False):
            policy = getattr(settings, 'CSP_REPORT_ONLY_POLICY', '')
            if policy:
                response['Content-Security-Policy-Report-Only'] = policy

        # Endurece isolamento e permissões por padrão.
        response.setdefault('Cross-Origin-Resource-Policy', 'same-site')
        response.setdefault('Cross-Origin-Opener-Policy', 'same-origin')
        response.setdefault('Permissions-Policy', 'geolocation=(), microphone=(), camera=()')

        return response
