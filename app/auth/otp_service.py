from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import base64
import hashlib
import hmac
import math
import os
import re
import secrets
import sqlite3
from threading import Lock

from cryptography.fernet import Fernet, InvalidToken
from flask import current_app
from werkzeug.security import check_password_hash, generate_password_hash

from app.auth.email_provider import EmailDeliveryError, send_email_otp
from app.auth.sms_provider import SMSDeliveryError, send_sms_otp
from app.auth.validators import mask_destination, normalize_email, normalize_phone_number
from app.database.models import OTPChallenge, User
from app.database.session import get_connection


GENERIC_DELIVERY_MESSAGE = (
    "We could not send a verification code. Check the address or number and try again."
)
GENERIC_CODE_MESSAGE = "That code is incorrect or has expired."
COOLDOWN_MESSAGE = "Please wait before requesting another code."


class OTPServiceError(RuntimeError):
    def __init__(self, message: str, error_key: str, status_code: int = 400) -> None:
        super().__init__(message)
        self.error_key = error_key
        self.status_code = status_code


@dataclass(frozen=True)
class ChallengeState:
    public_id: str
    channel: str
    purpose: str
    masked_destination: str
    expires_at: str
    cooldown_remaining: int
    expired: bool
    development_code: str | None = None


@dataclass(frozen=True)
class VerificationResult:
    user: User
    is_new_user: bool


_development_codes: dict[str, str] = {}
_development_codes_lock = Lock()


def request_otp(
    channel: str,
    destination_value: str,
    country_code: str | None,
    purpose: str,
    request_ip: str,
) -> ChallengeState:
    clean_channel = "email" if channel == "email" else "sms" if channel in {"phone", "sms"} else ""
    if not clean_channel or purpose not in {"login", "signup"}:
        raise OTPServiceError(GENERIC_DELIVERY_MESSAGE, "couldNotSendCode")

    destination = (
        normalize_email(destination_value)
        if clean_channel == "email"
        else normalize_phone_number(destination_value, country_code)
    )
    now = _now()
    destination_hash = _stable_hash(f"destination:{clean_channel}:{destination}")
    ip_hash = _stable_hash(f"ip:{request_ip or 'unknown'}")
    _enforce_request_limits(destination_hash, ip_hash, now)

    otp = f"{secrets.randbelow(1_000_000):06d}"
    public_id = secrets.token_urlsafe(24)
    expires_at = now + timedelta(minutes=_setting("OTP_EXPIRY_MINUTES", 10, minimum=1))
    otp_hash = generate_password_hash(f"{otp}:{_otp_pepper()}")
    encrypted_destination = _fernet().encrypt(destination.encode("utf-8")).decode("ascii")

    with get_connection() as db:
        latest = db.execute(
            """
            SELECT resend_count FROM otp_challenges
            WHERE destination_hash = ?
            ORDER BY created_at DESC, id DESC LIMIT 1
            """,
            (destination_hash,),
        ).fetchone()
        resend_count = (int(latest["resend_count"]) + 1) if latest else 0

        # A newly requested code always supersedes every older active code.
        db.execute(
            """
            UPDATE otp_challenges SET used_at = ?
            WHERE destination_hash = ? AND used_at IS NULL
            """,
            (_iso(now), destination_hash),
        )
        db.execute(
            """
            INSERT INTO otp_challenges (
                public_id, destination_hash, destination_encrypted, channel,
                purpose, otp_hash, expires_at, attempts, resend_count,
                used_at, created_at, last_sent_at, requested_ip_hash
            ) VALUES (?, ?, ?, ?, ?, ?, ?, 0, ?, NULL, ?, ?, ?)
            """,
            (
                public_id,
                destination_hash,
                encrypted_destination,
                clean_channel,
                purpose,
                otp_hash,
                _iso(expires_at),
                resend_count,
                _iso(now),
                _iso(now),
                ip_hash,
            ),
        )

    try:
        _deliver_code(clean_channel, destination, otp, public_id)
    except (EmailDeliveryError, SMSDeliveryError):
        with get_connection() as db:
            db.execute(
                "UPDATE otp_challenges SET used_at = ? WHERE public_id = ?",
                (_iso(_now()), public_id),
            )
        _remove_development_code(public_id)
        raise OTPServiceError(GENERIC_DELIVERY_MESSAGE, "couldNotSendCode", 502)

    return ChallengeState(
        public_id=public_id,
        channel=clean_channel,
        purpose=purpose,
        masked_destination=mask_destination(destination, clean_channel),
        expires_at=_iso(expires_at),
        cooldown_remaining=_setting("OTP_RESEND_COOLDOWN_SECONDS", 60, minimum=1),
        expired=False,
        development_code=_get_development_code(public_id),
    )


