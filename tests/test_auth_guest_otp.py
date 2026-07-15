from __future__ import annotations

from datetime import datetime, timedelta, timezone
import os
from pathlib import Path
import re
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from werkzeug.security import generate_password_hash

from app.auth.sms_provider import SMSDeliveryError
from app.auth.validators import IdentifierValidationError, normalize_phone_number
from app.database.session import get_connection
from app.server import create_app


def _past_time() -> str:
    return (datetime.now(timezone.utc) - timedelta(minutes=1)).isoformat(timespec="seconds")


class AuthFlowTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.directory = TemporaryDirectory(ignore_cleanup_errors=True)
        self.database_path = Path(self.directory.name) / "test.sqlite3"
        self.database_patch = patch("app.database.session.DATABASE_PATH", self.database_path)
        self.database_patch.start()
        self.environment_patch = patch.dict(
            os.environ,
            {
                "SECRET_KEY": "test-secret-key",
                "OTP_PEPPER": "test-otp-pepper",
                "OTP_TEST_MODE": "true",
                "APP_ENV": "testing",
                "OTP_RESEND_COOLDOWN_SECONDS": "60",
                "OTP_EXPIRY_MINUTES": "10",
                "OTP_MAX_ATTEMPTS": "5",
            },
            clear=False,
        )
        self.environment_patch.start()
        self.app = create_app()
        self.app.config.update(TESTING=True, SECRET_KEY="test-secret-key")
        self.client = self.app.test_client()

    def tearDown(self) -> None:
        self.environment_patch.stop()
        self.database_patch.stop()
        self.directory.cleanup()

    def request_email_code(self, email: str = "person@example.com", purpose: str = "login"):
        response = self.client.post(
            "/auth/request-code",
            data={
                "purpose": purpose,
                "channel": "email",
                "email": email,
                "selected_language": "en",
            },
        )
        return response

    def request_phone_code(
        self,
        phone: str = "4155552671",
        country: str = "US",
        purpose: str = "login",
    ):
        return self.client.post(
            "/auth/request-code",
            data={
                "purpose": purpose,
                "channel": "phone",
                "country": country,
                "phone_number": phone,
                "selected_language": "en",
            },
        )

    def pending_challenge(self) -> str:
        with self.client.session_transaction() as browser_session:
            return str(browser_session["pending_otp"])

    def development_code(self) -> str:
        response = self.client.get("/verify")
        match = re.search(r"<code>(\d{6})</code>", response.get_data(as_text=True))
        self.assertIsNotNone(match)
        return match.group(1)

    def verify(self, code: str):
        return self.client.post(
            "/verify",
            data={"challenge_id": self.pending_challenge(), "code": code},
        )


class LanguageSelectionTests(AuthFlowTestCase):
    def test_language_selection_is_saved_server_side_and_redirects_once(self) -> None:
        response = self.client.post(
            "/language",
            data={"selected_language": "hi", "next": "/login"},
            follow_redirects=False,
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers["Location"], "/login")
        with self.client.session_transaction() as browser_session:
            self.assertTrue(browser_session["language_selected"])
            self.assertEqual(browser_session["selected_language"], "hi")

        login_page = self.client.get("/login").get_data(as_text=True)
        self.assertIn('data-language-selected="true"', login_page)
        self.assertIn('data-selected-language="hi"', login_page)

    def test_language_next_url_cannot_leave_the_application(self) -> None:
        response = self.client.post(
            "/language",
            data={"selected_language": "en", "next": "//example.com/escape"},
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers["Location"], "/login")


