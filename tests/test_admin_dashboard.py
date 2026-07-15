from __future__ import annotations

import csv
from io import StringIO
import json
import os
from pathlib import Path
import re
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from werkzeug.security import generate_password_hash

from app.admin.services import AdminPromotionError, promote_verified_admin
from app.database.session import get_connection
from app.server import create_app


class AdminDashboardTests(unittest.TestCase):
    def setUp(self) -> None:
        self.directory = TemporaryDirectory(ignore_cleanup_errors=True)
        self.database_path = Path(self.directory.name) / "admin-test.sqlite3"
        self.database_patch = patch("app.database.session.DATABASE_PATH", self.database_path)
        self.database_patch.start()
        self.environment_patch = patch.dict(
            os.environ,
            {
                "SECRET_KEY": "admin-test-secret",
                "OTP_DEVELOPMENT_MODE": "false",
                "FLASK_ENV": "development",
                "APP_ENV": "development",
                "EMAIL_PROVIDER": "",
                "SMS_PROVIDER": "",
                "ADMIN_EMAIL": "normal@example.com",
            },
            clear=False,
        )
        self.environment_patch.start()
        self.app = create_app()
        self.app.config.update(TESTING=True, SECRET_KEY="admin-test-secret")
        self.client = self.app.test_client()
        self._seed_users()

    def tearDown(self) -> None:
        self.environment_patch.stop()
        self.database_patch.stop()
        self.directory.cleanup()

    def _seed_users(self) -> None:
        with get_connection() as db:
            db.execute(
                """
                INSERT INTO users (
                    id, email, password_hash, created_date, last_login_date,
                    verified_email, email_verified_at, created_at, last_login_at,
                    is_admin
                ) VALUES (1, ?, ?, ?, ?, ?, ?, ?, ?, 1)
                """,
                (
                    "admin@example.com",
                    generate_password_hash("admin-password"),
                    "2026-01-01T00:00:00+00:00",
                    "2026-07-01T00:00:00+00:00",
                    "admin@example.com",
                    "2026-01-01T00:00:00+00:00",
                    "2026-01-01T00:00:00+00:00",
                    "2026-07-01T00:00:00+00:00",
                ),
            )
            db.execute(
                """
                INSERT INTO users (
                    id, email, password_hash, created_date, last_login_date,
                    verified_email, verified_phone, email_verified_at,
                    phone_verified_at, created_at, last_login_at, is_admin
                ) VALUES (2, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0)
                """,
                (
                    "normal@example.com",
                    generate_password_hash("normal-password"),
                    "2026-02-01T00:00:00+00:00",
                    "2026-07-02T00:00:00+00:00",
                    "normal@example.com",
                    "+919876543210",
                    "2026-02-01T00:00:00+00:00",
                    "2026-02-01T00:00:00+00:00",
                    "2026-02-01T00:00:00+00:00",
                    "2026-07-02T00:00:00+00:00",
                ),
            )
            db.execute(
                """
                INSERT INTO profiles (
                    user_id, full_name, age, state, district, occupation,
                    occupation_custom, location_type, preferred_language,
                    gender, annual_household_income_range, disability_status,
                    marital_status, social_category, updated_date
                ) VALUES (2, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    "आशा देवी",
                    "34",
                    "Maharashtra",
                    "Pune",
                    "other",
                    "हस्तकला",
                    "Urban",
                    "hi",
                    "Female",
                    "₹2–5 lakh",
                    "None",
                    "Married",
                    "General",
                    "2026-07-03T00:00:00+00:00",
                ),
            )
            db.execute(
                """
                INSERT INTO users (
                    id, email, password_hash, created_date, verified_email,
                    email_verified_at, created_at, deleted_at
                ) VALUES (3, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    "deleted@example.com",
                    generate_password_hash("deleted-password"),
                    "2026-03-01T00:00:00+00:00",
                    "deleted@example.com",
                    "2026-03-01T00:00:00+00:00",
                    "2026-03-01T00:00:00+00:00",
                    "2026-07-04T00:00:00+00:00",
                ),
            )

    def _login_as(self, user_id: int) -> None:
        with self.client.session_transaction() as browser_session:
            browser_session.clear()
            browser_session["user_id"] = user_id

    def test_admin_route_is_server_protected_for_guests_and_normal_users(self) -> None:
        self.assertEqual(self.client.get("/admin").status_code, 403)
        self.client.post("/guest", data={"selected_language": "en"})
        self.assertEqual(self.client.get("/admin").status_code, 403)
        self._login_as(2)
        self.assertEqual(self.client.get("/admin").status_code, 403)
        self.assertEqual(self.client.post("/admin/export/csv").status_code, 403)

    def test_admin_dashboard_lists_active_records_and_supports_search(self) -> None:
        self._login_as(1)
        response = self.client.get("/admin?q=आशा&sort=full_name&direction=desc&per_page=10")
        page = response.get_data(as_text=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn("आशा देवी", page)
        self.assertIn("n***@example.com", page)
        self.assertIn("+91********10", page)
        self.assertNotIn("deleted@example.com", page)
        self.assertNotIn("password_hash", page)
        self.assertNotIn("otp_hash", page)
        self.assertEqual(response.headers["Cache-Control"], "no-store, private")

    def test_csv_and_json_exports_are_unicode_safe_private_and_audited(self) -> None:
        self._login_as(1)
        csv_response = self.client.post("/admin/export/csv")
        json_response = self.client.post("/admin/export/json")

        self.assertEqual(csv_response.status_code, 200)
        self.assertIn("attachment", csv_response.headers["Content-Disposition"])
        self.assertIn("user_export_", csv_response.headers["Content-Disposition"])
        csv_rows = list(csv.DictReader(StringIO(csv_response.data.decode("utf-8-sig"))))
        self.assertEqual(len(csv_rows), 2)
        unicode_row = next(row for row in csv_rows if row["user_id"] == "2")
        self.assertEqual(unicode_row["full_name"], "आशा देवी")
        self.assertEqual(unicode_row["custom_occupation"], "हस्तकला")
        self.assertNotIn("password_hash", unicode_row)
        self.assertNotIn("otp_hash", unicode_row)
        self.assertNotIn("is_admin", unicode_row)
        self.assertTrue(unicode_row["exported_at"].endswith("+00:00"))

        self.assertEqual(json_response.status_code, 200)
        payload = json.loads(json_response.data.decode("utf-8"))
        self.assertEqual(payload["record_count"], 2)
        self.assertEqual([record["user_id"] for record in payload["records"]], [1, 2])
        self.assertIn("आशा देवी".encode("utf-8"), json_response.data)
        serialized = json_response.get_data(as_text=True)
        for forbidden in (
            "password_hash",
            "otp_hash",
            "attempts",
            "session_hash",
            "provider_reference",
            "is_admin",
        ):
            self.assertNotIn(forbidden, serialized)

        with get_connection() as db:
            audits = db.execute(
                "SELECT admin_user_id, file_format, record_count FROM export_audit_log ORDER BY id"
            ).fetchall()
        self.assertEqual(
            [tuple(row) for row in audits],
            [(1, "csv", 2), (1, "json", 2)],
        )
        self.assertFalse(list(Path(self.directory.name).glob("user_export_*")))

    def test_profile_edit_cannot_self_promote_and_cli_service_is_guarded(self) -> None:
        self._login_as(2)
        response = self.client.post(
            "/profile",
            data={
                "full_name": "आशा देवी",
                "age": "34",
                "state": "Maharashtra",
                "district": "Pune",
                "occupation": "other",
                "occupation_custom": "हस्तकला",
                "location_type": "Urban",
                "preferred_language": "hi",
                "is_admin": "1",
            },
        )
        self.assertEqual(response.status_code, 302)
        with get_connection() as db:
            self.assertEqual(db.execute("SELECT is_admin FROM users WHERE id = 2").fetchone()[0], 0)

        user_id, changed = promote_verified_admin("normal@example.com")
        self.assertEqual((user_id, changed), (2, True))
        with get_connection() as db:
            self.assertEqual(db.execute("SELECT is_admin FROM users WHERE id = 2").fetchone()[0], 1)
        with self.assertRaises(AdminPromotionError):
            promote_verified_admin("admin@example.com")

    def test_admin_export_requires_csrf_outside_testing(self) -> None:
        self.app.config["TESTING"] = False
        self._login_as(1)
        page = self.client.get("/admin")
        match = re.search(r'name="_csrf_token" value="([^"]+)"', page.get_data(as_text=True))
        self.assertIsNotNone(match)
        self.assertEqual(self.client.post("/admin/export/csv").status_code, 400)
        accepted = self.client.post(
            "/admin/export/csv",
            data={"_csrf_token": match.group(1)},
        )
        self.assertEqual(accepted.status_code, 200)


if __name__ == "__main__":
    unittest.main()