def resend_otp(public_id: str, request_ip: str) -> ChallengeState:
    challenge = _get_challenge(public_id)
    if challenge is None:
        raise OTPServiceError(GENERIC_CODE_MESSAGE, "incorrectOrExpiredCode")
    try:
        destination = _decrypt_destination(challenge.destination_encrypted)
    except OTPServiceError:
        raise OTPServiceError(GENERIC_DELIVERY_MESSAGE, "couldNotSendCode")
    return request_otp(
        challenge.channel,
        destination,
        None,
        challenge.purpose,
        request_ip,
    )


def verify_otp(public_id: str, code: str) -> VerificationResult:
    now = _now()
    challenge = _get_challenge(public_id)
    if challenge is None or not _challenge_is_usable(challenge, now):
        raise OTPServiceError(GENERIC_CODE_MESSAGE, "incorrectOrExpiredCode")

    clean_code = re.sub(r"\s+", "", str(code or ""))
    is_correct = bool(re.fullmatch(r"\d{6}", clean_code)) and check_password_hash(
        challenge.otp_hash,
        f"{clean_code}:{_otp_pepper()}",
    )
    if not is_correct:
        with get_connection() as db:
            db.execute(
                "UPDATE otp_challenges SET attempts = attempts + 1 WHERE public_id = ?",
                (public_id,),
            )
        raise OTPServiceError(GENERIC_CODE_MESSAGE, "incorrectOrExpiredCode")

    destination = _decrypt_destination(challenge.destination_encrypted)
    with get_connection() as db:
        # Mark every challenge for this destination used, including races and
        # earlier resend attempts, before creating the authenticated session.
        db.execute(
            """
            UPDATE otp_challenges SET used_at = ?
            WHERE destination_hash = ? AND used_at IS NULL
            """,
            (_iso(now), challenge.destination_hash),
        )
        user, is_new = _find_or_create_verified_user(db, challenge.channel, destination, now)

    _remove_development_code(public_id)
    return VerificationResult(user=user, is_new_user=is_new)


def get_challenge_state(public_id: str) -> ChallengeState | None:
    challenge = _get_challenge(public_id)
    if challenge is None:
        return None
    try:
        destination = _decrypt_destination(challenge.destination_encrypted)
    except OTPServiceError:
        return None

    now = _now()
    sent_at = _parse_time(challenge.last_sent_at)
    cooldown_until = sent_at + timedelta(
        seconds=_setting("OTP_RESEND_COOLDOWN_SECONDS", 60, minimum=1)
    )
    cooldown_remaining = max(0, math.ceil((cooldown_until - now).total_seconds()))
    expired = now >= _parse_time(challenge.expires_at) or challenge.used_at is not None
    return ChallengeState(
        public_id=challenge.public_id,
        channel=challenge.channel,
        purpose=challenge.purpose,
        masked_destination=mask_destination(destination, challenge.channel),
        expires_at=challenge.expires_at,
        cooldown_remaining=cooldown_remaining,
        expired=expired,
        development_code=_get_development_code(public_id),
    )


def development_test_mode_enabled() -> bool:
    enabled = os.getenv("OTP_TEST_MODE", "false").strip().lower() in {"1", "true", "yes", "on"}
    environment = os.getenv("APP_ENV", os.getenv("FLASK_ENV", "development")).strip().lower()
    if enabled and environment in {"production", "prod"}:
        raise RuntimeError("OTP_TEST_MODE cannot be enabled when APP_ENV is production.")
    return enabled