class GuestModeTests(AuthFlowTestCase):
    def test_guest_reaches_chat_without_creating_user_and_sees_limitations(self) -> None:
        response = self.client.post(
            "/guest",
            data={"selected_language": "en"},
            follow_redirects=True,
        )

        self.assertEqual(response.status_code, 200)
        page = response.get_data(as_text=True)
        self.assertIn("Guest mode", page)
        self.assertIn("Create an account to save your information", page)
        with get_connection() as db:
            self.assertEqual(db.execute("SELECT COUNT(*) FROM users").fetchone()[0], 0)
            self.assertEqual(db.execute("SELECT COUNT(*) FROM guest_sessions").fetchone()[0], 1)

    def test_guest_can_use_word_count_and_voice_but_not_profile(self) -> None:
        self.client.post("/guest", data={"selected_language": "en"})

        chat = self.client.post(
            "/api/chat",
            json={"message": "word count: one two three", "selectedLanguage": "en"},
        )
        self.assertEqual(chat.status_code, 200)
        self.assertEqual(chat.get_json()["toolsUsed"], ["Word Count"])

        with patch("app.voice.routes.generate_speech_audio", return_value=b"audio"):
            voice = self.client.post(
                "/api/voice/speak",
                json={"text": "Hello", "preferredLanguage": "en"},
            )
        self.assertEqual(voice.status_code, 200)
        self.assertEqual(self.client.get("/profile").status_code, 302)
        self.assertIn("/login", self.client.get("/profile").headers["Location"])

    def test_guest_sessions_are_server_side_and_isolated(self) -> None:
        self.client.post("/guest", data={"selected_language": "en"})
        with self.client.session_transaction() as browser_session:
            first_token = browser_session["guest_token"]

        another_client = self.app.test_client()
        another_client.post("/guest", data={"selected_language": "en"})
        with another_client.session_transaction() as browser_session:
            second_token = browser_session["guest_token"]

        self.assertNotEqual(first_token, second_token)
        with get_connection() as db:
            rows = db.execute("SELECT session_hash FROM guest_sessions").fetchall()
        self.assertEqual(len(rows), 2)
        self.assertTrue(all(row["session_hash"] not in {first_token, second_token} for row in rows))


