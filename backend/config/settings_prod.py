"""
Settings di PRODUZIONE.
Viene caricato impostando DJANGO_SETTINGS_MODULE=config.settings_prod
"""
from .settings import *   # eredita tutto dallo sviluppo
import os
import dj_database_url

# ─── Sicurezza ────────────────────────────────────────────────────────────
DEBUG = False

SECRET_KEY = os.environ['SECRET_KEY']           # obbligatorio in prod

ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', 'localhost').split(',')

# Protegge da attacchi CSRF anche cross-origin
_csrf_raw = os.environ.get('CSRF_TRUSTED_ORIGINS', '')
CSRF_TRUSTED_ORIGINS = [o.strip() for o in _csrf_raw.split(',') if o.strip()]

# ─── Database ─────────────────────────────────────────────────────────────
DATABASES = {
    'default': dj_database_url.parse(os.environ['DATABASE_URL'])
}

# ─── Static files ─────────────────────────────────────────────────────────
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# ─── ASGI + Django Channels ───────────────────────────────────────────────
INSTALLED_APPS = [
    'daphne',                       # deve essere PRIMO per intercettare ASGI
    *INSTALLED_APPS,
    'channels',
]

ASGI_APPLICATION = 'config.asgi.application'

# InMemoryChannelLayer: nessuna dipendenza esterna, ottimale per single-server.
# Per cluster multi-nodo sostituire con RedisChannelLayer.
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels.layers.InMemoryChannelLayer',
    }
}

# ─── Sicurezza HTTP ───────────────────────────────────────────────────────
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
USE_X_FORWARDED_HOST = True

# Abilita quando si usa HTTPS (decommenta):
# SESSION_COOKIE_SECURE = True
# CSRF_COOKIE_SECURE = True
# SECURE_HSTS_SECONDS = 31536000

# ─── CORS ─────────────────────────────────────────────────────────────────
# In produzione non usiamo CORS_ALLOW_ALL_ORIGINS.
# Il frontend viene servito dallo stesso dominio via Nginx.
CORS_ALLOW_ALL_ORIGINS = False
_cors_raw = os.environ.get('CSRF_TRUSTED_ORIGINS', '')
CORS_ALLOWED_ORIGINS = [o.strip() for o in _cors_raw.split(',') if o.strip()]

# ─── Logging ─────────────────────────────────────────────────────────────
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '[{asctime}] {levelname} {name}: {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': os.environ.get('DJANGO_LOG_LEVEL', 'WARNING'),
            'propagate': False,
        },
    },
}
