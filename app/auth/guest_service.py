from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import hashlib
import hmac
import os
import secrets

from flask import current_app, session

from app.database.session import get_connection


@dataclass(frozen=True)
class CurrentGuest:
    subject_key: str
    expires_at: str


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(value: datetime) -> str:
    return value.isoformat(timespec="seconds")


def _session_hash(token: str) -> str:
    key = str(current_app.secret_key).encode("utf-8")
    return hmac.new(key, token.encode("utf-8"), hashlib.sha256).hexdigest()


def start_guest_session(language: str = "en") -> CurrentGuest:
    now = _now()
    ttl_hours = max(1, int(os.getenv("GUEST_SESSION_TTL_HOURS", "24")))
    expires_at = now + timedelta(hours=ttl_hours)
    token = secrets.token_urlsafe(32)
    session_hash = _session_hash(token)

    session.clear()
    session["guest_token"] = token
    session["guest_language"] = language
    session.permanent = False

    with get_connection() as db:
        db.execute("DELETE FROM guest_sessions WHERE expires_at <= ?", (_iso(now),))
        db.execute(
            """
            INSERT INTO guest_sessions (session_hash, created_at, last_seen_at, expires_at)
            VALUES (?, ?, ?, ?)
            """,
            (session_hash, _iso(now), _iso(now), _iso(expires_at)),
        )
    return CurrentGuest(subject_key=f"guest:{session_hash}", expires_at=_iso(expires_at))


def current_guest_session() -> CurrentGuest | None:
    token = session.get("guest_token")
    if not token:
        return None

    now = _now()
    session_hash = _session_hash(str(token))
    with get_connection() as db:
        row = db.execute(
            """
            SELECT expires_at FROM guest_sessions
            WHERE session_hash = ? AND expires_at > ?
            """,
            (session_hash, _iso(now)),
        ).fetchone()
        if row is None:
            session.pop("guest_token", None)
            return None
        db.execute(
            "UPDATE guest_sessions SET last_seen_at = ? WHERE session_hash = ?",
            (_iso(now), session_hash),
        )
    return CurrentGuest(subject_key=f"guest:{session_hash}", expires_at=row["expires_at"])


def end_guest_session() -> None:
    token = session.get("guest_token")
    if not token:
        return
    with get_connection() as db:
        db.execute("DELETE FROM guest_sessions WHERE session_hash = ?", (_session_hash(str(token)),))


def update_guest_language(language: str) -> None:
    if current_guest_session() is not None:
        session["guest_language"] = language
