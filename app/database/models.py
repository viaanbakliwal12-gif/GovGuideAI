from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class User:
    id: int
    email: str
    created_date: str
    last_login_date: str | None


@dataclass(frozen=True)
class UserProfile:
    user_id: int
    full_name: str
    age: str
    state: str
    district: str
    occupation: str
    location_type: str
    preferred_language: str
    gender: str | None = None
    student_status: str | None = None
    farmer_status: str | None = None
    annual_household_income_range: str | None = None
    disability_status: str | None = None
    employment_status: str | None = None
    marital_status: str | None = None
    social_category: str | None = None

    def to_agent_context(self) -> dict[str, str]:
        """Return only useful, non-empty profile values for the assistant."""

        values = {
            "full_name": self.full_name,
            "age": self.age,
            "state": self.state,
            "district": self.district,
            "occupation": self.occupation,
            "location_type": self.location_type,
            "preferred_language": self.preferred_language,
            "gender": self.gender,
            "student_status": self.student_status,
            "farmer_status": self.farmer_status,
            "annual_household_income_range": self.annual_household_income_range,
            "disability_status": self.disability_status,
            "employment_status": self.employment_status,
            "marital_status": self.marital_status,
            "social_category": self.social_category,
        }
        return {key: value for key, value in values.items() if value}
