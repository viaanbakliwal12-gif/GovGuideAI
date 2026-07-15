from __future__ import annotations

import json
import os
from urllib.error import HTTPError
import unittest
from unittest.mock import patch

from app.auth.email_provider import EmailDeliveryError, send_email_otp
from app.auth.sms_provider import (
    SMSDeliveryError,
    cancel_sms_verification,
    send_sms_otp,
    verify_sms_otp,
)


class _FakeResponse:
    def __init__(self, status: int, payload: dict | None = None) -> None:
        self.status = status
        self.payload = payload

    def read(self) -> bytes:
        if self.payload is None:
            return b""
        return json.dumps(self.payload).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False


class EmailProviderTests(unittest.TestCase):
    def test_resend_requires_configuration_and_verifies_success_id(self) -> None:
        with patch.dict(
            os.environ,
            {"EMAIL_PROVIDER": "resend", "RESEND_API_KEY": "", "EMAIL_FROM_ADDRESS": ""},
            clear=False,
        ):
            with self.assertRaises(EmailDeliveryError) as missing:
                send_email_otp("person@example.com", "123456")
        self.assertEqual(missing.exception.reason_code, "not_configured")

        settings = {
            "EMAIL_PROVIDER": "resend",
            "RESEND_API_KEY": "server-only-key",
            "EMAIL_FROM_ADDRESS": "GovGuideAI <verified@example.com>",
        }
        with patch.dict(os.environ, settings, clear=False):
            with patch(
                "app.auth.email_provider.urlopen",
                return_value=_FakeResponse(200, {"id": "email-id"}),
            ) as mocked:
                result = send_email_otp("person@example.com", "123456")
        self.assertEqual(result.provider_reference, "email-id")
        request = mocked.call_args.args[0]
        self.assertEqual(request.full_url, "https://api.resend.com/emails")
        self.assertIn(b"123456", request.data)

    def test_resend_classifies_authentication_and_invalid_success_responses(self) -> None:
        settings = {
            "EMAIL_PROVIDER": "resend",
            "RESEND_API_KEY": "server-only-key",
            "EMAIL_FROM_ADDRESS": "verified@example.com",
        }
        unauthorized = HTTPError("https://api.resend.com/emails", 401, "Unauthorized", None, None)
        with patch.dict(os.environ, settings, clear=False):
            with patch("app.auth.email_provider.urlopen", side_effect=unauthorized):
                with self.assertRaises(EmailDeliveryError) as auth_error:
                    send_email_otp("person@example.com", "123456")
            with patch(
                "app.auth.email_provider.urlopen",
                return_value=_FakeResponse(200, {}),
            ):
                with self.assertRaises(EmailDeliveryError) as invalid_response:
                    send_email_otp("person@example.com", "123456")
        self.assertEqual(auth_error.exception.reason_code, "authentication_or_sender")
        self.assertEqual(invalid_response.exception.reason_code, "invalid_response")


class TwilioVerifyProviderTests(unittest.TestCase):
    settings = {
        "SMS_PROVIDER": "twilio",
        "TWILIO_ACCOUNT_SID": "AC-server-only",
        "TWILIO_AUTH_TOKEN": "server-only-token",
        "TWILIO_VERIFY_SERVICE_SID": "VA-server-only",
    }

    def test_twilio_verify_start_check_and_cancel_responses(self) -> None:
        responses = [
            _FakeResponse(201, {"sid": "VE-reference", "status": "pending"}),
            _FakeResponse(200, {"status": "approved"}),
            _FakeResponse(200, {"status": "canceled"}),
        ]
        with patch.dict(os.environ, self.settings, clear=False):
            with patch("app.auth.sms_provider.urlopen", side_effect=responses) as mocked:
                delivery = send_sms_otp("+12025550187")
                approved = verify_sms_otp("+12025550187", "123456")
                cancel_sms_verification("VE-reference")

        self.assertEqual(delivery.provider_reference, "VE-reference")
        self.assertTrue(approved)
        urls = [call.args[0].full_url for call in mocked.call_args_list]
        self.assertTrue(urls[0].endswith("/Verifications"))
        self.assertTrue(urls[1].endswith("/VerificationCheck"))
        self.assertTrue(urls[2].endswith("/Verifications/VE-reference"))

    def test_twilio_invalid_code_and_unsupported_request_are_distinct(self) -> None:
        rejected = HTTPError("https://verify.twilio.com", 404, "Not found", None, None)
        with patch.dict(os.environ, self.settings, clear=False):
            with patch("app.auth.sms_provider.urlopen", side_effect=rejected):
                with self.assertRaises(SMSDeliveryError) as invalid_code:
                    verify_sms_otp("+12025550187", "123456")
            with patch("app.auth.sms_provider.urlopen", side_effect=rejected):
                with self.assertRaises(SMSDeliveryError) as destination_error:
                    send_sms_otp("+12025550187")
        self.assertEqual(invalid_code.exception.reason_code, "invalid_code")
        self.assertEqual(destination_error.exception.reason_code, "request_rejected")


if __name__ == "__main__":
    unittest.main()
