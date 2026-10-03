import os

from .base import *  # noqa: F401,F403

import dj_database_url


# ============================================================
# PRODUCTION
# ============================================================

DEBUG = False

# Domaines autorisés
ALLOWED_HOSTS = [
    host.strip()
    for host in os.getenv("ALLOWED_HOSTS", "").split(",")
    if host.strip()
]

if not ALLOWED_HOSTS:
    raise RuntimeError("ALLOWED_HOSTS must be configured in production.")


# CSRF
CSRF_TRUSTED_ORIGINS = [
    origin.strip()
    for origin in os.getenv("CSRF_TRUSTED_ORIGINS", "").split(",")
    if origin.strip()
]


# ============================================================
# DATABASE
# ============================================================

database_url = os.getenv("DATABASE_URL", "").strip()

if not database_url:
    raise RuntimeError("DATABASE_URL must be configured in production.")

DATABASES = {
    "default": dj_database_url.parse(
        database_url,
        conn_max_age=600,
        ssl_require=True,
    )
}


# ============================================================
# HTTPS / COOKIES
# ============================================================

SECURE_SSL_REDIRECT = True

SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"

CSRF_COOKIE_HTTPONLY = False
CSRF_COOKIE_SAMESITE = "Lax"


# ============================================================
# SECURITY HEADERS
# ============================================================

SECURE_CONTENT_TYPE_NOSNIFF = True

X_FRAME_OPTIONS = "DENY"

SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"


# HSTS
# À activer seulement lorsque HTTPS fonctionne correctement.
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True


# ============================================================
# PROXY / HTTPS
# ============================================================

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")


# ============================================================
# STATIC FILES
# ============================================================

STATIC_ROOT = BASE_DIR / "static_root"
