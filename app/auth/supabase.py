from __future__ import annotations

from dataclasses import dataclass
import base64
import json
import os
import socket
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from app.auth.validators import IdentifierValidationError, normalize_email


class SupabaseConfigurationError(RuntimeError):
    pass


class SupabaseAuthenticationError(RuntimeError):
    pass


class SupabaseNetworkError(RuntimeError):
    pass


@dataclass(frozen=True)
class SupabaseIdentity:
    user_id: str
    email: str
    created_at: str | None
    email_confirmed_at: str | None


def public_supabase_config() -> tuple[str, str]:
    """Return only the browser-safe project URL and public anon/publishable key."""

    url = os.getenv("SUPABASE_URL", "").strip()
    anon_key = os.getenv("SUPABASE_ANON_KEY", "").strip()
    if not _valid_url(url) or not _public_key_is_safe(anon_key):
        raise SupabaseConfigurationError(
            "Supabase email login is not configured. Set SUPABASE_URL and "
            "SUPABASE_ANON_KEY to the project's public browser values."
        )
    return url.rstrip("/"), anon_key


def verify_supabase_access_token(access_token: str) -> SupabaseIdentity:
    """Ask Supabase Auth to authenticate a browser-issued access token."""

    token = str(access_token or "").strip()
    if not token or len(token) > 16_384:
        raise SupabaseAuthenticationError("The Supabase session is missing or invalid.")

    url, anon_key = public_supabase_config()
    auth_request = Request(
        f"{url}/auth/v1/user",
        headers={
            "apikey": anon_key,
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
        },
        method="GET",
    )
    try:
        with urlopen(auth_request, timeout=10) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except HTTPError as error:
        if error.code in {400, 401, 403}:
            raise SupabaseAuthenticationError(
                "The Supabase session is invalid or has expired."
            ) from None
        if error.code == 429:
            raise SupabaseAuthenticationError(
                "Supabase is rate limiting authentication requests. Try again shortly."
            ) from None
        raise SupabaseNetworkError(
            "Supabase could not validate the session right now."
        ) from None
    except (URLError, TimeoutError, socket.timeout, json.JSONDecodeError):
        raise SupabaseNetworkError(
            "Supabase could not validate the session. Check the network and try again."
        ) from None

    if not isinstance(payload, dict) or not payload.get("id") or not payload.get("email"):
        raise SupabaseAuthenticationError(
            "Supabase did not return a verified email identity."
        )
    try:
        email = normalize_email(str(payload["email"]))
    except IdentifierValidationError:
        raise SupabaseAuthenticationError(
            "Supabase did not return a valid email identity."
        ) from None

    return SupabaseIdentity(
        user_id=str(payload["id"]),
        email=email,
        created_at=_optional_string(payload.get("created_at")),
        email_confirmed_at=_optional_string(
            payload.get("email_confirmed_at") or payload.get("confirmed_at")
        ),
    )


def _valid_url(value: str) -> bool:
    if not value or value.startswith("your_"):
        return False
    parsed = urlparse(value)
    if parsed.username or parsed.password or parsed.query or parsed.fragment:
        return False
    if parsed.scheme == "https" and bool(parsed.netloc):
        return True
    return parsed.scheme == "http" and parsed.hostname in {"127.0.0.1", "localhost"}


def _public_key_is_safe(value: str) -> bool:
    if not value or value.startswith("your_") or value.startswith("sb_secret_"):
        return False
    payload = _jwt_payload(value)
    return not (payload and payload.get("role") == "service_role")


def _jwt_payload(value: str) -> dict | None:
    parts = value.split(".")
    if len(parts) != 3:
        return None
    try:
        encoded = parts[1] + ("=" * (-len(parts[1]) % 4))
        payload = json.loads(base64.urlsafe_b64decode(encoded).decode("utf-8"))
    except (ValueError, UnicodeDecodeError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def _optional_string(value) -> str | None:
    text = str(value or "").strip()
    return text or None
