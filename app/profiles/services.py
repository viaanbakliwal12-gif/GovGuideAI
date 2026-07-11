from __future__ import annotations

from app.auth.services import utc_now
from app.database.models import UserProfile
from app.database.session import get_connection


REQUIRED_FIELDS = (
    "full_name",
    "age",
    "state",
    "district",
    "occupation",
    "location_type",
    "preferred_language",
)

OPTIONAL_FIELDS = (
    "gender",
    "student_status",
    "farmer_status",
    "annual_household_income_range",
    "disability_status",
    "employment_status",
    "marital_status",
    "social_category",
)


def profile_from_form(form) -> dict[str, str | None]:
    data: dict[str, str | None] = {}
    for field in REQUIRED_FIELDS + OPTIONAL_FIELDS:
        value = str(form.get(field, "")).strip()
        data[field] = value or None
    return data


def validate_profile(data: dict[str, str | None]) -> str | None:
    for field in REQUIRED_FIELDS:
        if not data.get(field):
            return "Please complete all required profile fields."
    return None


def save_profile(user_id: int, data: dict[str, str | None]) -> None:
    values = {field: data.get(field) for field in REQUIRED_FIELDS + OPTIONAL_FIELDS}
    with get_connection() as db:
        existing = db.execute(
            "SELECT id FROM profiles WHERE user_id = ?",
            (user_id,),
        ).fetchone()

        if existing:
            db.execute(
                """
                UPDATE profiles SET
                    full_name = ?, age = ?, state = ?, district = ?,
                    occupation = ?, location_type = ?, preferred_language = ?,
                    gender = ?, student_status = ?, farmer_status = ?,
                    annual_household_income_range = ?, disability_status = ?,
                    employment_status = ?, marital_status = ?, social_category = ?,
                    updated_date = ?
                WHERE user_id = ?
                """,
                (
                    values["full_name"],
                    values["age"],
                    values["state"],
                    values["district"],
                    values["occupation"],
                    values["location_type"],
                    values["preferred_language"],
                    values["gender"],
                    values["student_status"],
                    values["farmer_status"],
                    values["annual_household_income_range"],
                    values["disability_status"],
                    values["employment_status"],
                    values["marital_status"],
                    values["social_category"],
                    utc_now(),
                    user_id,
                ),
            )
        else:
            db.execute(
                """
                INSERT INTO profiles (
                    user_id, full_name, age, state, district, occupation,
                    location_type, preferred_language, gender, student_status,
                    farmer_status, annual_household_income_range,
                    disability_status, employment_status, marital_status,
                    social_category, updated_date
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    user_id,
                    values["full_name"],
                    values["age"],
                    values["state"],
                    values["district"],
                    values["occupation"],
                    values["location_type"],
                    values["preferred_language"],
                    values["gender"],
                    values["student_status"],
                    values["farmer_status"],
                    values["annual_household_income_range"],
                    values["disability_status"],
                    values["employment_status"],
                    values["marital_status"],
                    values["social_category"],
                    utc_now(),
                ),
            )


def get_profile(user_id: int) -> UserProfile | None:
    with get_connection() as db:
        row = db.execute(
            "SELECT * FROM profiles WHERE user_id = ?",
            (user_id,),
        ).fetchone()

    if row is None:
        return None

    return UserProfile(
        user_id=row["user_id"],
        full_name=row["full_name"],
        age=row["age"],
        state=row["state"],
        district=row["district"],
        occupation=row["occupation"],
        location_type=row["location_type"],
        preferred_language=row["preferred_language"],
        gender=row["gender"],
        student_status=row["student_status"],
        farmer_status=row["farmer_status"],
        annual_household_income_range=row["annual_household_income_range"],
        disability_status=row["disability_status"],
        employment_status=row["employment_status"],
        marital_status=row["marital_status"],
        social_category=row["social_category"],
    )


def delete_profile(user_id: int) -> None:
    with get_connection() as db:
        db.execute("DELETE FROM profiles WHERE user_id = ?", (user_id,))
