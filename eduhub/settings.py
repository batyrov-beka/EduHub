import os
from pathlib import Path
from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parent.parent / '.env', override=True)


BASE_DIR = Path(__file__).resolve().parent.parent


SECRET_KEY = os.getenv('SECRET_KEY') or 'dev-only-insecure-key-change-me'
DEBUG = os.getenv('DEBUG') == 'True'


hosts = os.getenv('ALLOWED_HOSTS')
ALLOWED_HOSTS = hosts.split(',') if hosts else ['127.0.0.1', 'localhost']


INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'users',
    'jobs',
    'materials',
    'forms',
    'Dashboard',
    'forum',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'Dashboard.middleware.VerificationMiddleware',
]

ROOT_URLCONF = 'eduhub.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'Dashboard.context_processors.notifications',
                'Dashboard.context_processors.telegram_channel',
            ],
        },
    },
]

WSGI_APPLICATION = 'eduhub.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]


LANGUAGE_CODE = 'ru'
LANGUAGES = [
    ('ru', 'Русский'),
    ('ky', 'Кыргызча'),
]
TIME_ZONE = 'Asia/Bishkek'
USE_I18N = True
USE_TZ = True

LOCALE_PATHS = [
    os.path.join(BASE_DIR, 'locale/'),
]

AUTH_USER_MODEL = 'users.CustomUser'

STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

LOGIN_URL = 'login'
LOGOUT_REDIRECT_URL = 'home'
LOGOUT_ON_GET = True

EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = (os.getenv('EMAIL_USER') or '').strip()
EMAIL_HOST_PASSWORD = (os.getenv('EMAIL_PASS') or '').replace(' ', '')
DEFAULT_FROM_EMAIL = f'EduHub <{EMAIL_HOST_USER}>' if EMAIL_HOST_USER else 'EduHub <noreply@eduhub.kg>'

if EMAIL_HOST_USER and EMAIL_HOST_PASSWORD:
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
else:
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

SITE_URL = os.getenv('SITE_URL', 'https://baiysh.pythonanywhere.com')
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
TELEGRAM_CHANNEL_URL = os.getenv('TELEGRAM_CHANNEL_URL', 'https://t.me/eduhub_kg_jobs').strip()

OTP_LIFETIME_MINUTES = 10
OTP_MAX_ATTEMPTS = 5
OTP_RESEND_SECONDS = 60

USE_HTTPS = os.getenv('USE_HTTPS', 'False' if DEBUG else 'True') == 'True'
if USE_HTTPS:
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'