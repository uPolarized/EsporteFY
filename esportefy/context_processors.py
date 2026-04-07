from django.conf import settings
import hmac
import hashlib
import time


def _build_ws_token(request):
    user = getattr(request, 'user', None)
    if not user or not user.is_authenticated:
        return ''

    ts = int(time.time())
    payload = f"{user.id}:{user.username}:{ts}"
    signature = hmac.new(
        settings.SECRET_KEY.encode('utf-8'),
        payload.encode('utf-8'),
        hashlib.sha256,
    ).hexdigest()
    return f"{payload}:{signature}"


def recaptcha_keys(request):
    return {
        'RECAPTCHA_PUBLIC_KEY': getattr(settings, 'RECAPTCHA_PUBLIC_KEY', None),
        'WS_AUTH_TOKEN': _build_ws_token(request),
        'giphy_api_key': getattr(settings, 'GIPHY_API_KEY', 'dc6zaTOxFJmzC'),
    }


def login_greeting_popup(request):
    popup = None
    user = getattr(request, 'user', None)
    is_authenticated = bool(user and user.is_authenticated)
    is_feed_route = request.path.startswith('/feed')

    # Consome a saudação apenas no feed autenticado para não perder em redirects intermediários.
    if is_authenticated and is_feed_route:
        popup = request.session.pop('login_greeting_popup', None)

    return {
        'login_greeting_popup': popup,
    }
