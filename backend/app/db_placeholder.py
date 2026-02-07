"""Database wiring placeholders for Phase 3 scaffolding.

This module provides non-destructive placeholders for database connections,
migrations, and models. It is intentionally minimal and safe to import in
DEMO_MODE. Replace these stubs with real implementations (SQLAlchemy,
Alembic, etc.) during Phase 3 integration.
"""
from __future__ import annotations
import os
from typing import Any, Optional


class DatabaseConnection:
    """Placeholder DB connection object.

    Usage:
      db = DatabaseConnection(url)
      db.connect()
      # use db.session or similar in real implementation
    """

    def __init__(self, url: Optional[str] = None):
        self.url = url or os.environ.get('DATABASE_URL')
        self.connected = False

    def connect(self) -> bool:
        """Establish a connection. In demo mode this is a no-op that returns False.

        Replace with real DB connection logic.
        """
        if not self.url:
            # No DB configured; do not raise in demo mode
            self.connected = False
            return False
        # Placeholder: in real code create engine/session here
        self.connected = True
        return True

    def close(self) -> None:
        self.connected = False

    def migrate(self) -> None:
        """Run migrations. No-op in placeholder.

        Replace with Alembic or other migration invocation.
        """
        print("[DB][MIGRATE] migrations skipped (placeholder)")


# Exported helper
def get_db_connection(url: Optional[str] = None) -> DatabaseConnection:
    return DatabaseConnection(url=url)


__all__ = ['DatabaseConnection', 'get_db_connection']
