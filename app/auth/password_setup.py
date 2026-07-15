from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import hashlib
import hmac
import os
import secrets

from flask import current_app

from app.auth.services import _password_hash, get_user_by_id, utc_now
from app.auth.validators import (
    IdentifierValidationError,
    mask_destination,
    normalize_email,
    password_validation_error,
)
from app.database.models import User
from app.database.session import get_connection


class PasswordSetupError(ValueError):
    def __init__(self, message: str, field: str = "form"):
        super().__init__(message)
        self.message = message
        self.field = field


@dataclass(frozen=True)
class PasswordSetupToken:
    token: str
    user_id: int
    account_label: str
    expires_at: str


@dataclass(frozen=True)
class PasswordSetupState:
    user_id: int
    account_label: str
    existing_email: str | None
    email_required: bool
    expires_at: str


def create_password_setup_token(
    user_id: int,
    admin_user_id: int,
) -> PasswordSetupToken:
    """Create a single-use setup link for an active passwordless account."""

    now = utc_now()
    expires_at = (
        datetime.now(timezone.utc) + timedelta(minutes=_expiry_minutes())
    ).isoformat(timespec="seconds")
    public_id = secrets.token_hex(16)
    secret = secrets.token_urlsafe(32)
    token = f"{public_id}.{secret}"

    with get_connection() as db:
        db.execute("BEGIN IMMEDIATE")
        admin = db.execute(
            """
            SELECT 1 FROM users
            WHERE id = ? AND is_admin = 1 AND deleted_at IS NULL
            """,
            (int(admin_user_id),),
        ).fetchone()
        if admin is None:
            raise PasswordSetupError("Administrator access is required.")

        user = db.execute(
            """
            SELECT id, email, verified_email, verified_phone, password_hash
            FROM users
            WHERE id = ? AND deleted_at IS NULL
            """,
            (int(user_id),),
        ).fetchone()
        if user is None:
            raise PasswordSetupError("That account is not available.")
        if user["password_hash"]:
            raise PasswordSetupError("That account already has password access.")

        db.execute(
            """
            UPDATE password_setup_tokens
            SET used_at = ?
            WHERE user_id = ? AND used_at IS NULL
            """,
            (now, int(user_id)),
        )
        db.execute(
            """
            INSERT INTO password_setup_tokens (
                public_id, user_id, token_hash, created_at, expires_at,
                created_by_admin_id
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                public_id,
                int(user_id),
                _hash_secret(secret),
                now,
                expires_at,
                int(admin_user_id),
            ),
        )

    return PasswordSetupToken(
        token=token,
        user_id=int(user_id),
        account_label=_account_label(user),
        expires_at=expires_at,
    )


def get_password_setup_state(token: str) -> PasswordSetupState | None:
    parts = _token_parts(token)
    if parts is None:
        return None
    public_id, secret = parts
    with get_connection() as db:
        row = db.execute(
            """
            SELECT
                t.token_hash, t.expires_at, t.used_at,
                u.id AS user_id, u.email, u.verified_email,
                u.verified_phone, u.password_hash, u.deleted_at
            FROM password_setup_tokens t
            JOIN users u ON u.id = t.user_id
            WHERE t.public_id = ?
            LIMIT 1
            """,
            (public_id,),
        ).fetchone()

    if not _valid_row(row, secret):
        return None
    email = row["email"] or row["verified_email"]
    return PasswordSetupState(
        user_id=int(row["user_id"]),
        account_label=_account_label(row),
        existing_email=str(email) if email else None,
        email_required=not bool(email),
        expires_at=str(row["expires_at"]),
    )


def complete_password_setup(
    token: str,
    *,
    email: str,
    password: str,
) -> User:
    password_error = password_validation_error(password)
    if password_error:
        raise PasswordSetupError(password_error, "password")

    parts = _token_parts(token)
    if parts is None:
        raise PasswordSetupError("This password setup link is invalid or has expired.")
    public_id, secret = parts
    now = utc_now()

    with get_connection() as db:
        db.execute("BEGIN IMMEDIATE")
        row = db.execute(
            """
            SELECT
                t.token_hash, t.expires_at, t.used_at,
                u.id AS user_id, u.email, u.verified_email,
                u.verified_phone, u.password_hash, u.deleted_at
            FROM password_setup_tokens t
            JOIN users u ON u.id = t.user_id
            WHERE t.public_id = ?
            LIMIT 1
            """,
            (public_id,),
        ).fetchone()
        if not _valid_row(row, secret):
            raise PasswordSetupError("This password setup link is invalid or has expired.")

        existing_email = row["email"] or row["verified_email"]
        try:
            login_email = normalize_email(existing_email or email)
        except IdentifierValidationError:
            raise PasswordSetupError("Enter a valid email address.", "email") from None

        duplicate = db.execute(
            """
            SELECT 1 FROM users
            WHERE id <> ? AND deleted_at IS NULL
              AND (
                LOWER(COALESCE(email, '')) = ?
                OR LOWER(COALESCE(verified_email, '')) = ?
              )
            LIMIT 1
            """,
            (int(row["user_id"]), login_email, login_email),
        ).fetchone()
        if duplicate is not None:
            raise PasswordSetupError(
                "An account with this email already exists.", "email"
            )

        db.execute(
            "UPDATE users SET email = ?, password_hash = ? WHERE id = ?",
            (login_email, _password_hash(password), int(row["user_id"])),
        )
        db.execute(
            "UPDATE password_setup_tokens SET used_at = ? WHERE public_id = ?",
            (now, public_id),
        )
        db.execute(
            """
            UPDATE password_setup_tokens
            SET used_at = COALESCE(used_at, ?)
            WHERE user_id = ?
            """,
            (now, int(row["user_id"])),
        )

    user = get_user_by_id(int(row["user_id"]))
    if user is None:
        raise PasswordSetupError("That account is not available.")
    return user


def _valid_row(row, secret: str) -> bool:
    return bool(
        row is not None
        and not row["used_at"]
        and not row["password_hash"]
        and not row["deleted_at"]
        and str(row["expires_at"]) > utc_now()
        and hmac.compare_digest(str(row["token_hash"]), _hash_secret(secret))
    )


def _token_parts(token: str) -> tuple[str, str] | None:
    public_id, separator, secret = str(token or "").partition(".")
    if not separator or len(public_id) != 32 or len(secret) < 32:
        return None
    return public_id, secret


def _hash_secret(secret: str) -> str:
    key = str(current_app.secret_key).encode("utf-8")
    return hmac.new(key, secret.encode("utf-8"), hashlib.sha256).hexdigest()


def _expiry_minutes() -> int:
    try:
        return max(5, min(120, int(os.getenv("PASSWORD_SETUP_TOKEN_MINUTES", "30"))))
    except ValueError:
        return 30


def _account_label(row) -> str:
    email = row["email"] or row["verified_email"]
    if email:
        return mask_destination(str(email), "email")
    if row["verified_phone"]:
        return f"Legacy phone account {mask_destination(str(row['verified_phone']), 'sms')}"
    return f"GovGuideAI user #{int(row['id'] if 'id' in row.keys() else row['user_id'])}"
