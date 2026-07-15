from __future__ import annotations

import os
from pathlib import Path
import re
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from werkzeug.security import check_password_hash

from app.database.session import get_connection
from app.server import create_app


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
                "FLASK_ENV": "development",
                "APP_ENV": "development",
                "PASSWORD_SETUP_TOKEN_MINUTES": "30",
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

    def signup(
        self,
        email: str = "person@example.com",
        password: str = "SecurePass123",
        confirmation: str | None = None,
    ):
        return self.client.post(
            "/signup",
            data={
                "email": email,
                "password": password,
                "confirm_password": password if confirmation is None else confirmation,
                "selected_language": "en",
            },
        )

    def create_completed_user(self, email: str = "complete@example.com") -> None:
        response = self.signup(email=email)
        self.assertEqual(response.status_code, 302)
        with get_connection() as db:
            user_id = db.execute(
                "SELECT id FROM users WHERE email = ?", (email,)
            ).fetchone()[0]
            db.execute(
                """
                INSERT INTO profiles (
                    user_id, full_name, age, state, district, occupation,
                    location_type, preferred_language, updated_date
                ) VALUES (?, 'Complete User', '30', 'Delhi', 'New Delhi',
                          'employed', 'urban', 'en', '2026-01-01')
                """,
                (user_id,),
            )


class PasswordAuthenticationTests(AuthFlowTestCase):
    def test_pages_are_complete_password_forms_without_otp_ui(self) -> None:
        login = self.client.get("/login").get_data(as_text=True)
        signup = self.client.get("/signup").get_data(as_text=True)
        combined = f"{login}\n{signup}".lower()

        self.assertIn('name="email"', login)
        self.assertIn('name="password"', login)
        self.assertIn('name="confirm_password"', signup)
        self.assertIn("continue as guest", combined)
        for forbidden in (
            "send code",
            "phone number",
            "country",
            "verification code",
            "resend code",
            "temporarily unavailable",
            "development otp",
            "one-time-code",
        ):
            self.assertNotIn(forbidden, combined)

        self.assertEqual(self.client.get("/verify").status_code, 404)
        self.assertEqual(self.client.post("/auth/request-code").status_code, 404)
        self.assertEqual(self.client.post("/auth/resend-code").status_code, 404)

    def test_signup_validates_email_password_and_confirmation_inline(self) -> None:
        invalid_email = self.signup(email="not-an-email")
        weak = self.signup(password="short1")
        mismatch = self.signup(confirmation="DifferentPass123")

        self.assertEqual(invalid_email.status_code, 400)
        self.assertIn("Enter a valid email address.", invalid_email.get_data(as_text=True))
        self.assertIn('class="field-error"', invalid_email.get_data(as_text=True))
        self.assertEqual(weak.status_code, 400)
        self.assertIn("at least 10 characters", weak.get_data(as_text=True))
        self.assertEqual(mismatch.status_code, 400)
        self.assertIn("Passwords do not match.", mismatch.get_data(as_text=True))

    def test_signup_hashes_password_and_redirects_to_profile_setup(self) -> None:
        response = self.signup(email="New.Person@Example.COM")

        self.assertEqual(response.status_code, 302)
        self.assertIn("/profile/setup", response.headers["Location"])
        with get_connection() as db:
            row = db.execute(
                "SELECT id, email, password_hash FROM users"
            ).fetchone()
        self.assertEqual(row["email"], "new.person@example.com")
        self.assertNotEqual(row["password_hash"], "SecurePass123")
        self.assertTrue(row["password_hash"].startswith("scrypt:"))
        self.assertTrue(check_password_hash(row["password_hash"], "SecurePass123"))
        with self.client.session_transaction() as browser_session:
            self.assertEqual(browser_session["user_id"], row["id"])

    def test_duplicate_email_is_rejected_without_creating_another_user(self) -> None:
        self.signup(email="duplicate@example.com")
        self.client.post("/logout")
        duplicate = self.signup(email="DUPLICATE@example.com")

        self.assertEqual(duplicate.status_code, 409)
        self.assertIn("already exists", duplicate.get_data(as_text=True))
        with get_connection() as db:
            self.assertEqual(db.execute("SELECT COUNT(*) FROM users").fetchone()[0], 1)

    def test_login_uses_generic_failure_and_routes_by_profile_state(self) -> None:
        self.signup(email="incomplete@example.com")
        self.client.post("/logout")

        unknown = self.client.post(
            "/login", data={"email": "unknown@example.com", "password": "WrongPass123"}
        )
        wrong = self.client.post(
            "/login", data={"email": "incomplete@example.com", "password": "WrongPass123"}
        )
        self.assertEqual(unknown.status_code, 401)
        self.assertEqual(wrong.status_code, 401)
        self.assertIn("Incorrect email or password.", unknown.get_data(as_text=True))
        self.assertIn("Incorrect email or password.", wrong.get_data(as_text=True))
        self.assertNotIn("unknown@example.com does not exist", unknown.get_data(as_text=True))

        incomplete = self.client.post(
            "/login",
            data={"email": "incomplete@example.com", "password": "SecurePass123"},
        )
        self.assertIn("/profile/setup", incomplete.headers["Location"])

        self.client.post("/logout")
        self.create_completed_user()
        self.client.post("/logout")
        complete = self.client.post(
            "/login",
            data={"email": "complete@example.com", "password": "SecurePass123"},
        )
        self.assertEqual(complete.headers["Location"], "/")

    def test_existing_profile_is_unchanged_by_login_and_logout(self) -> None:
        self.create_completed_user("preserved@example.com")
        self.client.post("/logout")
        before = None
        with get_connection() as db:
            before = dict(db.execute("SELECT * FROM profiles").fetchone())

        login = self.client.post(
            "/login",
            data={"email": "preserved@example.com", "password": "SecurePass123"},
        )
        self.assertEqual(login.headers["Location"], "/")
        logout = self.client.post("/logout")
        self.assertIn("/login", logout.headers["Location"])
        with get_connection() as db:
            after = dict(db.execute("SELECT * FROM profiles").fetchone())
        self.assertEqual(before, after)

    def test_startup_logs_password_auth_without_provider_warnings(self) -> None:
        with self.assertLogs("app.server", level="INFO") as captured:
            create_app()
        combined = "\n".join(captured.output)
        self.assertIn("Authentication: email and password", combined)
        self.assertNotIn("Email provider", combined)
        self.assertNotIn("SMS provider", combined)
        self.assertNotIn("Development OTP", combined)


