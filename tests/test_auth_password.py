from __future__ import annotations

import os
from pathlib import Path
import re
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from app.auth.supabase import (
    SupabaseAuthenticationError,
    SupabaseIdentity,
    SupabaseNetworkError,
)
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
                "SUPABASE_URL": "https://project-ref.supabase.co",
                "SUPABASE_ANON_KEY": "test-public-anon-key",
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

    @staticmethod
    def identity(
        email: str = "person@example.com",
        user_id: str = "9ce31cba-7890-4e42-b3bc-bf7e5f932659",
    ) -> SupabaseIdentity:
        return SupabaseIdentity(
            user_id=user_id,
            email=email,
            created_at="2026-07-16T12:00:00+00:00",
            email_confirmed_at="2026-07-16T12:01:00+00:00",
        )

    def create_session(self, identity: SupabaseIdentity | None = None, **payload):
        with patch(
            "app.auth.routes.verify_supabase_access_token",
            return_value=identity or self.identity(),
        ):
            return self.client.post(
                "/api/auth/session",
                json={"access_token": "verified-access-token", **payload},
            )

    def add_profile(self, user_id: int) -> None:
        with get_connection() as db:
            db.execute(
                """
                INSERT INTO profiles (
                    user_id, full_name, age, state, district, occupation,
                    location_type, preferred_language, updated_date
                ) VALUES (?, 'Complete User', '30', 'Delhi', 'New Delhi',
                          'employed', 'urban', 'en', '2026-07-16')
                """,
                (user_id,),
            )


class SupabaseAuthenticationTests(AuthFlowTestCase):
    def test_login_page_is_email_otp_ui_and_signup_routes_to_it(self) -> None:
        response = self.client.get("/login")
        page = response.get_data(as_text=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn('type="email"', page)
        self.assertIn("Send OTP", page)
        self.assertIn('autocomplete="one-time-code"', page)
        self.assertIn('maxlength="6"', page)
        self.assertIn("Verify OTP", page)
        self.assertIn("Change Email", page)
        self.assertIn("Resend Code", page)
        self.assertIn("@supabase/supabase-js@2", page)
        self.assertEqual(self.client.get("/signup").status_code, 302)
        self.assertEqual(self.client.post("/login").status_code, 405)

    def test_public_config_exposes_exactly_two_public_fields(self) -> None:
        response = self.client.get("/api/auth/config")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.get_json(),
            {
                "SUPABASE_URL": "https://project-ref.supabase.co",
                "SUPABASE_ANON_KEY": "test-public-anon-key",
            },
        )
        self.assertIn("no-store", response.headers["Cache-Control"])

    def test_missing_config_is_safe_and_does_not_expose_other_environment(self) -> None:
        with patch.dict(
            os.environ,
            {"SUPABASE_URL": "", "SUPABASE_ANON_KEY": ""},
            clear=False,
        ):
            response = self.client.get("/api/auth/config")
        self.assertEqual(response.status_code, 503)
        self.assertEqual(
            response.get_json(),
            {"SUPABASE_URL": "", "SUPABASE_ANON_KEY": ""},
        )
        self.assertNotIn("SECRET_KEY", response.get_data(as_text=True))

    def test_verified_supabase_identity_creates_local_profile_account(self) -> None:
        response = self.create_session(selected_language="hi")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["next"], "/profile/setup")
        with get_connection() as db:
            row = db.execute(
                "SELECT id, email, verified_email, password_hash, supabase_user_id FROM users"
            ).fetchone()
        self.assertEqual(row["email"], "person@example.com")
        self.assertEqual(row["verified_email"], "person@example.com")
        self.assertIsNone(row["password_hash"])
        self.assertEqual(row["supabase_user_id"], self.identity().user_id)
        with self.client.session_transaction() as browser_session:
            self.assertEqual(browser_session["user_id"], row["id"])
            self.assertEqual(browser_session["selected_language"], "hi")

    def test_existing_email_is_safely_linked_and_profile_is_preserved(self) -> None:
        with get_connection() as db:
            db.execute(
                """
                INSERT INTO users (email, password_hash, created_date, created_at)
                VALUES ('person@example.com', 'legacy-hash', '2026-01-01', '2026-01-01')
                """
            )
            user_id = db.execute("SELECT id FROM users").fetchone()[0]
        self.add_profile(user_id)

        response = self.create_session(next="/profile")

        self.assertEqual(response.get_json()["next"], "/profile")
        with get_connection() as db:
            row = db.execute(
                "SELECT supabase_user_id, password_hash FROM users WHERE id = ?",
                (user_id,),
            ).fetchone()
            profile_count = db.execute("SELECT COUNT(*) FROM profiles").fetchone()[0]
        self.assertEqual(row["supabase_user_id"], self.identity().user_id)
        self.assertEqual(row["password_hash"], "legacy-hash")
        self.assertEqual(profile_count, 1)

    def test_invalid_token_and_supabase_network_failure_are_clear(self) -> None:
        with patch(
            "app.auth.routes.verify_supabase_access_token",
            side_effect=SupabaseAuthenticationError("The session is invalid or expired."),
        ):
            invalid = self.client.post(
                "/api/auth/session", json={"access_token": "invalid"}
            )
        with patch(
            "app.auth.routes.verify_supabase_access_token",
            side_effect=SupabaseNetworkError("Check the network and try again."),
        ):
            offline = self.client.post(
                "/api/auth/session", json={"access_token": "valid-but-offline"}
            )
        self.assertEqual(invalid.status_code, 401)
        self.assertIn("expired", invalid.get_json()["error"])
        self.assertEqual(offline.status_code, 502)
        self.assertIn("network", offline.get_json()["error"])

    def test_logout_clears_server_session(self) -> None:
        self.create_session()
        response = self.client.post("/logout")
        self.assertEqual(response.status_code, 302)
        self.assertIn("/login", response.headers["Location"])
        with self.client.session_transaction() as browser_session:
            self.assertNotIn("user_id", browser_session)

    def test_startup_logs_supabase_otp_auth(self) -> None:
        with self.assertLogs("app.server", level="INFO") as captured:
            create_app()
        combined = "\n".join(captured.output)
        self.assertIn("Authentication: Supabase email OTP", combined)
        self.assertNotIn("Development OTP", combined)


