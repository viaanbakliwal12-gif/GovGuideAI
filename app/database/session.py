from __future__ import annotations

import sqlite3
import os
from pathlib import Path

from app.database.migrations import apply_migrations


BASE_DIR = Path(__file__).resolve().parents[2]
DATABASE_PATH = Path(os.getenv("DATABASE_PATH", str(BASE_DIR / "govguideai.sqlite3")))


def get_connection() -> sqlite3.Connection:
    """Open a SQLite connection with dictionary-like rows."""

    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def init_db() -> None:
    """Apply safe, in-place schema migrations without deleting existing records."""

    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    try:
        # The user-table compatibility migration must replace a referenced parent
        # table. SQLite requires foreign-key enforcement to be disabled for that
        # short, transactional operation.
        connection.execute("PRAGMA foreign_keys = OFF")
        apply_migrations(connection)
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()
