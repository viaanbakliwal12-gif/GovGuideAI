from __future__ import annotations

from dataclasses import dataclass
from functools import wraps
import math
import os

from flask import abort

from app.auth.services import current_user, utc_now
from app.auth.validators import IdentifierValidationError, mask_destination, normalize_email
from app.config import is_development_environment
from app.database.models import User
from app.database.session import get_connection


ACCOUNT_TYPE_SQL = """
CASE
    WHEN u.supabase_user_id IS NOT NULL AND TRIM(u.supabase_user_id) <> '' THEN 'Supabase email OTP'
    WHEN u.password_hash IS NOT NULL AND TRIM(u.password_hash) <> '' THEN 'email + password'
    WHEN COALESCE(u.email, u.verified_email) IS NOT NULL THEN 'password setup needed'
    WHEN u.verified_phone IS NOT NULL THEN 'legacy phone account'
    ELSE 'legacy account'
END
"""

PROFILE_SELECT_SQL = f"""
SELECT
    u.id AS user_id,
    {ACCOUNT_TYPE_SQL} AS account_type,
    COALESCE(u.email, u.verified_email) AS email,
    u.verified_phone AS phone,
    CASE WHEN u.password_hash IS NULL OR TRIM(u.password_hash) = '' THEN 0 ELSE 1 END AS has_password,
    p.full_name,
    p.age,
    p.state,
    p.district,
    p.occupation,
    p.occupation_custom AS custom_occupation,
    p.location_type,
    p.preferred_language,
    p.gender,
    p.annual_household_income_range AS income_range,
    p.disability_status,
    p.marital_status,
    p.social_category,
    CASE WHEN p.user_id IS NULL THEN 0 ELSE 1 END AS profile_completed,
    COALESCE(u.created_at, u.created_date) AS created_at,
    COALESCE(u.last_login_at, u.last_login_date) AS last_login_at,
    p.updated_date AS updated_at
FROM users u
LEFT JOIN profiles p ON p.user_id = u.id
"""

SORT_COLUMNS = {
    "user_id": "u.id",
    "account_type": ACCOUNT_TYPE_SQL,
    "email": "COALESCE(u.email, u.verified_email)",
    "phone": "u.verified_phone",
    "full_name": "p.full_name",
    "age": "p.age",
    "state": "p.state",
    "district": "p.district",
    "occupation": "p.occupation",
    "custom_occupation": "p.occupation_custom",
    "location_type": "p.location_type",
    "preferred_language": "p.preferred_language",
    "gender": "p.gender",
    "income_range": "p.annual_household_income_range",
    "disability_status": "p.disability_status",
    "marital_status": "p.marital_status",
    "social_category": "p.social_category",
    "profile_completed": "CASE WHEN p.user_id IS NULL THEN 0 ELSE 1 END",
    "created_at": "COALESCE(u.created_at, u.created_date)",
    "last_login_at": "COALESCE(u.last_login_at, u.last_login_date)",
    "updated_at": "p.updated_date",
}

SEARCH_SQL = """
AND (
    CAST(u.id AS TEXT) LIKE ?
    OR LOWER(COALESCE(u.email, u.verified_email, '')) LIKE ?
    OR COALESCE(u.verified_phone, '') LIKE ?
    OR LOWER(COALESCE(p.full_name, '')) LIKE ?
    OR LOWER(COALESCE(p.age, '')) LIKE ?
    OR LOWER(COALESCE(p.state, '')) LIKE ?
    OR LOWER(COALESCE(p.district, '')) LIKE ?
    OR LOWER(COALESCE(p.occupation, '')) LIKE ?
    OR LOWER(COALESCE(p.occupation_custom, '')) LIKE ?
    OR LOWER(COALESCE(p.location_type, '')) LIKE ?
    OR LOWER(COALESCE(p.preferred_language, '')) LIKE ?
)
"""


@dataclass(frozen=True)
class ProfilePage:
    records: list[dict]
    page: int
    per_page: int
    total_records: int
    total_pages: int
    query: str
    sort: str
    direction: str


@dataclass(frozen=True)
class AdminDashboardSummary:
    total_users: int
    completed_profiles: int
    active_guests: int
    recent_accounts: list[dict]


class AdminPromotionError(RuntimeError):
    pass


class AdminSetupError(RuntimeError):
    pass


FIRST_ADMIN_CONFIRMATION = "MAKE ME ADMIN"


def admin_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        user = current_user()
        if user is None or not user.is_admin:
            abort(403)
        return view(*args, **kwargs)

    return wrapped_view


