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