class EmailOTPTests(AuthFlowTestCase):
    def test_invalid_email_is_rejected_before_challenge_creation(self) -> None:
        response = self.request_email_code("not-an-email")
        self.assertEqual(response.status_code, 400)
        self.assertIn("Enter a valid email address", response.get_data(as_text=True))
        with get_connection() as db:
            self.assertEqual(db.execute("SELECT COUNT(*) FROM otp_challenges").fetchone()[0], 0)

    def test_correct_email_code_creates_verified_user_without_plaintext_otp(self) -> None:
        response = self.request_email_code("New.Person@Example.COM", purpose="signup")
        self.assertEqual(response.status_code, 302)
        code = self.development_code()

        with get_connection() as db:
            challenge = db.execute("SELECT * FROM otp_challenges").fetchone()
            self.assertNotEqual(challenge["otp_hash"], code)
            self.assertNotIn("new.person@example.com", challenge["destination_encrypted"])
            self.assertNotIn(code, challenge["otp_hash"])

        verified = self.verify(code)
        self.assertEqual(verified.status_code, 200)
        self.assertIn("Verification successful", verified.get_data(as_text=True))
        with self.client.session_transaction() as browser_session:
            self.assertIn("user_id", browser_session)
            self.assertNotIn("pending_otp", browser_session)
        with get_connection() as db:
            user = db.execute("SELECT * FROM users").fetchone()
            self.assertEqual(user["email"], "new.person@example.com")
            self.assertEqual(user["verified_email"], "new.person@example.com")
            self.assertIsNotNone(user["email_verified_at"])
            self.assertIsNotNone(db.execute("SELECT used_at FROM otp_challenges").fetchone()[0])

    def test_incorrect_and_expired_codes_fail_generically(self) -> None:
        self.request_email_code()
        correct_code = self.development_code()

        incorrect = self.verify("000000" if correct_code != "000000" else "111111")
        self.assertEqual(incorrect.status_code, 400)
        self.assertIn("incorrect or has expired", incorrect.get_data(as_text=True))
        with get_connection() as db:
            attempts = db.execute("SELECT attempts FROM otp_challenges").fetchone()[0]
        self.assertEqual(attempts, 1)

        with get_connection() as db:
            db.execute("UPDATE otp_challenges SET expires_at = ?", (_past_time(),))
        expired = self.verify(correct_code)
        self.assertEqual(expired.status_code, 400)
        self.assertIn("incorrect or has expired", expired.get_data(as_text=True))

    def test_attempt_limit_blocks_a_later_correct_code(self) -> None:
        self.request_email_code()
        correct_code = self.development_code()
        wrong_code = "000000" if correct_code != "000000" else "111111"
        with patch.dict(os.environ, {"OTP_MAX_ATTEMPTS": "2"}, clear=False):
            self.assertEqual(self.verify(wrong_code).status_code, 400)
            self.assertEqual(self.verify(wrong_code).status_code, 400)
            blocked = self.verify(correct_code)
        self.assertEqual(blocked.status_code, 400)
        with get_connection() as db:
            self.assertEqual(db.execute("SELECT COUNT(*) FROM users").fetchone()[0], 0)

    def test_resend_cooldown_and_delivery_failure_are_clear(self) -> None:
        self.request_email_code()
        cooldown = self.request_email_code()
        self.assertEqual(cooldown.status_code, 429)
        self.assertIn("Please wait", cooldown.get_data(as_text=True))

        with patch.dict(os.environ, {"OTP_TEST_MODE": "false", "EMAIL_PROVIDER": ""}, clear=False):
            failure = self.request_email_code("other@example.com")
        self.assertEqual(failure.status_code, 502)
        self.assertIn("could not send a verification code", failure.get_data(as_text=True))

    def test_resend_after_cooldown_replaces_the_old_challenge(self) -> None:
        self.request_email_code()
        old_challenge = self.pending_challenge()
        with get_connection() as db:
            db.execute(
                "UPDATE otp_challenges SET last_sent_at = ? WHERE public_id = ?",
                (_past_time(), old_challenge),
            )

        resent = self.client.post(
            "/auth/resend-code",
            data={"challenge_id": old_challenge},
        )
        self.assertEqual(resent.status_code, 302)
        new_challenge = self.pending_challenge()
        self.assertNotEqual(new_challenge, old_challenge)
        with get_connection() as db:
            old = db.execute(
                "SELECT used_at FROM otp_challenges WHERE public_id = ?",
                (old_challenge,),
            ).fetchone()
            new = db.execute(
                "SELECT resend_count, used_at FROM otp_challenges WHERE public_id = ?",
                (new_challenge,),
            ).fetchone()
        self.assertIsNotNone(old["used_at"])
        self.assertEqual(new["resend_count"], 1)
        self.assertIsNone(new["used_at"])

    def test_production_cannot_enable_development_codes(self) -> None:
        with patch.dict(
            os.environ,
            {"APP_ENV": "production", "OTP_TEST_MODE": "true"},
            clear=False,
        ):
            with self.assertRaises(RuntimeError):
                create_app()

    def test_ip_rate_limit_applies_across_different_destinations(self) -> None:
        with patch.dict(
            os.environ,
            {"OTP_MAX_REQUESTS_PER_IP": "1", "OTP_RESEND_COOLDOWN_SECONDS": "1"},
            clear=False,
        ):
            first = self.request_email_code("first@example.com")
            second = self.request_email_code("second@example.com")
        self.assertEqual(first.status_code, 302)
        self.assertEqual(second.status_code, 429)