class LanguageSelectionTests(AuthFlowTestCase):
    def test_language_selection_is_saved_server_side_and_redirects_once(self) -> None:
        response = self.client.post(
            "/language",
            data={"selected_language": "hi", "next": "/login"},
            follow_redirects=False,
        )
        self.assertEqual(response.headers["Location"], "/login")
        with self.client.session_transaction() as browser_session:
            self.assertTrue(browser_session["language_selected"])
            self.assertEqual(browser_session["selected_language"], "hi")

    def test_language_next_url_cannot_leave_the_application(self) -> None:
        response = self.client.post(
            "/language",
            data={"selected_language": "en", "next": "//example.com/escape"},
        )
        self.assertEqual(response.headers["Location"], "/login")


class GuestModeTests(AuthFlowTestCase):
    def test_guest_reaches_chat_without_creating_user_and_sees_limitations(self) -> None:
        response = self.client.post(
            "/guest", data={"selected_language": "en"}, follow_redirects=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("Guest mode", response.get_data(as_text=True))
        with get_connection() as db:
            self.assertEqual(db.execute("SELECT COUNT(*) FROM users").fetchone()[0], 0)
            self.assertEqual(db.execute("SELECT COUNT(*) FROM guest_sessions").fetchone()[0], 1)

    def test_guest_can_use_word_count_and_voice_but_not_profile(self) -> None:
        self.client.post("/guest", data={"selected_language": "en"})
        chat = self.client.post(
            "/api/chat",
            json={"message": "word count: one two three", "selectedLanguage": "en"},
        )
        self.assertEqual(chat.get_json()["toolsUsed"], ["Word Count"])
        with patch("app.voice.routes.generate_speech_audio", return_value=b"audio"):
            voice = self.client.post(
                "/api/voice/speak",
                json={"text": "Hello", "preferredLanguage": "en"},
            )
        self.assertEqual(voice.status_code, 200)
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
        self.assertTrue(
            any("HttpOnly" in value and "SameSite=Lax" in value for value in cookie_headers)
        )


if __name__ == "__main__":
    unittest.main()
