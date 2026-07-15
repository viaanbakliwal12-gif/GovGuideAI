from __future__ import annotations

import json
import os
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class EmailDeliveryError(RuntimeError):
    """Raised without exposing provider details to the browser."""


def send_email_otp(destination: str, otp: str) -> None:
    provider = os.getenv("EMAIL_PROVIDER", "").strip().lower()
    api_key = os.getenv("EMAIL_API_KEY", "").strip()
    from_address = os.getenv("EMAIL_FROM_ADDRESS", "").strip()
    if not provider or not api_key or not from_address:
        raise EmailDeliveryError("Email delivery is not configured.")

    if provider == "resend":
        _send_resend(destination, otp, api_key, from_address)
        return
    if provider == "sendgrid":
        _send_sendgrid(destination, otp, api_key, from_address)
        return
    raise EmailDeliveryError("Unsupported email provider.")


def _message_text(otp: str) -> str:
    return (
        f"Your GovGuideAI verification code is {otp}. "
        "It expires shortly and can be used only once. Do not share this code."
    )


def _send_resend(destination: str, otp: str, api_key: str, from_address: str) -> None:
    payload = {
        "from": from_address,
        "to": [destination],
        "subject": "Your GovGuideAI verification code",
        "text": _message_text(otp),
    }
    _post_json(
        "https://api.resend.com/emails",
        payload,
        {"Authorization": f"Bearer {api_key}"},
    )


def _send_sendgrid(destination: str, otp: str, api_key: str, from_address: str) -> None:
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
    )


def _post_json(url: str, payload: dict, headers: dict[str, str]) -> None:
    request = Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", **headers},
        method="POST",
    )
    try:
        with urlopen(request, timeout=12) as response:
            if response.status >= 300:
                raise EmailDeliveryError("The email provider rejected the request.")
    except (HTTPError, URLError, TimeoutError) as error:
        raise EmailDeliveryError("The email provider could not deliver the code.") from error
