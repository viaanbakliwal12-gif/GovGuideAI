from __future__ import annotations

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class FrontendContractTests(unittest.TestCase):
    def test_authentication_states_share_one_responsive_component(self) -> None:
        partial = (ROOT / "templates" / "_auth_methods.html").read_text(encoding="utf-8")
        verification = (ROOT / "templates" / "verify_otp.html").read_text(encoding="utf-8")
        script = (ROOT / "static" / "js" / "auth.js").read_text(encoding="utf-8")

        self.assertIn('data-auth-tab="email"', partial)
        self.assertIn('data-auth-tab="phone"', partial)
        self.assertIn('data-auth-panel="email"', partial)
        self.assertIn('data-auth-panel="phone"', partial)
        self.assertIn("Continue as Guest", partial)
        self.assertIn("autocomplete=\"one-time-code\"", verification)
        self.assertIn("data-resend-form", verification)
        self.assertIn("replace(/\\D/g", script)
        self.assertIn("clipboardData", script)

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
            "continueWithEmail",
            "continueWithPhone",
            "country",
            "phoneNumber",
            "sendCode",
            "enterVerificationCode",
            "verify",
            "resendCode",
            "codeExpired",
            "incorrectOrExpiredCode",
            "changeEmail",
            "changePhoneNumber",
            "createAccountToSave",
        )
        for key in required_keys:
            self.assertIn(f"{key}:", translations)

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
