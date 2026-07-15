from __future__ import annotations

from datetime import datetime, timezone
import sqlite3


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def apply_migrations(db: sqlite3.Connection) -> None:
    """Upgrade the existing SQLite database in place and preserve all row IDs."""

    db.executescript(
        """
        CREATE TABLE IF NOT EXISTS schema_migrations (
            version INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            applied_at TEXT NOT NULL
        );
        """
    )

    _create_or_upgrade_users(db)
    _ensure_column(db, "users", "is_admin", "INTEGER NOT NULL DEFAULT 0")
    _ensure_column(db, "users", "deleted_at", "TEXT")
    _create_profiles(db)
    _ensure_column(db, "profiles", "occupation_custom", "TEXT")
    _migrate_legacy_occupation_values(db)
    _create_auth_tables(db)
    _ensure_column(
        db,
        "otp_challenges",
        "delivery_method",
        "TEXT NOT NULL DEFAULT 'local'",
    )
    _ensure_column(db, "otp_challenges", "provider_reference", "TEXT")
    _create_admin_tables(db)
    _record_migration(db, 1, "otp_and_guest_auth")
    _record_migration(db, 2, "admin_profiles_and_provider_tracking")


def _create_or_upgrade_users(db: sqlite3.Connection) -> None:
    existing = db.execute(
        "SELECT sql FROM sqlite_master WHERE type = 'table' AND name = 'users'"
    ).fetchone()
    if existing is None:
        _create_users_table(db, "users")
        return

    columns = {row["name"]: row for row in db.execute("PRAGMA table_info(users)")}
    required_columns = {
        "verified_email",
        "verified_phone",
        "email_verified_at",
        "phone_verified_at",
        "created_at",
        "last_login_at",
    }
    legacy_constraints_remain = bool(columns["email"]["notnull"]) or bool(
        columns["password_hash"]["notnull"]
    )
    if required_columns.issubset(columns) and not legacy_constraints_remain:
        return

    db.execute("DROP TABLE IF EXISTS users_migrated")
    _create_users_table(db, "users_migrated")
    column_names = set(columns)
    verified_email = "verified_email" if "verified_email" in column_names else "NULL"
    verified_phone = "verified_phone" if "verified_phone" in column_names else "NULL"
    email_verified_at = (
        "email_verified_at" if "email_verified_at" in column_names else "NULL"
    )
    phone_verified_at = (
        "phone_verified_at" if "phone_verified_at" in column_names else "NULL"
    )
    created_at = "COALESCE(created_at, created_date)" if "created_at" in column_names else "created_date"
    last_login_at = (
        "COALESCE(last_login_at, last_login_date)"
        if "last_login_at" in column_names
        else "last_login_date"
    )
    is_admin = "COALESCE(is_admin, 0)" if "is_admin" in column_names else "0"
    deleted_at = "deleted_at" if "deleted_at" in column_names else "NULL"
    db.execute(
        f"""
        INSERT INTO users_migrated (
            id, email, password_hash, created_date, last_login_date,
            verified_email, verified_phone, email_verified_at,
            phone_verified_at, created_at, last_login_at, is_admin, deleted_at
        )
        SELECT
            id, email, password_hash, created_date, last_login_date,
            {verified_email}, {verified_phone}, {email_verified_at},
            {phone_verified_at}, {created_at}, {last_login_at}, {is_admin}, {deleted_at}
        FROM users
        """
    )
    db.execute("DROP TABLE users")
    db.execute("ALTER TABLE users_migrated RENAME TO users")


def _create_users_table(db: sqlite3.Connection, table_name: str) -> None:
    db.execute(
        f"""
        CREATE TABLE {table_name} (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE,
            password_hash TEXT,
            created_date TEXT NOT NULL,
            last_login_date TEXT,
            verified_email TEXT UNIQUE,
            verified_phone TEXT UNIQUE,
            email_verified_at TEXT,
            phone_verified_at TEXT,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            last_login_at TEXT,
            is_admin INTEGER NOT NULL DEFAULT 0 CHECK (is_admin IN (0, 1)),
            deleted_at TEXT,
            CHECK (email IS NOT NULL OR verified_email IS NOT NULL OR verified_phone IS NOT NULL)
        )
        """
    )