def _deliver_code(channel: str, destination: str, otp: str, public_id: str) -> None:
    if development_test_mode_enabled():
        with _development_codes_lock:
            _development_codes[public_id] = otp
        return
    if channel == "email":
        send_email_otp(destination, otp)
    else:
        send_sms_otp(destination, otp)


def _enforce_request_limits(destination_hash: str, ip_hash: str, now: datetime) -> None:
    window_start = _iso(now - timedelta(hours=1))
    with get_connection() as db:
        destination_count = db.execute(
            """
            SELECT COUNT(*) AS total FROM otp_challenges
            WHERE destination_hash = ? AND created_at >= ?
            """,
            (destination_hash, window_start),
        ).fetchone()["total"]
        ip_count = db.execute(
            """
            SELECT COUNT(*) AS total FROM otp_challenges
            WHERE requested_ip_hash = ? AND created_at >= ?
            """,
            (ip_hash, window_start),
        ).fetchone()["total"]
        latest = db.execute(
            """
            SELECT last_sent_at FROM otp_challenges
            WHERE destination_hash = ?
            ORDER BY created_at DESC, id DESC LIMIT 1
            """,
            (destination_hash,),
        ).fetchone()

    if destination_count >= _setting("OTP_MAX_REQUESTS_PER_DESTINATION", 5, minimum=1):
        raise OTPServiceError(COOLDOWN_MESSAGE, "waitBeforeCode", 429)
    if ip_count >= _setting("OTP_MAX_REQUESTS_PER_IP", 20, minimum=1):
        raise OTPServiceError(COOLDOWN_MESSAGE, "waitBeforeCode", 429)
    if latest:
        next_allowed = _parse_time(latest["last_sent_at"]) + timedelta(
            seconds=_setting("OTP_RESEND_COOLDOWN_SECONDS", 60, minimum=1)
        )
        if now < next_allowed:
            raise OTPServiceError(COOLDOWN_MESSAGE, "waitBeforeCode", 429)


def _challenge_is_usable(challenge: OTPChallenge, now: datetime) -> bool:
    return (
        challenge.used_at is None
        and now < _parse_time(challenge.expires_at)
        and challenge.attempts < _setting("OTP_MAX_ATTEMPTS", 5, minimum=1)
    )


def _get_challenge(public_id: str) -> OTPChallenge | None:
    with get_connection() as db:
        row = db.execute(
            "SELECT * FROM otp_challenges WHERE public_id = ?",
            (str(public_id or ""),),
        ).fetchone()
    if row is None:
        return None
    return OTPChallenge(**{field: row[field] for field in OTPChallenge.__dataclass_fields__})


