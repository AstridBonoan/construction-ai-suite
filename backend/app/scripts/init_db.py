"""
Initialize the database tables using Flask-SQLAlchemy `create_all()` for development.

Usage:
  set DATABASE_URL=postgresql://user:pass@host:5432/db
  python backend/app/scripts/init_db.py

NOTE: Prefer running SQL migrations in production. This is intended for local/dev convenience.
"""
import os
from backend.app.main import app


def run():
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print('DATABASE_URL not set. Aborting.')
        return 1

    if not hasattr(app, 'db') or app.db is None:
        print('Flask-SQLAlchemy not initialized. Ensure DATABASE_URL and models are available.')
        return 2

    with app.app_context():
        print('Creating tables (this uses SQLAlchemy create_all()).')
        app.db.create_all()
        print('Tables created (if not existing).')
    return 0


if __name__ == '__main__':
    raise SystemExit(run())
