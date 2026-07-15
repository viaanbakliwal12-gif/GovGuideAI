from __future__ import annotations

from dataclasses import dataclass
import json
import os
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


@dataclass(frozen=True)
class EmailDeliveryResult:
    provider_reference: str | None = None


class EmailDeliveryError(RuntimeError):
    """A safe provider error whose message never contains credentials or recipients."""

    def __init__(self, message: str, reason_code: str) -> None:
        super().__init__(message)
        self.reason_code = reason_code


def email_provider_configured() -> bool:
    provider = os.getenv("EMAIL_PROVIDER", "").strip().lower()
    from_address = os.getenv("EMAIL_FROM_ADDRESS", "").strip()
    if provider == "resend":
        return bool(_resend_api_key() and from_address)
    if provider == "sendgrid":
        return bool(os.getenv("EMAIL_API_KEY", "").strip() and from_address)
    return False


def send_email_otp(destination: str, otp: str) -> EmailDeliveryResult:
    provider = os.getenv("EMAIL_PROVIDER", "").strip().lower()
    from_address = os.getenv("EMAIL_FROM_ADDRESS", "").strip()
    if not provider:
        raise EmailDeliveryError("Email delivery is not configured.", "not_configured")

    if provider == "resend":
        api_key = _resend_api_key()
        if not api_key or not from_address:
            raise EmailDeliveryError("Email delivery is not configured.", "not_configured")
        return _send_resend(destination, otp, api_key, from_address)

    # Preserve the provider already supported by older GovGuideAI deployments.
    if provider == "sendgrid":
        api_key = os.getenv("EMAIL_API_KEY", "").strip()
        if not api_key or not from_address:
            raise EmailDeliveryError("Email delivery is not configured.", "not_configured")
        return _send_sendgrid(destination, otp, api_key, from_address)

    raise EmailDeliveryError("The configured email provider is unsupported.", "unsupported_provider")


def _resend_api_key() -> str:
    # EMAIL_API_KEY remains a compatibility fallback for existing installations.
    return os.getenv("RESEND_API_KEY", "").strip() or os.getenv("EMAIL_API_KEY", "").strip()


def _message_text(otp: str) -> str:
    return (
        f"Your GovGuideAI verification code is {otp}. "
        "It expires shortly and can be used only once. Do not share this code."
    )


def _send_resend(
    destination: str,
    otp: str,
    api_key: str,
    from_address: str,
) -> EmailDeliveryResult:
    payload = {
        "from": from_address,
        "to": [destination],
        "subject": "Your GovGuideAI verification code",
        "text": _message_text(otp),
    }
    response = _post_json(
        "https://api.resend.com/emails",
        payload,
        {"Authorization": f"Bearer {api_key}"},
    )
    reference = str(response.get("id", "")).strip()
    if not reference:
        raise EmailDeliveryError(
            "The email provider returned an invalid success response.",
            "invalid_response",
        )
    return EmailDeliveryResult(provider_reference=reference)


def _send_sendgrid(
    destination: str,
    otp: str,
    api_key: str,
    from_address: str,
) -> EmailDeliveryResult:
    payload = {
        "personalizations": [{"to": [{"email": destination}]}],
        "from": {"email": from_address},
        "subject": "Your GovGuideAI verification code",
        "content": [{"type": "text/plain", "value": _message_text(otp)}],
    }
    _post_json(
        "https://api.sendgrid.com/v3/mail/send",
        payload,
        {"Authorization": f"Bearer {api_key}"},
        allow_empty=True,
    )
    return EmailDeliveryResult()


def _post_json(
    url: str,
    payload: dict,
    headers: dict[str, str],
    *,
    allow_empty: bool = False,
) -> dict:
    provider_request = Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", **headers},
        method="POST",
    )
    try:
        with urlopen(provider_request, timeout=12) as response:
            status = int(response.status)
            body = response.read()
    except HTTPError as error:
        raise _http_delivery_error(int(error.code)) from error
    except (URLError, TimeoutError, OSError) as error:
        raise EmailDeliveryError(
            "The email provider could not be reached.",
            "network_error",
        ) from error

    if status >= 300:
        raise _http_delivery_error(status)
    if not body:
        if allow_empty:
            return {}
        raise EmailDeliveryError(
            "The email provider returned an invalid success response.",
            "invalid_response",
        )
    try:
        parsed = json.loads(body.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as error:
        raise EmailDeliveryError(
            "The email provider returned an invalid success response.",
            "invalid_response",
        ) from error
    if not isinstance(parsed, dict):
        raise EmailDeliveryError(
            "The email provider returned an invalid success response.",
            "invalid_response",
        )
    return parsed


def _http_delivery_error(status: int) -> EmailDeliveryError:
    if status in {401, 403}:
        return EmailDeliveryError(
            "The email provider rejected its authentication or sender configuration.",
            "authentication_or_sender",
        )
    if status == 422:
        return EmailDeliveryError(
            "The email provider rejected the sender or delivery request.",
            "sender_or_recipient_rejected",
        )
    if status == 429:
        return EmailDeliveryError("The email provider rate limit was reached.", "rate_limited")
    if status >= 500:
        return EmailDeliveryError("The email provider is temporarily unavailable.", "provider_unavailable")
    return EmailDeliveryError("The email provider rejected the delivery request.", "delivery_rejected")
