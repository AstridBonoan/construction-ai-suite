"""
Run SQL migrations against the configured DATABASE_URL.

Usage:
    set DATABASE_URL=postgresql://user:pass@host:5432/dbname
    python backend/app/scripts/run_migrations.py

This script executes all .sql files in `backend/app/migrations/` in lexicographic order.
"""
import os
from sqlalchemy import create_engine, text

MIGRATIONS_DIR = os.path.join(os.path.dirname(__file__), '..', 'migrations')


def run():
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print('DATABASE_URL not set. Aborting.')
        return 1

    engine = create_engine(database_url)

    files = sorted([f for f in os.listdir(MIGRATIONS_DIR) if f.endswith('.sql')])
    if not files:
        print('No migration files found in', MIGRATIONS_DIR)
        return 0

    with engine.connect() as conn:
        for fname in files:
            path = os.path.join(MIGRATIONS_DIR, fname)
            print('Applying', fname)
            with open(path, 'r', encoding='utf-8') as fh:
                sql = fh.read()
            try:
                conn.execute(text(sql))
                conn.commit()
            except Exception as e:
                print('Failed to apply', fname, e)
                return 2

    print('Migrations applied successfully')
    return 0


if __name__ == '__main__':
    raise SystemExit(run())