class WelcomeAndAccessTests(AuthFlowTestCase):
    def test_root_shows_welcome_cover_before_language_selection(self) -> None:
        response = self.client.get("/")
        page = response.get_data(as_text=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn("Welcome to GovGuideAI", page)
        self.assertIn('href="/language"', page)

    def test_protected_routes_redirect_to_login_with_safe_return_path(self) -> None:
        profile = self.client.get("/profile", follow_redirects=False)
        chat = self.client.get("/chat", follow_redirects=False)
        self.assertEqual(profile.status_code, 302)
        self.assertEqual(profile.headers["Location"], "/login?next=/profile")
        self.assertEqual(chat.headers["Location"], "/login?next=/chat")

    def test_external_next_url_is_not_used(self) -> None:
        response = self.client.get("/login?next=//example.com/escape")
        self.assertNotIn("//example.com/escape", response.get_data(as_text=True))


class LanguageSelectionTests(AuthFlowTestCase):
    def test_language_selection_is_saved_server_side(self) -> None:
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
    def test_guest_reaches_chat_without_creating_user(self) -> None:
        response = self.client.post(
            "/guest", data={"selected_language": "en"}, follow_redirects=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("Guest mode", response.get_data(as_text=True))
        with get_connection() as db:
            self.assertEqual(db.execute("SELECT COUNT(*) FROM users").fetchone()[0], 0)

    def test_guest_cannot_open_profile(self) -> None:
        self.client.post("/guest", data={"selected_language": "en"})
        self.assertIn("/login", self.client.get("/profile").headers["Location"])


class SecurityBoundaryTests(AuthFlowTestCase):
    def test_session_exchange_requires_csrf_outside_testing_mode(self) -> None:
        self.app.config["TESTING"] = False
        page = self.client.get("/login")
        match = re.search(r'<meta name="csrf-token" content="([^"]+)"', page.get_data(as_text=True))
        self.assertIsNotNone(match)
        with patch(
            "app.auth.routes.verify_supabase_access_token",
            return_value=self.identity(),
        ):
            rejected = self.client.post(
                "/api/auth/session", json={"access_token": "verified-access-token"}
            )
            accepted = self.client.post(
                "/api/auth/session",
                json={"access_token": "verified-access-token"},
                headers={"X-CSRF-Token": match.group(1)},
            )
        self.assertEqual(rejected.status_code, 400)
        self.assertEqual(accepted.status_code, 200)


if __name__ == "__main__":
    unittest.main()
