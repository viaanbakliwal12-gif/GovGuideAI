from __future__ import annotations

import base64
from dataclasses import dataclass
import json
import os
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen


@dataclass(frozen=True)
class SMSDeliveryResult:
    provider_reference: str


class SMSDeliveryError(RuntimeError):
    """A safe provider error whose message never contains credentials or recipients."""

    def __init__(self, message: str, reason_code: str) -> None:
        super().__init__(message)
        self.reason_code = reason_code


def sms_provider_configured() -> bool:
    return bool(
        os.getenv("SMS_PROVIDER", "").strip().lower() == "twilio"
        and os.getenv("TWILIO_ACCOUNT_SID", "").strip()
        and os.getenv("TWILIO_AUTH_TOKEN", "").strip()
        and os.getenv("TWILIO_VERIFY_SERVICE_SID", "").strip()
    )


def send_sms_otp(destination: str) -> SMSDeliveryResult:
    account_sid, auth_token, service_sid = _configuration()
    response = _post_form(
        f"https://verify.twilio.com/v2/Services/{quote(service_sid, safe='')}/Verifications",
        {"To": destination, "Channel": "sms"},
        account_sid,
        auth_token,
        verification_check=False,
    )
    reference = str(response.get("sid", "")).strip()
    status = str(response.get("status", "")).strip().lower()
    if not reference or status != "pending":
        raise SMSDeliveryError(
            "Twilio Verify returned an invalid delivery response.",
            "invalid_response",
        )
    return SMSDeliveryResult(provider_reference=reference)


def verify_sms_otp(destination: str, code: str) -> bool:
    account_sid, auth_token, service_sid = _configuration()
    response = _post_form(
        f"https://verify.twilio.com/v2/Services/{quote(service_sid, safe='')}/VerificationCheck",
        {"To": destination, "Code": code},
        account_sid,
        auth_token,
        verification_check=True,
    )
    return str(response.get("status", "")).strip().lower() == "approved"


def cancel_sms_verification(provider_reference: str) -> None:
    account_sid, auth_token, service_sid = _configuration()
    reference = str(provider_reference or "").strip()
    if not reference:
        return
    response = _post_form(
        (
            f"https://verify.twilio.com/v2/Services/{quote(service_sid, safe='')}"
            f"/Verifications/{quote(reference, safe='')}"
        ),
        {"Status": "canceled"},
        account_sid,
        auth_token,
        verification_check=False,
    )
    if str(response.get("status", "")).strip().lower() != "canceled":
        raise SMSDeliveryError(
            "Twilio Verify did not confirm cancellation of the earlier code.",
            "cancellation_failed",
        )


def _configuration() -> tuple[str, str, str]:
    provider = os.getenv("SMS_PROVIDER", "").strip().lower()
    account_sid = os.getenv("TWILIO_ACCOUNT_SID", "").strip()
    auth_token = os.getenv("TWILIO_AUTH_TOKEN", "").strip()
    service_sid = os.getenv("TWILIO_VERIFY_SERVICE_SID", "").strip()
    if provider != "twilio" or not account_sid or not auth_token or not service_sid:
        raise SMSDeliveryError("SMS delivery is not configured.", "not_configured")
    return account_sid, auth_token, service_sid


def _post_form(
    url: str,
    payload: dict[str, str],
    account_sid: str,
    auth_token: str,
    *,
    verification_check: bool,
) -> dict:
    credentials = base64.b64encode(
        f"{account_sid}:{auth_token}".encode("utf-8")
    ).decode("ascii")
    provider_request = Request(
        url,
        data=urlencode(payload).encode("utf-8"),
        headers={
            "Authorization": f"Basic {credentials}",
            "Content-Type": "application/x-www-form-urlencoded",
        },
        method="POST",
    )
    try:
        with urlopen(provider_request, timeout=12) as response:
            status = int(response.status)
            body = response.read()
    except HTTPError as error:
        raise _http_delivery_error(
            int(error.code),
            verification_check=verification_check,
        ) from error
    except (URLError, TimeoutError, OSError) as error:
        raise SMSDeliveryError("Twilio Verify could not be reached.", "network_error") from error

    if status >= 300:
        raise _http_delivery_error(status, verification_check=verification_check)
    try:
        parsed = json.loads(body.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as error:
        raise SMSDeliveryError(
            "Twilio Verify returned an invalid response.",
            "invalid_response",
        ) from error
    if not isinstance(parsed, dict):
        raise SMSDeliveryError(
            "Twilio Verify returned an invalid response.",
            "invalid_response",
        )
    return parsed


def _http_delivery_error(status: int, *, verification_check: bool) -> SMSDeliveryError:
    if status in {401, 403}:
        return SMSDeliveryError(
            "Twilio Verify rejected its authentication or service configuration.",
            "authentication_or_service",
        )
    if verification_check and status in {400, 404, 422}:
        return SMSDeliveryError(
            "Twilio Verify did not approve the submitted code.",
            "invalid_code",
        )
    if status in {400, 404, 422}:
        return SMSDeliveryError(
            "Twilio Verify rejected the destination, code, or service request.",
            "request_rejected",
        )
    if status == 429:
        return SMSDeliveryError("Twilio Verify rate limit was reached.", "rate_limited")
    if status >= 500:
        return SMSDeliveryError("Twilio Verify is temporarily unavailable.", "provider_unavailable")
    return SMSDeliveryError("Twilio Verify rejected the request.", "delivery_rejected")
