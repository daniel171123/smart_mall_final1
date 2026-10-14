import environ
import os
from pathlib import Path

# ─── Base Directory ────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent

# ─── Environment Variables ─────────────────────────────────────────
env = environ.Env()
environ.Env.read_env(BASE_DIR / '.env')

# ─── Security ──────────────────────────────────────────────────────
SECRET_KEY = env('SECRET_KEY')
DEBUG = env.bool('DEBUG', default=False)
ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=['localhost'])

# ─── Installed Apps ────────────────────────────────────────────────
DJANGO_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

THIRD_PARTY_APPS = [
    'crispy_forms',
    'crispy_bootstrap5',
    'django_celery_beat',
]

LOCAL_APPS = [
    'accounts',
    'malls',
    'tenants',
    'leases',
    'invoices',
    'payments',
    'notifications',
    'complaints',
    'maintenance',
    'dashboard',
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

# ─── Middleware ────────────────────────────────────────────────────
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'core.urls'

# ─── Templates ─────────────────────────────────────────────────────
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        # WHY: One global templates folder — easier to manage
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'notifications.context_processors.recent_notifications',
            ],
        },
    },
]

WSGI_APPLICATION = 'core.wsgi.application'

# ─── Database (MySQL) ──────────────────────────────────────────────
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': env('DB_NAME'),
        'USER': env('DB_USER'),
        'PASSWORD': env('DB_PASSWORD'),
        'HOST': env('DB_HOST', default='localhost'),
        'PORT': env('DB_PORT', default='3306'),
        'OPTIONS': {
            'charset': 'utf8mb4',
            # WHY: Enforces strict mode — catches data errors early
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
        },
    }
}

# ─── Custom User Model ─────────────────────────────────────────────
# WHY: Must be set BEFORE first migration — cannot change after
AUTH_USER_MODEL = 'accounts.CustomUser'

# ─── Authentication ────────────────────────────────────────────────
LOGIN_URL = '/accounts/login/'
LOGIN_REDIRECT_URL = '/dashboard/'
LOGOUT_REDIRECT_URL = '/accounts/login/'

# ─── Password Validation ───────────────────────────────────────────
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# ─── Internationalization ──────────────────────────────────────────
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Africa/Addis_Ababa'  # Ethiopian timezone
USE_I18N = True
USE_TZ = False

# ─── Static Files ──────────────────────────────────────────────────
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

# ─── Media Files (Uploads) ─────────────────────────────────────────
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# ─── Email Configuration ───────────────────────────────────────────
# WHY: Console backend for regular notifications in DEBUG
# but password reset ALWAYS uses real SMTP so the link
# actually reaches the user's inbox.
EMAIL_HOST          = env('EMAIL_HOST',
                          default='smtp.gmail.com')
EMAIL_PORT          = env.int('EMAIL_PORT', default=587)
EMAIL_USE_TLS       = env.bool('EMAIL_USE_TLS', default=True)
EMAIL_HOST_USER     = env('EMAIL_HOST_USER',     default='')
EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL  = (
    f'Smart Mall System '
    f'<{env("EMAIL_HOST_USER", default="noreply@smartmall.com")}>'
)

if DEBUG:
    # Notification emails print to terminal
    EMAIL_BACKEND = (
        'django.core.mail.backends.console.EmailBackend'
    )
else:
    EMAIL_BACKEND = env('EMAIL_BACKEND')

# Password reset always uses real SMTP regardless of DEBUG
# WHY: The reset link must reach the user's actual inbox
PASSWORD_RESET_EMAIL_BACKEND = (
    'django.core.mail.backends.smtp.EmailBackend'
)

# ─── Crispy Forms ──────────────────────────────────────────────────
CRISPY_ALLOWED_TEMPLATE_PACKS = 'bootstrap5'
CRISPY_TEMPLATE_PACK = 'bootstrap5'

# ─── Celery Configuration ──────────────────────────────────────────
CELERY_BROKER_URL = env('CELERY_BROKER_URL')
CELERY_RESULT_BACKEND = env('CELERY_RESULT_BACKEND')
CELERY_TIMEZONE = 'Africa/Addis_Ababa'
CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers:DatabaseScheduler'

# ─── Business Logic Constants ──────────────────────────────────────
# WHY: Centralized here so we never hardcode these values anywhere else
PENALTY_RATE_PER_DAY = env.float('DEFAULT_PENALTY_RATE', default=0.01)
PAYMENT_DUE_DAYS = env.int('DEFAULT_PAYMENT_DUE_DAYS', default=10)
LEASE_EXPIRY_WARNING_DAYS = env.int(
    'DEFAULT_LEASE_EXPIRY_WARNING_DAYS',
    default=30
)
PRE_DEADLINE_REMINDER_DAYS = 3
POST_DEADLINE_REMINDER_INTERVAL_DAYS = 3

# ─── Default Primary Key ───────────────────────────────────────────
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ── Rate Limiting ──────────────────────────────────────────────────
# WHY: Prevents brute force attacks on the login page.
# After 5 failed attempts from same IP, lock for 15 minutes.
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    }
}

# ─── Logging ───────────────────────────────────────────────────────
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': (
                '[{asctime}] {levelname} {name}: {message}'
            ),
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class':     'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level':    'INFO',
    },
    'loggers': {
        'django': {
            'handlers':  ['console'],
            'level':     'INFO',
            'propagate': False,
        },
        'celery': {
            'handlers':  ['console'],
            'level':     'INFO',
            'propagate': False,
        },
    },
}