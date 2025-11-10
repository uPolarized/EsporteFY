from pathlib import Path
import environ
import os

BASE_DIR = Path(__file__).resolve().parent.parent
env = environ.Env()
environ.Env.read_env(os.path.join(BASE_DIR, '.env'))


OPENWEATHER_API_KEY = env('OPENWEATHER_API_KEY', default=None)
NEWS_API_KEY = env('NEWS_API_KEY', default=None)
SECRET_KEY = env('SECRET_KEY')
DEBUG = env.bool('DEBUG', default=False)

RECAPTCHA_REQUIRED_SCORE = 0.5


# --- Configurações para Ngrok (Ambiente Local) ---
ALLOWED_HOSTS = [
    "localhost",
    "127.0.0.1",
    "a9b6a9e85d43.ngrok-free.app",
]

CSRF_TRUSTED_ORIGINS = [
    "http://localhost:8000",
    "https://a9b6a9e85d43.ngrok-free.app",
]
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')


INSTALLED_APPS = [
    'daphne',   # Adicionado para o Channels
    'channels',
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
    'social',
    'conteudo',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',
    'allauth.socialaccount.providers.github',  # <- Adicione isto
    'crispy_forms',
    'crispy_bootstrap5',
]
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'allauth.account.middleware.AccountMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
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
ASGI_APPLICATION = 'esportefy.asgi.application'

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


# --- Arquivos estáticos ---
STATIC_URL = '/static/'

# Local onde o Django vai reunir todos os estáticos (admin, apps, etc.)
STATIC_ROOT = BASE_DIR / "staticfiles"

# Pasta de arquivos estáticos do projeto (customizados)
STATICFILES_DIRS = [
    BASE_DIR / "static",
]





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

# Configurações do Allauth
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_USERNAME_REQUIRED = True # O username será pedido no nosso formulário, não exigido pelo allauth
ACCOUNT_LOGIN_METHODS = ['username', 'email']
ACCOUNT_EMAIL_VERIFICATION = 'optional'
SOCIALACCOUNT_AUTO_SIGNUP = True
SOCIALACCOUNT_EMAIL_VERIFICATION = 'optional'
# ESTA É A MUDANÇA: em vez de herdar, apontamos para um formulário simples.
ACCOUNT_SIGNUP_FORM_CLASS = 'perfis.signup_form.CustomSignupForm'

# --- Configuração do Google reCAPTCHA ---
RECAPTCHA_PUBLIC_KEY = env('RECAPTCHA_PUBLIC_KEY', default='')
RECAPTCHA_PRIVATE_KEY = env('RECAPTCHA_PRIVATE_KEY', default='')

RECAPTCHA_USE_SSL = True




SOCIALACCOUNT_PROVIDERS = {
    "google": {
        "SCOPE": [
            "profile",
            "email",
        ],
        "AUTH_PARAMS": {
            "access_type": "online",
        },
    }
}

# --- Configuração do Django Channels (para o Chat) ---
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [("redis", 6379)], 
        },
    },
}




# --------------------------------------------------------------------------
# --- CONFIGURAÇÃO DE ENVIO DE E-MAIL (SMTP) ---
# --------------------------------------------------------------------------

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True  # Para comunicação segura
EMAIL_HOST_USER = env('EMAIL_HOST_USER')  # Lê o e-mail do arquivo .env
EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD') # Lê a senha de app do arquivo .env
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER # O e-mail que aparecerá como remetente

# Faz o usuário logar automaticamente ao clicar no link de verificação
ACCOUNT_CONFIRM_EMAIL_ON_GET = True

#----------------------------------------------------------------------------


# --- Configuração de Arquivos de Mídia (Uploads dos Usuários)
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'


REST_FRAMEWORK = {
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,  # 20 quadras por página (ajustável)
}
