from pathlib import Path
import environ
import os

BASE_DIR = Path(__file__).resolve().parent.parent
env = environ.Env()
environ.Env.read_env(os.path.join(BASE_DIR, '.env'))

OPENWEATHER_API_KEY = env('OPENWEATHER_API_KEY', default=None)
NEWS_API_KEY = env('NEWS_API_KEY', default=None)
GIPHY_API_KEY = env('GIPHY_API_KEY', default='dc6zaTOxFJmzC')
SECRET_KEY = env('SECRET_KEY')
DEBUG = env.bool('DEBUG', default=False)

RECAPTCHA_REQUIRED_SCORE = 0.5

# --- Configuração Híbrida ---
# URL usada pelas Views do Django para publicar mensagens no Redis
REDIS_URL = env('REDIS_URL', default='redis://redis:6379/0')
SOCIAL_CONTENT_ENCRYPTION_KEY = env('SOCIAL_CONTENT_ENCRYPTION_KEY', default='')
SOCIAL_ALLOWED_GIF_HOSTS = tuple(env.list('SOCIAL_ALLOWED_GIF_HOSTS', default=[
    'giphy.com',
    'giphyusercontent.com',
    'media.tenor.com',
    'tenor.com',
]))

ALLOWED_HOSTS = [
    "localhost",
    "127.0.0.1",
    ".ngrok-free.app",
    "2e04-2804-3d28-43-1eeb-9540-3aad-ad40-e8b.ngrok-free.app"
]



CSRF_TRUSTED_ORIGINS = [
    "http://localhost:8000",
    "https://d9fcadc8ea7a.ngrok-free.app",
    "https://ee8218ea778b.ngrok-free.app",
]


SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

INSTALLED_APPS = [
    # 'daphne',   <-- REMOVIDO (Causa conflito na arquitetura hibrida)
    # 'channels', <-- REMOVIDO
    'django_recaptcha',
    'rest_framework',
    'django_filters',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
    'app',
    'quadras',
    'partidas',
    'perfis',
    'social.apps.SocialConfig',
    'conteudo',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',
    'allauth.socialaccount.providers.github',
    'crispy_forms',
    'crispy_bootstrap5',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'esportefy.security_headers.SecurityHeadersMiddleware',
    'django.middleware.gzip.GZipMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'allauth.account.middleware.AccountMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'perfis.middleware.TrackSessionSecurityMetadataMiddleware',
    'perfis.middleware.RequireLgpdConsentMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'esportefy.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'app' / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.template.context_processors.debug',
                'esportefy.context_processors.recaptcha_keys', 
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'esportefy.wsgi.application'
# ASGI_APPLICATION = 'esportefy.asgi.application' <-- COMENTADO/REMOVIDO

DATABASES = {'default': env.db('DATABASE_URL')}

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'pt-br'
USE_TZ = True
TIME_ZONE = 'America/Sao_Paulo'
USE_I18N = True

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
SITE_ID = 1
CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]

LOGIN_REDIRECT_URL = '/feed/'
LOGOUT_REDIRECT_URL = '/'

ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_USERNAME_REQUIRED = True
ACCOUNT_LOGIN_METHODS = ['username', 'email']
ACCOUNT_EMAIL_VERIFICATION = 'optional'
SOCIALACCOUNT_AUTO_SIGNUP = False
SOCIALACCOUNT_EMAIL_VERIFICATION = 'none'
ACCOUNT_SIGNUP_FORM_CLASS = 'perfis.signup_form.CustomSignupForm'
ACCOUNT_ADAPTER = 'perfis.adapters.AsyncAccountAdapter'

ACCOUNT_FORMS = {
    "set_password": "perfis.forms.CustomPasswordSetForm",
    "change_password": "perfis.forms.ChangePasswordCaptchaForm",
    "reset_password": "perfis.forms.CustomResetPasswordForm",
}

RECAPTCHA_PUBLIC_KEY = env('RECAPTCHA_PUBLIC_KEY', default='')
RECAPTCHA_PRIVATE_KEY = env('RECAPTCHA_PRIVATE_KEY', default='')
RECAPTCHA_USE_SSL = True

SOCIALACCOUNT_PROVIDERS = {
    "google": {
        "SCOPE": ["profile", "email"],
        "AUTH_PARAMS": {"access_type": "online"},
    },
    "github": {
        "APP": {
            "client_id": env("GITHUB_CLIENT_ID", default=""),
            "secret": env("GITHUB_CLIENT_SECRET", default=""),
            "key": ""
        }
    }
}

# CHANNEL_LAYERS REMOVIDO - Não usamos mais o Channels, usamos FastAPI+Redis direto.

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True 
EMAIL_HOST_USER = env('EMAIL_HOST_USER') 
EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD') 
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER 
EMAIL_TIMEOUT = 10
ACCOUNT_CONFIRM_EMAIL_ON_GET = True

# Segurança padrão para produção (ajuste por variável de ambiente).
SECURE_SSL_REDIRECT = env.bool('SECURE_SSL_REDIRECT', default=not DEBUG)
SESSION_COOKIE_SECURE = env.bool('SESSION_COOKIE_SECURE', default=not DEBUG)
CSRF_COOKIE_SECURE = env.bool('CSRF_COOKIE_SECURE', default=not DEBUG)
SECURE_HSTS_SECONDS = env.int('SECURE_HSTS_SECONDS', default=31536000 if not DEBUG else 0)
SECURE_HSTS_INCLUDE_SUBDOMAINS = env.bool('SECURE_HSTS_INCLUDE_SUBDOMAINS', default=not DEBUG)
SECURE_HSTS_PRELOAD = env.bool('SECURE_HSTS_PRELOAD', default=not DEBUG)
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
REFERRER_POLICY = 'strict-origin-when-cross-origin'
SESSION_COOKIE_HTTPONLY = True

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

REST_FRAMEWORK = {
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
}

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'esportefy-local-cache',
        'TIMEOUT': 300,
        'OPTIONS': {
            'MAX_ENTRIES': 1000,
        },
    }
}

# Limites de upload para mídia social (posts/comentários)
SOCIAL_IMAGE_MAX_UPLOAD_BYTES = env.int('SOCIAL_IMAGE_MAX_UPLOAD_BYTES', default=5 * 1024 * 1024)
SOCIAL_ALLOWED_IMAGE_MIME_TYPES = tuple(env.list('SOCIAL_ALLOWED_IMAGE_MIME_TYPES', default=[
    'image/jpeg',
    'image/png',
    'image/webp',
    'image/gif',
]))

# CSP em modo report-only para observabilidade sem bloquear produção.
CSP_REPORT_ONLY_ENABLED = env.bool('CSP_REPORT_ONLY_ENABLED', default=True)
CSP_REPORT_ONLY_POLICY = env(
    'CSP_REPORT_ONLY_POLICY',
    default=(
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://www.google.com https://www.gstatic.com; "
        "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://fonts.googleapis.com; "
        "img-src 'self' data: blob: https:; "
        "font-src 'self' data: https://fonts.gstatic.com https://cdn.jsdelivr.net; "
        "connect-src 'self' https: ws: wss:; "
        "media-src 'self' data: https:; "
        "frame-src 'self' https://www.google.com https://www.gstatic.com; "
        "object-src 'none'; "
        "base-uri 'self'; "
        "form-action 'self'; "
        "frame-ancestors 'none'; "
        "report-uri /security/csp-report/;"
    )
)