import os

from .base import *  # noqa: F401,F403

DEBUG = os.getenv('DEBUG', 'true').lower() in ('1', 'true', 'yes')

database_url = os.getenv('DATABASE_URL', '').strip()
if database_url:
    import dj_database_url

    DATABASES = {
        'default': dj_database_url.parse(
            database_url,
            conn_max_age=600,
            ssl_require=os.getenv('DATABASE_SSL_REQUIRE', 'false').lower()
            in ('1', 'true', 'yes'),
        )
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

if DEBUG:
    CSRF_TRUSTED_ORIGINS = CSRF_TRUSTED_ORIGINS or [
        'http://localhost:8000',
        'http://127.0.0.1:8000',
    ]
