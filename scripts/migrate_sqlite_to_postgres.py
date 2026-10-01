#!/usr/bin/env python
"""
Migrate data from a local SQLite db.sqlite3 to PostgreSQL.

Prerequisites:
  1. PostgreSQL database created and empty (or you accept duplicate key errors).
  2. DATABASE_URL pointing to PostgreSQL.
  3. SQLite file at the project root (db.sqlite3).

Usage (from project root):
  set DJANGO_SETTINGS_MODULE=demo.settings.development
  set DATABASE_URL=postgresql://user:pass@localhost:5432/accesories_ma
  python scripts/migrate_sqlite_to_postgres.py

This script:
  - exports data from SQLite via dumpdata
  - runs migrate on PostgreSQL
  - loads the fixture into PostgreSQL
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SQLITE_PATH = PROJECT_ROOT / 'db.sqlite3'
FIXTURE_PATH = PROJECT_ROOT / 'scripts' / '_sqlite_export.json'


def run(cmd: list[str], env: dict[str, str]) -> None:
    print('+', ' '.join(cmd))
    subprocess.check_call(cmd, cwd=PROJECT_ROOT, env=env)


def main() -> int:
    if not SQLITE_PATH.is_file():
        print(
            'No db.sqlite3 found at project root. '
            'Nothing to migrate (typical for a fresh clone).',
            file=sys.stderr,
        )
        return 0

    database_url = os.getenv('DATABASE_URL', '').strip()
    if not database_url or not database_url.startswith('postgresql'):
        print('Set DATABASE_URL to a PostgreSQL connection string.', file=sys.stderr)
        return 1

    env = os.environ.copy()
    env.setdefault('DJANGO_SETTINGS_MODULE', 'demo.settings.development')
    env.setdefault('SECRET_KEY', 'migration-temporary-secret-key')

    sqlite_env = env.copy()
    sqlite_env['DATABASE_URL'] = ''

    run(
        [sys.executable, 'manage.py', 'dumpdata',
         '--natural-foreign', '--natural-primary',
         '--indent', '2', '-o', str(FIXTURE_PATH)],
        sqlite_env,
    )

    run([sys.executable, 'manage.py', 'migrate', '--noinput'], env)

    run(
        [sys.executable, 'manage.py', 'loaddata', str(FIXTURE_PATH)],
        env,
    )

    print('Migration complete. Verify data in PostgreSQL and back up the fixture:')
    print(FIXTURE_PATH)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
