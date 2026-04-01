import base64
import hashlib
from typing import Tuple

from django.conf import settings
from django.core.cache import cache


ENCRYPTION_PREFIX = "enc::"


def _get_fernet():
    try:
        from cryptography.fernet import Fernet
    except Exception:
        return None

    configured_key = getattr(settings, "SOCIAL_CONTENT_ENCRYPTION_KEY", "") or ""
    if configured_key:
        key_bytes = configured_key.encode("utf-8")
    else:
        digest = hashlib.sha256(settings.SECRET_KEY.encode("utf-8")).digest()
        key_bytes = base64.urlsafe_b64encode(digest)

    try:
        return Fernet(key_bytes)
    except Exception:
        return None


def encrypt_text(value: str) -> str:
    text = (value or "").strip()
    if not text:
        return ""
    fernet = _get_fernet()
    if not fernet:
        return text
    token = fernet.encrypt(text.encode("utf-8")).decode("utf-8")
    return f"{ENCRYPTION_PREFIX}{token}"


def decrypt_text(value: str) -> str:
    text = value or ""
    if not text.startswith(ENCRYPTION_PREFIX):
        return text
    fernet = _get_fernet()
    if not fernet:
        return ""

    token = text[len(ENCRYPTION_PREFIX):]
    try:
        return fernet.decrypt(token.encode("utf-8")).decode("utf-8")
    except Exception:
        return ""


def throttle_request(request, scope: str, limit: int, window_seconds: int) -> Tuple[bool, int]:
    user_part = f"u:{request.user.id}" if request.user.is_authenticated else "anon"
    ip_part = request.META.get("REMOTE_ADDR", "unknown")
    cache_key = f"ratelimit:{scope}:{user_part}:{ip_part}"

    current = cache.get(cache_key)
    if current is None:
        cache.set(cache_key, 1, timeout=window_seconds)
        return True, limit - 1

    if int(current) >= limit:
        return False, 0

    cache.incr(cache_key)
    remaining = max(0, limit - int(current) - 1)
    return True, remaining
