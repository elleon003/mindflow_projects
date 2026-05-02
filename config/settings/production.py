import dj_database_url
from .base import *

DEBUG = env.bool('DEBUG', False)
DJANGO_ENV = env.str('DJANGO_ENV', 'production')
SECRET_KEY = env.str('SECRET_KEY')
ALLOWED_HOSTS = env.list('ALLOWED_HOSTS')
INTERNAL_IPS = env.list('INTERNAL_IPS', ['127.0.0.1', 'localhost'])

DATABASES = {
    'default': dj_database_url.config(
        env='DATABASE_URL',
        conn_max_age=600,
        ssl_require=env.bool('DATABASE_SSL_REQUIRE', False),
    )
}

# Email backend for production (SMTP)
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = env.str('EMAIL_HOST')
EMAIL_PORT = env.int('EMAIL_PORT')
EMAIL_HOST_USER = env.str('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = env.str('EMAIL_HOST_PASSWORD')
EMAIL_USE_TLS = env.bool('EMAIL_USE_TLS', True)
EMAIL_USE_SSL = env.bool('EMAIL_USE_SSL', False)
DEFAULT_FROM_EMAIL = env.str('DEFAULT_FROM_EMAIL')
SERVER_EMAIL = env.str('SERVER_EMAIL')
EMAIL_ADMIN = env.str('EMAIL_ADMIN')    

SECURE_SSL_REDIRECT = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SOCIAL_AUTH_REDIRECT_IS_HTTPS = True
USE_X_FORWARDED_HOST = env.bool('USE_X_FORWARDED_HOST', True)
CSRF_TRUSTED_ORIGINS = env.list('CSRF_TRUSTED_ORIGINS', [])
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = env.bool('CSRF_COOKIE_HTTPONLY', False)
SESSION_COOKIE_SAMESITE = env.str('SESSION_COOKIE_SAMESITE', 'Lax')
CSRF_COOKIE_SAMESITE = env.str('CSRF_COOKIE_SAMESITE', 'Lax')
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = env.str('SECURE_REFERRER_POLICY', 'same-origin')
X_FRAME_OPTIONS = env.str('X_FRAME_OPTIONS', 'DENY')
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Logging configuration for production
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'level': 'INFO',
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
            'level': 'INFO',
            'propagate': False,
        },
        'django.request': {
            'handlers': ['console'],
            'level': 'ERROR',
            'propagate': False,
        },
    },
}