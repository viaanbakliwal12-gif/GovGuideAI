from __future__ import annotations

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class FrontendContractTests(unittest.TestCase):
    def test_welcome_cover_uses_existing_brand_and_language_route(self) -> None:
        welcome = (ROOT / "templates" / "welcome.html").read_text(encoding="utf-8")

        self.assertIn('class="brand-mark"', welcome)
        self.assertIn("Welcome to GovGuideAI", welcome)
        self.assertIn("url_for('language_select')", welcome)
        self.assertNotIn("<script", welcome)

    def test_authentication_pages_use_complete_password_forms(self) -> None:
        login = (ROOT / "templates" / "login.html").read_text(encoding="utf-8")
        signup = (ROOT / "templates" / "signup.html").read_text(encoding="utf-8")
        guest = (ROOT / "templates" / "_guest_option.html").read_text(encoding="utf-8")
        script = (ROOT / "static" / "js" / "auth.js").read_text(encoding="utf-8")

        self.assertIn('autocomplete="current-password"', login)
        self.assertIn('name="confirm_password"', signup)
        self.assertIn('autocomplete="new-password"', signup)
        self.assertIn("Continue as Guest", guest)
        self.assertIn("data-confirm-password", script)
        self.assertIn("Passwords do not match", script)
        self.assertFalse((ROOT / "templates" / "verify_otp.html").exists())
        self.assertFalse((ROOT / "templates" / "_auth_methods.html").exists())

    def test_mobile_css_has_no_fixed_desktop_squeeze_contract(self) -> None:
        css = (ROOT / "static" / "css" / "styles.css").read_text(encoding="utf-8")
        required_rules = (
            "@media (max-width: 940px)",
            "@media (max-width: 720px)",
            "@media (max-width: 520px)",
            "100dvh",
            "env(safe-area-inset-bottom)",
            '.context-panel[data-open="true"]',
            "position: sticky",
            "grid-template-columns: minmax(0, 1fr) 44px",
            "overflow-x: hidden",
        )
        for rule in required_rules:
            self.assertIn(rule, css)

    def test_new_visible_strings_are_routed_through_i18n(self) -> None:
        translations = (ROOT / "static" / "js" / "i18n.js").read_text(encoding="utf-8")
        required_keys = (
            "continueAsGuest",
            "reducedPersonalization",
            "loginPasswordCopy",
            "signupPasswordCopy",
            "confirmPassword",
            "passwordHelp",
            "passwordMismatch",
            "createAccountToSave",
            "adminDashboard",
            "administratorSetup",
        )
        for key in required_keys:
            self.assertIn(f"{key}:", translations)

    def test_admin_website_setup_and_download_feedback_are_present(self) -> None:
        setup = (ROOT / "templates" / "admin" / "setup.html").read_text(encoding="utf-8")
        dashboard = (ROOT / "templates" / "admin" / "dashboard.html").read_text(encoding="utf-8")
        script = (ROOT / "static" / "js" / "admin.js").read_text(encoding="utf-8")

        self.assertIn("Make this account the administrator", setup)
        self.assertIn('name="confirmation"', setup)
        self.assertIn("Recent accounts", dashboard)
        self.assertIn("Create setup link", dashboard)
        self.assertIn("data-export-form", dashboard)
        self.assertIn("Preparing ${format} download", script)

        profile_setup = (ROOT / "templates" / "profile_setup.html").read_text(encoding="utf-8")
        self.assertIn("url_for('auth.logout')", profile_setup)

    def test_api_calls_send_csrf_tokens(self) -> None:
        for relative_path in (
            "static/js/chat.js",
            "static/js/voice.js",
            "static/js/i18n.js",
        ):
            source = (ROOT / relative_path).read_text(encoding="utf-8")
            self.assertIn("X-CSRF-Token", source)

    def test_language_form_has_a_server_backed_non_looping_fallback(self) -> None:
        template = (ROOT / "templates" / "language_select.html").read_text(encoding="utf-8")
        script = (ROOT / "static" / "js" / "i18n.js").read_text(encoding="utf-8")

        self.assertIn('method="post"', template)
        self.assertIn('name="selected_language"', template)
        self.assertIn('name="next"', template)
        self.assertIn("document.body.dataset.languageSelected", script)
        self.assertNotIn("event.preventDefault();\n      const language = getLanguage();", script)


if __name__ == "__main__":
    unittest.main()
