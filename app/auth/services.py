from __future__ import annotations

from datetime import datetime, timezone
from functools import wraps

from flask import redirect, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

from app.database.models import User
from app.database.session import get_connection


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def create_user(email: str, password: str) -> tuple[bool, str]:
    email = email.strip().lower()
    if not email or "@" not in email:
        return False, "Enter a valid email address."
    if len(password) < 8:
        return False, "Use at least 8 characters for your password."

    try:
        with get_connection() as db:
            db.execute(
                """
                INSERT INTO users (email, password_hash, created_date)
                VALUES (?, ?, ?)
                """,
                (email, generate_password_hash(password), utc_now()),
            )
        return True, "Account created. Please log in."
    except Exception:
        return False, "An account with this email may already exist."


def authenticate_user(email: str, password: str) -> User | None:
    with get_connection() as db:
        row = db.execute(
            "SELECT * FROM users WHERE email = ?",
            (email.strip().lower(),),
        ).fetchone()

        if row is None or not check_password_hash(row["password_hash"], password):
            return None

        db.execute(
            "UPDATE users SET last_login_date = ? WHERE id = ?",
            (utc_now(), row["id"]),
        )

    return User(
        id=row["id"],
        email=row["email"],
        created_date=row["created_date"],
        last_login_date=row["last_login_date"],
    )


def get_user_by_id(user_id: int) -> User | None:
    with get_connection() as db:
        row = db.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()

    if row is None:
        return None

    return User(
        id=row["id"],
        email=row["email"],
        created_date=row["created_date"],
        last_login_date=row["last_login_date"],
    )


def current_user() -> User | None:
    user_id = session.get("user_id")
    if not user_id:
        return None
    return get_user_by_id(int(user_id))


def login_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if current_user() is None:
            return redirect(url_for("auth.login"))
        return view(*args, **kwargs)

    return wrapped_view


def delete_user(user_id: int) -> None:
    with get_connection() as db:
        db.execute("DELETE FROM users WHERE id = ?", (user_id,))