def _create_profiles(db: sqlite3.Connection) -> None:
    db.executescript(
        """
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


def _create_auth_tables(db: sqlite3.Connection) -> None:
    db.executescript(
        """
        CREATE TABLE IF NOT EXISTS otp_challenges (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            public_id TEXT NOT NULL UNIQUE,
            destination_hash TEXT NOT NULL,
            destination_encrypted TEXT NOT NULL,
            channel TEXT NOT NULL CHECK (channel IN ('email', 'sms')),
            purpose TEXT NOT NULL,
            otp_hash TEXT NOT NULL,
            expires_at TEXT NOT NULL,
            attempts INTEGER NOT NULL DEFAULT 0,
            resend_count INTEGER NOT NULL DEFAULT 0,
            used_at TEXT,
            created_at TEXT NOT NULL,
            last_sent_at TEXT NOT NULL,
            requested_ip_hash TEXT NOT NULL,
            delivery_method TEXT NOT NULL DEFAULT 'local',
            provider_reference TEXT
        );

        CREATE INDEX IF NOT EXISTS idx_otp_destination_created
            ON otp_challenges(destination_hash, created_at);
        CREATE INDEX IF NOT EXISTS idx_otp_ip_created
            ON otp_challenges(requested_ip_hash, created_at);
        CREATE INDEX IF NOT EXISTS idx_otp_expiry
            ON otp_challenges(expires_at);

        CREATE TABLE IF NOT EXISTS guest_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_hash TEXT NOT NULL UNIQUE,
            created_at TEXT NOT NULL,
            last_seen_at TEXT NOT NULL,
            expires_at TEXT NOT NULL
        );

        CREATE INDEX IF NOT EXISTS idx_guest_expiry
            ON guest_sessions(expires_at);
        """
    )


def _create_admin_tables(db: sqlite3.Connection) -> None:
    db.executescript(
        """
        CREATE TABLE IF NOT EXISTS export_audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            admin_user_id INTEGER NOT NULL,
            exported_at TEXT NOT NULL,
            file_format TEXT NOT NULL CHECK (file_format IN ('csv', 'json')),
            record_count INTEGER NOT NULL CHECK (record_count >= 0)
        );

        CREATE INDEX IF NOT EXISTS idx_export_audit_admin_time
            ON export_audit_log(admin_user_id, exported_at);
        """
    )


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
    columns = {row["name"] for row in db.execute("PRAGMA table_info(profiles)")}
    if "occupation" not in columns:
        return

    db.execute("UPDATE profiles SET occupation = 'student' WHERE LOWER(TRIM(occupation)) = 'student'")
    db.execute("UPDATE profiles SET occupation = 'farmer' WHERE LOWER(TRIM(occupation)) = 'farmer'")
    db.execute("UPDATE profiles SET occupation = 'employed' WHERE LOWER(TRIM(occupation)) IN ('employed', 'employee', 'job')")
    db.execute("UPDATE profiles SET occupation = 'unemployed' WHERE LOWER(TRIM(occupation)) LIKE '%unemploy%'")

    if "student_status" in columns:
        db.execute(
            """
            UPDATE profiles SET occupation = 'student'
            WHERE TRIM(COALESCE(occupation, '')) = ''
              AND LOWER(COALESCE(student_status, '')) LIKE '%student%'
              AND LOWER(COALESCE(student_status, '')) NOT LIKE '%not%'
            """
        )
    if "farmer_status" in columns:
        db.execute(
            """
            UPDATE profiles SET occupation = 'farmer'
            WHERE TRIM(COALESCE(occupation, '')) = ''
              AND LOWER(COALESCE(farmer_status, '')) LIKE '%farmer%'
              AND LOWER(COALESCE(farmer_status, '')) NOT LIKE '%not%'
            """
        )
    if "employment_status" in columns:
        db.execute(
            """
            UPDATE profiles SET occupation = 'unemployed'
            WHERE TRIM(COALESCE(occupation, '')) = ''
              AND LOWER(COALESCE(employment_status, '')) LIKE '%unemploy%'
            """
        )


def _record_migration(db: sqlite3.Connection, version: int, name: str) -> None:
    db.execute(
        """
        INSERT OR IGNORE INTO schema_migrations (version, name, applied_at)
        VALUES (?, ?, ?)
        """,
        (version, name, _utc_now()),
    )
