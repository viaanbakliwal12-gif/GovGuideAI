from __future__ import annotations

import base64
import os
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


class SMSDeliveryError(RuntimeError):
    """Raised without exposing provider details to the browser."""


def send_sms_otp(destination: str, otp: str) -> None:
    provider = os.getenv("SMS_PROVIDER", "").strip().lower()
    if provider != "twilio":
        raise SMSDeliveryError("SMS delivery is not configured.")

    account_id = os.getenv("SMS_ACCOUNT_ID", "").strip()
    api_key = os.getenv("SMS_API_KEY", "").strip()
    sender_id = os.getenv("SMS_SENDER_ID", "").strip()
    if not account_id or not api_key or not sender_id:
        raise SMSDeliveryError("SMS delivery is not configured.")

    body = (
        f"Your GovGuideAI verification code is {otp}. "
        "It expires shortly. Do not share it."
    )
    data = urlencode({"To": destination, "From": sender_id, "Body": body}).encode("utf-8")
    credentials = base64.b64encode(f"{account_id}:{api_key}".encode("utf-8")).decode("ascii")
    request = Request(
        f"https://api.twilio.com/2010-04-01/Accounts/{account_id}/Messages.json",
        data=data,
        headers={
            "Authorization": f"Basic {credentials}",
            "Content-Type": "application/x-www-form-urlencoded",
        },
        method="POST",
    )
    try:
        with urlopen(request, timeout=12) as response:
            if response.status >= 300:
                raise SMSDeliveryError("The SMS provider rejected the request.")
    except (HTTPError, URLError, TimeoutError) as error:
        raise SMSDeliveryError("The SMS provider could not deliver the code.") from error
