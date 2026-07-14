from __future__ import annotations

import sqlite3
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[2]
DATABASE_PATH = BASE_DIR / "govguideai.sqlite3"


def get_connection() -> sqlite3.Connection:
    """Open a SQLite connection with dictionary-like rows."""

    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def init_db() -> None:
    """Create the local database tables if they do not already exist."""

    with get_connection() as db:
        db.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                created_date TEXT NOT NULL,
                last_login_date TEXT
            );

            CREATE TABLE IF NOT EXISTS profiles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL UNIQUE,
                full_name TEXT NOT NULL,
                age TEXT NOT NULL,
                state TEXT NOT NULL,
                district TEXT NOT NULL,
                occupation TEXT NOT NULL,
                occupation_custom TEXT,
                location_type TEXT NOT NULL,
                preferred_language TEXT NOT NULL,
                gender TEXT,
                student_status TEXT,
                farmer_status TEXT,
                annual_household_income_range TEXT,
                disability_status TEXT,
                employment_status TEXT,
                marital_status TEXT,
                social_category TEXT,
                updated_date TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            );
            """
        )
        _ensure_column(db, "profiles", "occupation_custom", "TEXT")
        _migrate_legacy_occupation_values(db)


def _ensure_column(
    db: sqlite3.Connection,
    table_name: str,
    column_name: str,
    column_type: str,
) -> None:
    columns = db.execute(f"PRAGMA table_info({table_name})").fetchall()
    if any(column["name"] == column_name for column in columns):
        return

    db.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}")


def _migrate_legacy_occupation_values(db: sqlite3.Connection) -> None:
    """Map old profile statuses to occupation only when occupation is empty."""

    db.execute("UPDATE profiles SET occupation = 'student' WHERE LOWER(TRIM(occupation)) = 'student'")
    db.execute("UPDATE profiles SET occupation = 'farmer' WHERE LOWER(TRIM(occupation)) = 'farmer'")
    db.execute("UPDATE profiles SET occupation = 'employed' WHERE LOWER(TRIM(occupation)) IN ('employed', 'employee', 'job')")
    db.execute("UPDATE profiles SET occupation = 'unemployed' WHERE LOWER(TRIM(occupation)) LIKE '%unemploy%'")

    db.execute(
        """
        UPDATE profiles
        SET occupation = 'student'
        WHERE TRIM(COALESCE(occupation, '')) = ''
          AND LOWER(COALESCE(student_status, '')) LIKE '%student%'
          AND LOWER(COALESCE(student_status, '')) NOT LIKE '%not%'
        """
    )
    db.execute(
        """
        UPDATE profiles
        SET occupation = 'farmer'
        WHERE TRIM(COALESCE(occupation, '')) = ''
          AND LOWER(COALESCE(farmer_status, '')) LIKE '%farmer%'
          AND LOWER(COALESCE(farmer_status, '')) NOT LIKE '%not%'
        """
    )
    db.execute(
        """
        UPDATE profiles
        SET occupation = 'unemployed'
        WHERE TRIM(COALESCE(occupation, '')) = ''
          AND LOWER(COALESCE(employment_status, '')) LIKE '%unemploy%'
        """
    )