def fetch_profile_page(
    *,
    query: str = "",
    sort: str = "user_id",
    direction: str = "asc",
    page: int = 1,
    per_page: int = 25,
) -> ProfilePage:
    clean_query = str(query or "").strip()[:200]
    clean_sort = sort if sort in SORT_COLUMNS else "user_id"
    clean_direction = "desc" if str(direction).lower() == "desc" else "asc"
    clean_per_page = per_page if per_page in {10, 25, 50, 100} else 25
    clean_page = max(1, int(page or 1))

    where_sql, parameters = _where_clause(clean_query)
    with get_connection() as db:
        total_records = int(
            db.execute(
                f"SELECT COUNT(*) FROM users u LEFT JOIN profiles p ON p.user_id = u.id {where_sql}",
                parameters,
            ).fetchone()[0]
        )
        total_pages = max(1, math.ceil(total_records / clean_per_page))
        clean_page = min(clean_page, total_pages)
        offset = (clean_page - 1) * clean_per_page
        rows = db.execute(
            f"""
            {PROFILE_SELECT_SQL}
            {where_sql}
            ORDER BY {SORT_COLUMNS[clean_sort]} {clean_direction.upper()}, u.id ASC
            LIMIT ? OFFSET ?
            """,
            (*parameters, clean_per_page, offset),
        ).fetchall()

    records = [_display_record(dict(row)) for row in rows]
    return ProfilePage(
        records=records,
        page=clean_page,
        per_page=clean_per_page,
        total_records=total_records,
        total_pages=total_pages,
        query=clean_query,
        sort=clean_sort,
        direction=clean_direction,
    )


def fetch_dashboard_summary() -> AdminDashboardSummary:
    with get_connection() as db:
        total_users = int(
            db.execute(
                "SELECT COUNT(*) FROM users WHERE deleted_at IS NULL"
            ).fetchone()[0]
        )
        completed_profiles = int(
            db.execute(
                """
                SELECT COUNT(*)
                FROM profiles p
                JOIN users u ON u.id = p.user_id
                WHERE u.deleted_at IS NULL
                """
            ).fetchone()[0]
        )
        active_guests = int(
            db.execute(
                "SELECT COUNT(*) FROM guest_sessions WHERE expires_at > ?",
                (utc_now(),),
            ).fetchone()[0]
        )
        rows = db.execute(
            f"""
            {PROFILE_SELECT_SQL}
            WHERE u.deleted_at IS NULL
            ORDER BY COALESCE(u.created_at, u.created_date) DESC, u.id DESC
            LIMIT 5
            """
        ).fetchall()

    return AdminDashboardSummary(
        total_users=total_users,
        completed_profiles=completed_profiles,
        active_guests=active_guests,
        recent_accounts=[_display_record(dict(row)) for row in rows],
    )


def count_admin_accounts() -> int:
    with get_connection() as db:
        return int(
            db.execute(
                """
                SELECT COUNT(*) FROM users
                WHERE is_admin = 1 AND deleted_at IS NULL
                """
            ).fetchone()[0]
        )


def first_admin_setup_completed() -> bool:
    with get_connection() as db:
        setup_row = db.execute(
            "SELECT 1 FROM admin_setup_state WHERE id = 1"
        ).fetchone()
        if setup_row is not None:
            return True
        return bool(
            db.execute("SELECT 1 FROM users WHERE is_admin = 1 LIMIT 1").fetchone()
        )


def user_has_password_login(user: User | None) -> bool:
    if user is None or not (user.email or user.verified_email):
        return False
    with get_connection() as db:
        row = db.execute(
            """
            SELECT 1 FROM users
            WHERE id = ? AND deleted_at IS NULL
              AND password_hash IS NOT NULL AND TRIM(password_hash) <> ''
            """,
            (int(user.id),),
        ).fetchone()
    return row is not None


def user_has_verified_login(user: User | None) -> bool:
    if user is None or not (user.email or user.verified_email):
        return False
    with get_connection() as db:
        row = db.execute(
            """
            SELECT 1 FROM users
            WHERE id = ? AND deleted_at IS NULL
              AND (
                (supabase_user_id IS NOT NULL AND TRIM(supabase_user_id) <> '')
                OR (password_hash IS NOT NULL AND TRIM(password_hash) <> '')
              )
            """,
            (int(user.id),),
        ).fetchone()
    return row is not None


def admin_setup_available_for_user(user: User | None) -> bool:
    if not is_development_environment() or not user_has_verified_login(user):
        return False
    return not first_admin_setup_completed()


def admin_setup_account_label(user: User) -> str:
    if user.email or user.verified_email:
        return mask_destination(user.email or user.verified_email, "email")
    if user.verified_phone:
        return mask_destination(user.verified_phone, "sms")
    return "GovGuideAI account"


