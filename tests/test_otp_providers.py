from __future__ import annotations

import json
import os
import unittest
from unittest.mock import patch
from urllib.error import HTTPError, URLError

from app.auth.supabase import (
    SupabaseAuthenticationError,
    SupabaseConfigurationError,
    SupabaseNetworkError,
    public_supabase_config,
    verify_supabase_access_token,
)


class _Response:
    def __init__(self, payload: dict):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def read(self) -> bytes:
        return json.dumps(self.payload).encode("utf-8")


class SupabaseAuthProviderTests(unittest.TestCase):
    settings = {
        "SUPABASE_URL": "https://project-ref.supabase.co",
        "SUPABASE_ANON_KEY": "test-public-anon-key",
    }

    def test_public_config_returns_only_configured_browser_values(self) -> None:
        with patch.dict(os.environ, self.settings, clear=False):
            self.assertEqual(
                public_supabase_config(),
                (self.settings["SUPABASE_URL"], self.settings["SUPABASE_ANON_KEY"]),
            )

    def test_missing_or_secret_configuration_is_rejected(self) -> None:
        with patch.dict(
            os.environ,
            {"SUPABASE_URL": "", "SUPABASE_ANON_KEY": ""},
            clear=False,
        ):
            with self.assertRaises(SupabaseConfigurationError):
                public_supabase_config()
        with patch.dict(
            os.environ,
            {
                "SUPABASE_URL": self.settings["SUPABASE_URL"],
                "SUPABASE_ANON_KEY": "sb_secret_must_not_be_public",
            },
            clear=False,
        ):
            with self.assertRaises(SupabaseConfigurationError):
                public_supabase_config()

    def test_access_token_is_validated_by_supabase_auth(self) -> None:
        response = _Response(
            {
                "id": "9ce31cba-7890-4e42-b3bc-bf7e5f932659",
                "email": "Person@Example.com",
                "created_at": "2026-07-16T12:00:00Z",
                "email_confirmed_at": "2026-07-16T12:01:00Z",
            }
        )
        with patch.dict(os.environ, self.settings, clear=False):
            with patch("app.auth.supabase.urlopen", return_value=response) as mocked:
                identity = verify_supabase_access_token("signed-access-token")

        request = mocked.call_args.args[0]
        self.assertEqual(request.full_url, "https://project-ref.supabase.co/auth/v1/user")
        self.assertEqual(request.headers["Authorization"], "Bearer signed-access-token")
        self.assertEqual(request.headers["Apikey"], "test-public-anon-key")
        self.assertEqual(identity.email, "person@example.com")

    def test_invalid_token_and_network_failure_are_distinct(self) -> None:
        unauthorized = HTTPError("https://example.test", 401, "Unauthorized", None, None)
        with patch.dict(os.environ, self.settings, clear=False):
            with patch("app.auth.supabase.urlopen", side_effect=unauthorized):
                with self.assertRaises(SupabaseAuthenticationError):
                    verify_supabase_access_token("invalid-token")
            with patch("app.auth.supabase.urlopen", side_effect=URLError("offline")):
                with self.assertRaises(SupabaseNetworkError):
                    verify_supabase_access_token("otherwise-valid-token")


if __name__ == "__main__":
    unittest.main()