class PhoneOTPTests(AuthFlowTestCase):
    def test_phone_library_normalizes_international_numbers(self) -> None:
        self.assertEqual(normalize_phone_number("98765 43210", "IN"), "+919876543210")
        self.assertEqual(normalize_phone_number("415-555-2671", "US"), "+14155552671")
        with self.assertRaises(IdentifierValidationError):
            normalize_phone_number("123", "US")

    def test_phone_code_verifies_and_stores_e164_without_email(self) -> None:
        response = self.request_phone_code()
        self.assertEqual(response.status_code, 302)
        verified = self.verify(self.development_code())
        self.assertEqual(verified.status_code, 200)
        with get_connection() as db:
            user = db.execute("SELECT * FROM users").fetchone()
        self.assertEqual(user["verified_phone"], "+14155552671")
        self.assertIsNone(user["email"])

    def test_invalid_phone_and_sms_provider_failure_are_handled(self) -> None:
        invalid = self.request_phone_code("123", "US")
        self.assertEqual(invalid.status_code, 400)
        self.assertIn("valid phone number", invalid.get_data(as_text=True))

        with patch.dict(os.environ, {"OTP_TEST_MODE": "false", "SMS_PROVIDER": "twilio"}, clear=False):
            with patch(
                "app.auth.otp_service.send_sms_otp",
                side_effect=SMSDeliveryError("provider failure"),
            ):
                failure = self.request_phone_code("2025550187", "US")
        self.assertEqual(failure.status_code, 502)
        self.assertIn("could not send a verification code", failure.get_data(as_text=True))


class ExistingAccountTests(AuthFlowTestCase):
    def test_otp_signs_into_existing_password_account_and_preserves_profile(self) -> None:
        with get_connection() as db:
            db.execute(
                """
                INSERT INTO users (id, email, password_hash, created_date, created_at)
                VALUES (7, ?, ?, ?, ?)
                """,
                (
                    "existing@example.com",
                    generate_password_hash("password123"),
                    "2026-01-01",
                    "2026-01-01",
                ),
            )
            db.execute(
                """
                INSERT INTO profiles (
                    user_id, full_name, age, state, district, occupation,
                    location_type, preferred_language, updated_date
                ) VALUES (7, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                ("Existing User", "30", "Delhi", "New Delhi", "employed", "Urban", "en", "2026-01-01"),
            )

        self.request_email_code("existing@example.com")
        verified = self.verify(self.development_code())
        self.assertEqual(verified.status_code, 200)
        self.assertIn('window.location.href = "/"', verified.get_data(as_text=True))
        with get_connection() as db:
            self.assertEqual(db.execute("SELECT COUNT(*) FROM users").fetchone()[0], 1)
            user = db.execute("SELECT * FROM users").fetchone()
            profile = db.execute("SELECT * FROM profiles WHERE user_id = 7").fetchone()
        self.assertEqual(user["id"], 7)
        self.assertEqual(user["verified_email"], "existing@example.com")
        self.assertEqual(profile["full_name"], "Existing User")

    def test_legacy_password_login_still_works(self) -> None:
        with get_connection() as db:
            db.execute(
                """
                INSERT INTO users (email, password_hash, created_date, created_at)
                VALUES (?, ?, ?, ?)
                """,
                (
                    "legacy@example.com",
                    generate_password_hash("password123"),
                    "2026-01-01",
                    "2026-01-01",
                ),
            )
        response = self.client.post(
            "/login",
            data={"email": "legacy@example.com", "password": "password123"},
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn("/profile/setup", response.headers["Location"])


class SecurityBoundaryTests(AuthFlowTestCase):
    def test_csrf_is_required_outside_testing_mode(self) -> None:
        self.app.config["TESTING"] = False
        page = self.client.get("/login")
        match = re.search(r'name="_csrf_token" value="([^"]+)"', page.get_data(as_text=True))
        self.assertIsNotNone(match)

        rejected = self.client.post("/guest", data={"selected_language": "en"})
        accepted = self.client.post(
            "/guest",
            data={"selected_language": "en", "_csrf_token": match.group(1)},
        )
        self.assertEqual(rejected.status_code, 400)
        self.assertEqual(accepted.status_code, 302)

        cookie_headers = page.headers.getlist("Set-Cookie")
        self.assertTrue(any("HttpOnly" in value and "SameSite=Lax" in value for value in cookie_headers))


if __name__ == "__main__":
    unittest.main()
