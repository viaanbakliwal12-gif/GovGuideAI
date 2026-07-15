from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class User:
    id: int
    email: str | None
    created_date: str
    last_login_date: str | None
    verified_email: str | None = None
    verified_phone: str | None = None
    email_verified_at: str | None = None
    phone_verified_at: str | None = None
    is_admin: bool = False
    deleted_at: str | None = None

    @property
    def display_identifier(self) -> str:
        return self.email or self.verified_email or self.verified_phone or "GovGuideAI user"


@dataclass(frozen=True)
class OTPChallenge:
    id: int
    public_id: str
    destination_hash: str
    destination_encrypted: str
    channel: str
    purpose: str
    otp_hash: str
    expires_at: str
    attempts: int
    resend_count: int
    used_at: str | None
    created_at: str
    last_sent_at: str
    requested_ip_hash: str
    delivery_method: str = "local"
    provider_reference: str | None = None


@dataclass(frozen=True)
class GuestSession:
    id: int
    session_hash: str
    created_at: str
    last_seen_at: str
    expires_at: str


@dataclass(frozen=True)
class UserProfile:
    user_id: int
    full_name: str
    age: str
    state: str
    district: str
    occupation: str
    occupation_custom: str | None
    location_type: str
    preferred_language: str
    gender: str | None = None
    annual_household_income_range: str | None = None
    disability_status: str | None = None
    marital_status: str | None = None
    social_category: str | None = None

    def to_agent_context(self, user_message: str = "") -> dict[str, str]:
        """Return only current-user fields relevant to this specific request."""

        values = {
            "age": self.age,
            "state": self.state,
            "district": self.district,
            "occupation": self.occupation,
            "occupation_custom": self.occupation_custom,
            "location_type": self.location_type,
            "gender": self.gender,
            "annual_household_income_range": self.annual_household_income_range,
            "disability_status": self.disability_status,
            "marital_status": self.marital_status,
            "social_category": self.social_category,
        }
        text = str(user_message or "").casefold()
        broad_eligibility = any(
            term in text
            for term in (
                "scheme",
                "yojana",
                "benefit",
                "eligible",
                "eligibility",
                "support for me",
                "for my profile",
                "recommend",
                "scholarship",
                "pension",
                "subsidy",
            )
        )
        field_terms = {
            "age": ("age", "birth", "senior", "pension", "student", "scholarship"),
            "state": ("state", "district", "local", "near me", "rural", "urban"),
            "district": ("district", "local", "near me"),
            "occupation": (
                "occupation",
                "job",
                "work",
                "student",
                "farmer",
                "business",
                "employ",
                "retired",
            ),
            "occupation_custom": ("occupation", "job", "work", "business"),
            "location_type": ("rural", "urban", "village", "city", "location"),
            "gender": ("gender", "woman", "women", "girl", "female", "widow"),
            "annual_household_income_range": ("income", "economic", "ews", "bpl"),
            "disability_status": ("disability", "disabled", "divyang"),
            "marital_status": ("marital", "married", "widow", "spouse"),
            "social_category": ("category", "caste", "sc ", "st ", "obc", "minority"),
        }
        relevant: dict[str, str] = {}
        for key, value in values.items():
            if not value:
                continue
            if broad_eligibility or any(term in text for term in field_terms[key]):
                relevant[key] = value
        return relevant
