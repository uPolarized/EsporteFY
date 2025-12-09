from django.conf import settings

def recaptcha_keys(request):
    return {
        'RECAPTCHA_PUBLIC_KEY': getattr(settings, 'RECAPTCHA_PUBLIC_KEY', None),
    }
