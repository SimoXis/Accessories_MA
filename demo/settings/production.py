import os

import dj_database_url

from .base import *  # noqa: F401,F403

DEBUG = False

database_url = os.getenv('DATABASE_URL', '').strip()
if not database_url:
    db_name = os.getenv('DB_NAME')
    db_user = os.getenv('DB_USER')
    db_password = os.getenv('DB_PASSWORD')
    db_host = os.getenv('DB_HOST', 'localhost')
    db_port = os.getenv('DB_PORT', '5432')
    if db_name and db_user and db_password:
        database_url = (
            f'postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}'
        )

if not database_url:
    raise RuntimeError(
        'Production requires DATABASE_URL or DB_NAME, DB_USER, and DB_PASSWORD.'
    )

DATABASES = {
    'default': dj_database_url.parse(
        database_url,
        conn_max_age=600,
        ssl_require=os.getenv('DATABASE_SSL_REQUIRE', 'true').lower()
        in ('1', 'true', 'yes'),
    )
}

if DATABASES['default']['ENGINE'] not in (
    'django.db.backends.postgresql',
    'django.db.backends.postgresql_psycopg2',
):
    raise RuntimeError('Production database must be PostgreSQL.')

SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_SECONDS = 31536000
SECURE_SSL_REDIRECT = os.getenv('SECURE_SSL_REDIRECT', 'true').lower() in (
    '1',
    'true',
    'yes',
)
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
X_FRAME_OPTIONS = 'DENY'
