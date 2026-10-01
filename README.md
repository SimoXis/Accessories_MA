# ACCESORIES MA (modernisé)

Version modernisée du e-commerce **ACCESORIES MA** (Django 4.2 LTS, Python 3.11, PostgreSQL en production).

Fonctionnement métier identique à l’original : boutique, panier invité, checkout, paiement à la livraison (COD), administration, stock, pages légales, contact.

## Prérequis

- Python 3.11
- PostgreSQL 15+ (production et développement recommandé)
- Optionnel : SQLite uniquement en développement local si `DATABASE_URL` n’est pas défini

## Installation

```powershell
cd ACCESORIES_MA_MODERN
python -m venv venv
venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Copier les variables d’environnement :

```powershell
copy .env.example .env
```

Puis éditer `.env` (ne jamais committer `.env`).

## Variables d’environnement

| Variable | Description |
| --- | --- |
| `SECRET_KEY` | Clé Django (obligatoire) |
| `DEBUG` | `True` en dev, `False` en production |
| `ALLOWED_HOSTS` | Hôtes séparés par des virgules |
| `CSRF_TRUSTED_ORIGINS` | Origines HTTPS séparées par des virgules (production) |
| `DATABASE_URL` | URL PostgreSQL (`postgresql://user:pass@host:5432/dbname`) |
| `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT` | Alternative à `DATABASE_URL` (production uniquement) |
| `DATABASE_SSL_REQUIRE` | `true` / `false` (défaut : `true` en production) |
| `SECURE_SSL_REDIRECT` | Redirection HTTPS en production (défaut : `true`) |

En développement, sans `DATABASE_URL`, SQLite (`db.sqlite3`) est utilisée **uniquement** via `demo.settings.development`.

## Base de données

```powershell
$env:DJANGO_SETTINGS_MODULE = 'demo.settings.development'
python manage.py migrate
python manage.py createsuperuser
```

### Migrer SQLite → PostgreSQL

Si vous avez un fichier `db.sqlite3` avec des données :

```powershell
$env:DATABASE_URL = 'postgresql://USER:PASSWORD@localhost:5432/accesories_ma'
python scripts/migrate_sqlite_to_postgres.py
```

Ou manuellement : `dumpdata` depuis SQLite, `migrate` + `loaddata` sur PostgreSQL (voir le script).

## Fichiers statiques

```powershell
python manage.py collectstatic --noinput
```

WhiteNoise sert les fichiers statiques en production. Les médias (`media_root/`) doivent être sur un stockage persistant ou un volume monté en production.

## Lancement local

```powershell
$env:SECRET_KEY = 'dev-secret-key-change-me'
python manage.py runserver
```

Ouvrir `http://127.0.0.1:8000/`. Administration : `/admin/`.

## Tests et vérifications

```powershell
python manage.py check
python manage.py makemigrations --check
python manage.py test
python manage.py collectstatic --noinput
```

## Production

Module de settings : `demo.settings.production` (utilisé par `demo/wsgi.py`).

```powershell
$env:DJANGO_SETTINGS_MODULE = 'demo.settings.production'
$env:DEBUG = 'False'
$env:SECRET_KEY = '...'
$env:DATABASE_URL = 'postgresql://...'
$env:ALLOWED_HOSTS = 'votredomaine.ma'
$env:CSRF_TRUSTED_ORIGINS = 'https://votredomaine.ma'
python manage.py migrate --noinput
python manage.py collectstatic --noinput
gunicorn demo.wsgi:application --bind 0.0.0.0:8000
```

### Déploiement (Render, Railway, Fly.io, Azure Web App, VPS)

1. **Backend** : déployer ce dépôt avec `Procfile` (`gunicorn demo.wsgi:application`).
2. **Base** : PostgreSQL managé ; définir `DATABASE_URL`.
3. **Secrets** : `SECRET_KEY`, `ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS`.
4. **Médias** : volume persistant ou stockage objet (S3, Azure Blob, etc.) — non inclus par défaut.
5. **Netlify** : non adapté comme hébergeur principal pour cette app Django SSR (sessions, admin, uploads). Utiliser une plateforme WSGI ci-dessus.

## Gestion de la boutique

Identique à l’original : paramètres boutique, collections, produits, galerie, commandes (CSV, statuts, stock), pages légales, messages contact.
