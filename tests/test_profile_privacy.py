from __future__ import annotations

import unittest

from app.database.models import UserProfile


class ProfileContextPrivacyTests(unittest.TestCase):
    def setUp(self) -> None:
        self.profile = UserProfile(
            user_id=7,
            full_name="Private Person",
            age="34",
            state="Maharashtra",
            district="Pune",
            occupation="farmer",
            occupation_custom=None,
            location_type="Rural",
            preferred_language="hi",
            gender="Female",
            annual_household_income_range="₹2–5 lakh",
            disability_status="None",
            marital_status="Married",
            social_category="General",
        )

    def test_unrelated_request_does_not_send_the_full_profile(self) -> None:
        context = self.profile.to_agent_context(
            "What documents are needed for a new passport application?"
        )
        self.assertEqual(context, {})

    def test_scheme_request_uses_current_user_eligibility_fields_but_no_identity(self) -> None:
        context = self.profile.to_agent_context("Which government schemes are suitable for me?")
        self.assertEqual(context["state"], "Maharashtra")
        self.assertEqual(context["occupation"], "farmer")
        self.assertNotIn("full_name", context)
        self.assertNotIn("preferred_language", context)
        self.assertNotIn("email", context)
        self.assertNotIn("phone", context)
        self.assertNotIn("user_id", context)


if __name__ == "__main__":
    unittest.main()
