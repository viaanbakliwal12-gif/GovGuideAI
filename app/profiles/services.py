from __future__ import annotations

from app.auth.services import utc_now
from app.database.models import UserProfile
from app.database.session import get_connection


SUPPORTED_LANGUAGES = {
    "en": "English",
    "hi": "हिन्दी",
    "mr": "मराठी",
    "bn": "বাংলা",
    "ta": "தமிழ்",
    "te": "తెలుగు",
    "gu": "ગુજરાતી",
    "kn": "ಕನ್ನಡ",
    "ml": "മലയാളം",
    "pa": "ਪੰਜਾਬੀ",
    "ur": "اردو",
}

OCCUPATION_VALUES = {
    "student",
    "farmer",
    "employed",
    "self_employed",
    "business_owner",
    "unemployed",
    "retired",
    "homemaker",
    "other",
}

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
    "occupation_custom",
    "gender",
    "annual_household_income_range",
    "disability_status",
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

    if data.get("occupation") not in OCCUPATION_VALUES:
        return "Please choose a valid occupation."

    if normalize_language(data.get("preferred_language")) != data.get("preferred_language"):
        return "Please choose a supported language."

    return None


def save_profile(user_id: int, data: dict[str, str | None]) -> None:
    values = {field: data.get(field) for field in REQUIRED_FIELDS + OPTIONAL_FIELDS}
    values["preferred_language"] = normalize_language(values.get("preferred_language"))
    if values["occupation"] != "other":
        values["occupation_custom"] = None

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
                    occupation_custom = ?, gender = ?,
                    annual_household_income_range = ?, disability_status = ?,
                    marital_status = ?, social_category = ?,
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
                    values["occupation_custom"],
                    values["gender"],
                    values["annual_household_income_range"],
                    values["disability_status"],
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
                    location_type, preferred_language, occupation_custom, gender,
                    annual_household_income_range, disability_status,
                    marital_status, social_category, updated_date
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                    values["occupation_custom"],
                    values["gender"],
                    values["annual_household_income_range"],
                    values["disability_status"],
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
        occupation_custom=row["occupation_custom"],
        location_type=row["location_type"],
        preferred_language=normalize_language(row["preferred_language"]),
        gender=row["gender"],
        annual_household_income_range=row["annual_household_income_range"],
        disability_status=row["disability_status"],
        marital_status=row["marital_status"],
        social_category=row["social_category"],
    )


def delete_profile(user_id: int) -> None:
    with get_connection() as db:
        db.execute("DELETE FROM profiles WHERE user_id = ?", (user_id,))


def normalize_language(language: str | None) -> str:
    if not language:
        return "en"

    value = str(language).strip()
    if value in SUPPORTED_LANGUAGES:
        return value

    lower_value = value.lower()
    name_to_code = {name.lower(): code for code, name in SUPPORTED_LANGUAGES.items()}
    return name_to_code.get(lower_value, "en")


def update_profile_language(user_id: int, language: str | None) -> str:
    language_code = normalize_language(language)
    with get_connection() as db:
        db.execute(
            """
            UPDATE profiles
            SET preferred_language = ?, updated_date = ?
            WHERE user_id = ?
            """,
            (language_code, utc_now(), user_id),
        )
    return language_code
