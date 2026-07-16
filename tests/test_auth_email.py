from __future__ import annotations

import os
from pathlib import Path
import re
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

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

    def login(self, email: str):
        return self.client.post("/login", data={"email": email}, follow_redirects=False)

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


class EmailOnlyAuthenticationTests(AuthFlowTestCase):
    def test_login_page_has_one_email_form_and_no_provider_ui(self) -> None:
        response = self.client.get("/login")
        page = response.get_data(as_text=True)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(page.count('type="email"'), 1)
        self.assertIn('method="post"', page)
        self.assertIn('action="/login"', page)
        self.assertIn("Continue with Email", page)
        self.assertIn("Continue as Guest", page)
        self.assertNotIn('type="password"', page)
        self.assertNotIn('autocomplete="one-time-code"', page)
        self.assertNotIn("Send OTP", page)
        self.assertNotIn("Supabase", page)
        self.assertNotIn("auth.js", page)
        self.assertEqual(self.client.get("/signup").status_code, 302)

    def test_new_email_creates_passwordless_local_user_and_starts_session(self) -> None:
        with self.client.session_transaction() as browser_session:
            browser_session["language_selected"] = True
            browser_session["selected_language"] = "hi"

        response = self.login("Person@Example.com")

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers["Location"], "/profile/setup")
        with get_connection() as db:
            row = db.execute(
                """
                SELECT id, email, verified_email, password_hash,
                       last_login_date, last_login_at, supabase_user_id
                FROM users
                """
            ).fetchone()
        self.assertEqual(row["email"], "person@example.com")
        self.assertIsNone(row["verified_email"])
        self.assertIsNone(row["password_hash"])
        self.assertIsNone(row["supabase_user_id"])
        self.assertTrue(row["last_login_date"])
        self.assertTrue(row["last_login_at"])
        with self.client.session_transaction() as browser_session:
            self.assertEqual(browser_session["user_id"], row["id"])
            self.assertEqual(browser_session["selected_language"], "hi")
            self.assertTrue(browser_session["language_selected"])

    def test_existing_email_reuses_local_record_and_preserves_profile_and_legacy_fields(self) -> None:
        with get_connection() as db:
            db.execute(
                """
                INSERT INTO users (
                    email, password_hash, created_date, created_at,
                    verified_email, email_verified_at, supabase_user_id
                ) VALUES (
                    'person@example.com', 'legacy-hash', '2026-01-01',
                    '2026-01-01', 'person@example.com', '2026-01-01',
                    'legacy-provider-id'
                )
                """
            )
            user_id = db.execute("SELECT id FROM users").fetchone()[0]
        self.add_profile(user_id)

        response = self.login("PERSON@example.com")

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers["Location"], "/chat")
        with get_connection() as db:
            row = db.execute(
                """
                SELECT id, password_hash, supabase_user_id, last_login_at
                FROM users WHERE id = ?
                """,
                (user_id,),
            ).fetchone()
            profile_count = db.execute("SELECT COUNT(*) FROM profiles").fetchone()[0]
            user_count = db.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        self.assertEqual(row["id"], user_id)
        self.assertEqual(row["password_hash"], "legacy-hash")
        self.assertEqual(row["supabase_user_id"], "legacy-provider-id")
        self.assertTrue(row["last_login_at"])
        self.assertEqual(profile_count, 1)
        self.assertEqual(user_count, 1)

    def test_verified_email_only_record_is_reused(self) -> None:
        with get_connection() as db:
            db.execute(
                """
                INSERT INTO users (
                    email, password_hash, created_date, created_at,
                    verified_email, verified_phone
                ) VALUES (
                    NULL, NULL, '2026-01-01', '2026-01-01',
                    'legacy@example.com', '+14155552671'
                )
                """
            )
            user_id = db.execute("SELECT id FROM users").fetchone()[0]
        self.add_profile(user_id)

        response = self.login("legacy@example.com")

        self.assertEqual(response.headers["Location"], "/chat")
        with self.client.session_transaction() as browser_session:
            self.assertEqual(browser_session["user_id"], user_id)
        with get_connection() as db:
            self.assertEqual(db.execute("SELECT COUNT(*) FROM users").fetchone()[0], 1)

    def test_invalid_email_returns_form_error_without_creating_user(self) -> None:
        response = self.login("not-an-email")
        page = response.get_data(as_text=True)

        self.assertEqual(response.status_code, 400)
        self.assertIn("Enter a valid email address.", page)
        with get_connection() as db:
            self.assertEqual(db.execute("SELECT COUNT(*) FROM users").fetchone()[0], 0)
        with self.client.session_transaction() as browser_session:
            self.assertNotIn("user_id", browser_session)

    def test_old_provider_auth_endpoints_are_removed(self) -> None:
        self.assertEqual(self.client.get("/api/auth/config").status_code, 404)
        self.assertEqual(
            self.client.post("/api/auth/session", json={"access_token": "unused"}).status_code,
            404,
        )

    def test_logout_clears_server_session(self) -> None:
        self.login("person@example.com")
        response = self.client.post("/logout")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers["Location"], "/login")
        with self.client.session_transaction() as browser_session:
            self.assertNotIn("user_id", browser_session)

    def test_startup_logs_local_email_auth(self) -> None:
        with self.assertLogs("app.server", level="INFO") as captured:
            create_app()
        combined = "\n".join(captured.output)
        self.assertIn("Authentication: local email-only session", combined)
        self.assertNotIn("Supabase", combined)


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

    def test_external_next_url_is_not_rendered_or_used(self) -> None:
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
    def test_email_login_requires_csrf_outside_testing_mode(self) -> None:
        self.app.config["TESTING"] = False
        page = self.client.get("/login")
        match = re.search(
            r'name="_csrf_token" value="([^"]+)"',
            page.get_data(as_text=True),
        )
        self.assertIsNotNone(match)

        rejected = self.client.post("/login", data={"email": "person@example.com"})
        accepted = self.client.post(
            "/login",
            data={
                "email": "person@example.com",
                "_csrf_token": match.group(1),
            },
        )

        self.assertEqual(rejected.status_code, 400)
        self.assertEqual(accepted.status_code, 302)
        self.assertEqual(accepted.headers["Location"], "/profile/setup")


if __name__ == "__main__":
    unittest.main()