def promote_first_password_admin(user_id: int, confirmation: str) -> None:
    if str(confirmation or "").strip() != FIRST_ADMIN_CONFIRMATION:
        raise AdminSetupError(f'Type "{FIRST_ADMIN_CONFIRMATION}" to confirm.')

    now = utc_now()
    with get_connection() as db:
        db.execute("BEGIN IMMEDIATE")
        if db.execute(
            "SELECT 1 FROM admin_setup_state WHERE id = 1"
        ).fetchone() or db.execute(
            "SELECT 1 FROM users WHERE is_admin = 1 LIMIT 1"
        ).fetchone():
            raise AdminSetupError("Administrator setup has already been completed.")

        user = db.execute(
            """
            SELECT id FROM users
            WHERE id = ? AND deleted_at IS NULL
              AND COALESCE(email, verified_email) IS NOT NULL
              AND (
                (supabase_user_id IS NOT NULL AND TRIM(supabase_user_id) <> '')
                OR (password_hash IS NOT NULL AND TRIM(password_hash) <> '')
              )
            LIMIT 1
            """,
            (int(user_id),),
        ).fetchone()
        if user is None:
            raise AdminSetupError("A verified logged-in account is required.")

        db.execute("UPDATE users SET is_admin = 1 WHERE id = ?", (int(user_id),))
        db.execute(
            """
            INSERT INTO admin_setup_state (id, completed_at, admin_user_id)
            VALUES (1, ?, ?)
            """,
            (now, int(user_id)),
        )


def fetch_export_records() -> list[dict]:
    with get_connection() as db:
        rows = db.execute(
            f"""
            {PROFILE_SELECT_SQL}
            WHERE u.deleted_at IS NULL
            ORDER BY u.id ASC
            """
        ).fetchall()
    return [dict(row) for row in rows]


def record_export_audit(
    admin_user_id: int,
    exported_at: str,
    file_format: str,
    record_count: int,
) -> None:
    if file_format not in {"csv", "json"}:
        raise ValueError("Unsupported export format.")
    with get_connection() as db:
        db.execute(
            """
            INSERT INTO export_audit_log (
                admin_user_id, exported_at, file_format, record_count
            ) VALUES (?, ?, ?, ?)
            """,
            (admin_user_id, exported_at, file_format, int(record_count)),
        )


def promote_password_admin(email: str) -> tuple[int, bool]:
    configured_email = os.getenv("ADMIN_EMAIL", "").strip()
    if not configured_email:
        raise AdminPromotionError("ADMIN_EMAIL is not configured on the server.")
    try:
        requested = normalize_email(email)
        configured = normalize_email(configured_email)
    except IdentifierValidationError as error:
        raise AdminPromotionError("ADMIN_EMAIL or the supplied email is invalid.") from error
    if requested != configured:
        raise AdminPromotionError("The supplied email does not match ADMIN_EMAIL.")

    with get_connection() as db:
        row = db.execute(
            """
            SELECT id, is_admin FROM users
            WHERE deleted_at IS NULL
              AND (
                (supabase_user_id IS NOT NULL AND TRIM(supabase_user_id) <> '')
                OR (password_hash IS NOT NULL AND TRIM(password_hash) <> '')
              )
              AND (
                LOWER(COALESCE(email, '')) = ?
                OR LOWER(COALESCE(verified_email, '')) = ?
              )
            LIMIT 1
            """,
            (requested, requested),
        ).fetchone()
        if row is None:
            raise AdminPromotionError(
                "No active verified account with that email exists."
            )
        already_admin = bool(row["is_admin"])
        if not already_admin:
            db.execute("UPDATE users SET is_admin = 1 WHERE id = ?", (row["id"],))
        db.execute(
            """
            INSERT OR IGNORE INTO admin_setup_state (
                id, completed_at, admin_user_id
            ) VALUES (1, ?, ?)
            """,
            (utc_now(), int(row["id"])),
        )
    return int(row["id"]), not already_admin


def safe_promotion_label(email: str) -> str:
    try:
        return mask_destination(normalize_email(email), "email")
    except IdentifierValidationError:
        return "***"


def export_timestamp() -> str:
    return utc_now()


def _where_clause(query: str) -> tuple[str, tuple[str, ...]]:
    where_sql = "WHERE u.deleted_at IS NULL"
    if not query:
        return where_sql, ()
    term = f"%{query.casefold()}%"
    return f"{where_sql} {SEARCH_SQL}", (term,) * 11


def _display_record(record: dict) -> dict:
    displayed = dict(record)
    displayed["email_display"] = (
        mask_destination(str(record["email"]), "email") if record.get("email") else "—"
    )
    displayed["phone_display"] = (
        mask_destination(str(record["phone"]), "sms") if record.get("phone") else "—"
    )
    return displayed
