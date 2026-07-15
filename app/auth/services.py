from __future__ import annotations

from datetime import datetime, timezone
from functools import wraps

from flask import jsonify, redirect, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

from app.auth.validators import IdentifierValidationError, normalize_email
from app.database.models import User
from app.database.session import get_connection


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def create_user(email: str, password: str) -> tuple[bool, str]:
    try:
        email = normalize_email(email)
    except IdentifierValidationError:
        return False, "Enter a valid email address."
    if len(password) < 8:
        return False, "Use at least 8 characters for your password."

    try:
        with get_connection() as db:
            db.execute(
                """
                INSERT INTO users (
                    email, password_hash, created_date, created_at
                ) VALUES (?, ?, ?, ?)
                """,
                (email, generate_password_hash(password), utc_now(), utc_now()),
            )
        return True, "Account created. Please log in."
    except Exception:
        return False, "An account with this email may already exist."


def authenticate_user(email: str, password: str) -> User | None:
    try:
        normalized_email = normalize_email(email)
    except IdentifierValidationError:
        return None

    with get_connection() as db:
        row = db.execute(
            """
            SELECT * FROM users
            WHERE deleted_at IS NULL AND (email = ? OR verified_email = ?)
            ORDER BY CASE WHEN verified_email = ? THEN 0 ELSE 1 END, id
            LIMIT 1
            """,
            (normalized_email, normalized_email, normalized_email),
        ).fetchone()

        if (
            row is None
            or not row["password_hash"]
            or not check_password_hash(row["password_hash"], password)
        ):
            return None

        now = utc_now()
        db.execute(
            "UPDATE users SET last_login_date = ?, last_login_at = ? WHERE id = ?",
            (now, now, row["id"]),
        )
        row = db.execute("SELECT * FROM users WHERE id = ?", (row["id"],)).fetchone()

    return user_from_row(row)


def get_user_by_id(user_id: int) -> User | None:
    with get_connection() as db:
        row = db.execute(
            "SELECT * FROM users WHERE id = ? AND deleted_at IS NULL",
            (user_id,),
        ).fetchone()

    if row is None:
        return None

    return user_from_row(row)


def user_from_row(row) -> User:
    return User(
        id=row["id"],
        email=row["email"],
        created_date=row["created_date"],
        last_login_date=row["last_login_date"],
        verified_email=row["verified_email"],
        verified_phone=row["verified_phone"],
        email_verified_at=row["email_verified_at"],
        phone_verified_at=row["phone_verified_at"],
        is_admin=bool(row["is_admin"]),
        deleted_at=row["deleted_at"],
    )


def current_user() -> User | None:
    user_id = session.get("user_id")
    if not user_id:
        return None
    return get_user_by_id(int(user_id))


def establish_user_session(user: User) -> None:
    from app.auth.guest_service import end_guest_session

    end_guest_session()
    session.clear()
    session["user_id"] = user.id
    session.permanent = True


def login_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if current_user() is None:
            return redirect(url_for("auth.login"))
        return view(*args, **kwargs)

    return wrapped_view


def assistant_access_required(view):
    """Allow either a verified/legacy user session or an active guest session."""

    @wraps(view)
    def wrapped_view(*args, **kwargs):
        from app.auth.guest_service import current_guest_session

        if current_user() is None and current_guest_session() is None:
            if request.path.startswith("/api/"):
                return jsonify({"error": "Please sign in or continue as a guest."}), 401
            return redirect(url_for("auth.login"))
        return view(*args, **kwargs)

    return wrapped_view


def current_subject_key() -> str | None:
    user = current_user()
    if user is not None:
        return f"user:{user.id}"

    from app.auth.guest_service import current_guest_session

    guest = current_guest_session()
    return guest.subject_key if guest else None


def is_guest() -> bool:
    if current_user() is not None:
        return False
    from app.auth.guest_service import current_guest_session

    return current_guest_session() is not None


def delete_user(user_id: int) -> None:
    with get_connection() as db:
        db.execute("DELETE FROM users WHERE id = ?", (user_id,))