def _find_or_create_verified_user(
    db,
    channel: str,
    destination: str,
    now: datetime,
) -> tuple[User, bool]:
    timestamp = _iso(now)
    if channel == "email":
        row = db.execute(
            """
            SELECT * FROM users
            WHERE verified_email = ? OR email = ?
            ORDER BY CASE WHEN verified_email = ? THEN 0 ELSE 1 END, id
            LIMIT 1
            """,
            (destination, destination, destination),
        ).fetchone()
    else:
        row = db.execute(
            "SELECT * FROM users WHERE verified_phone = ? LIMIT 1",
            (destination,),
        ).fetchone()

    is_new = row is None
    if row is None:
        try:
            if channel == "email":
                cursor = db.execute(
                    """
                    INSERT INTO users (
                        email, password_hash, created_date, last_login_date,
                        verified_email, verified_phone, email_verified_at,
                        phone_verified_at, created_at, last_login_at
                    ) VALUES (?, NULL, ?, ?, ?, NULL, ?, NULL, ?, ?)
                    """,
                    (destination, timestamp, timestamp, destination, timestamp, timestamp, timestamp),
                )
            else:
                cursor = db.execute(
                    """
                    INSERT INTO users (
                        email, password_hash, created_date, last_login_date,
                        verified_email, verified_phone, email_verified_at,
                        phone_verified_at, created_at, last_login_at
                    ) VALUES (NULL, NULL, ?, ?, NULL, ?, NULL, ?, ?, ?)
                    """,
                    (timestamp, timestamp, destination, timestamp, timestamp, timestamp),
                )
            user_id = cursor.lastrowid
        except sqlite3.IntegrityError:
            # A concurrent successful verification may have inserted the same
            # normalized identifier first. Reuse it; never create a duplicate.
            lookup_column = "verified_email" if channel == "email" else "verified_phone"
            concurrent = db.execute(
                f"SELECT id FROM users WHERE {lookup_column} = ? LIMIT 1",
                (destination,),
            ).fetchone()
            if concurrent is None:
                raise
            user_id = concurrent["id"]
            is_new = False
            db.execute(
                "UPDATE users SET last_login_date = ?, last_login_at = ? WHERE id = ?",
                (timestamp, timestamp, user_id),
            )
    else:
        user_id = row["id"]
        if channel == "email":
            db.execute(
                """
                UPDATE users SET
                    email = COALESCE(email, ?), verified_email = ?,
                    email_verified_at = COALESCE(email_verified_at, ?),
                    last_login_date = ?, last_login_at = ?
                WHERE id = ?
                """,
                (destination, destination, timestamp, timestamp, timestamp, user_id),
            )
        else:
            db.execute(
                """
                UPDATE users SET
                    verified_phone = ?,
                    phone_verified_at = COALESCE(phone_verified_at, ?),
                    last_login_date = ?, last_login_at = ?
                WHERE id = ?
                """,
                (destination, timestamp, timestamp, timestamp, user_id),
            )

    updated = db.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    return _user_from_row(updated), is_new


def _user_from_row(row) -> User:
    return User(
        id=row["id"],
        email=row["email"],
        created_date=row["created_date"],
        last_login_date=row["last_login_date"],
        verified_email=row["verified_email"],
        verified_phone=row["verified_phone"],
        email_verified_at=row["email_verified_at"],
        phone_verified_at=row["phone_verified_at"],
    )


def _fernet() -> Fernet:
    configured_key = os.getenv("OTP_DESTINATION_KEY", "").strip()
    if configured_key:
        try:
            return Fernet(configured_key.encode("ascii"))
        except (ValueError, TypeError) as error:
            raise RuntimeError("OTP_DESTINATION_KEY must be a valid Fernet key.") from error
    derived = hashlib.sha256(str(current_app.secret_key).encode("utf-8")).digest()
    return Fernet(base64.urlsafe_b64encode(derived))


def _decrypt_destination(value: str) -> str:
    try:
        return _fernet().decrypt(value.encode("ascii")).decode("utf-8")
    except (InvalidToken, ValueError, UnicodeError) as error:
        raise OTPServiceError(GENERIC_CODE_MESSAGE, "incorrectOrExpiredCode") from error


def _stable_hash(value: str) -> str:
    key = _otp_pepper().encode("utf-8")
    return hmac.new(key, value.encode("utf-8"), hashlib.sha256).hexdigest()


def _otp_pepper() -> str:
    return os.getenv("OTP_PEPPER", "").strip() or str(current_app.secret_key)


def _setting(name: str, default: int, minimum: int = 0) -> int:
    try:
        value = int(os.getenv(name, str(default)))
    except ValueError:
        value = default
    return max(minimum, value)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(value: datetime) -> str:
    return value.isoformat(timespec="seconds")


def _parse_time(value: str) -> datetime:
    parsed = datetime.fromisoformat(value)
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def _get_development_code(public_id: str) -> str | None:
    if not development_test_mode_enabled():
        return None
    with _development_codes_lock:
        return _development_codes.get(public_id)


def _remove_development_code(public_id: str) -> None:
    with _development_codes_lock:
        _development_codes.pop(public_id, None)
