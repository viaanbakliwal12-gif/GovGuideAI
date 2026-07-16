from __future__ import annotations

from flask import (
    Blueprint,
    Response,
    abort,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)

from app.admin.export_service import build_export
from app.admin.services import (
    FIRST_ADMIN_CONFIRMATION,
    AdminSetupError,
    admin_required,
    admin_setup_account_label,
    fetch_dashboard_summary,
    fetch_profile_page,
    first_admin_setup_completed,
    promote_first_local_admin,
    record_export_audit,
    user_has_email_login,
)
from app.auth.password_setup import PasswordSetupError, create_password_setup_token
from app.auth.services import current_user
from app.config import is_development_environment


admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


@admin_bp.after_request
def protect_admin_responses(response):
    response.headers["Cache-Control"] = "no-store, private"
    response.headers["Pragma"] = "no-cache"
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response


@admin_bp.get("")
@admin_required
def dashboard():
    page = fetch_profile_page(
        query=request.args.get("q", ""),
        sort=request.args.get("sort", "user_id"),
        direction=request.args.get("direction", "asc"),
        page=_positive_int(request.args.get("page"), 1),
        per_page=_positive_int(request.args.get("per_page"), 25),
    )
    return render_template(
        "admin/dashboard.html",
        profile_page=page,
        summary=fetch_dashboard_summary(),
    )


@admin_bp.get("/setup")
def setup():
    user = _first_admin_setup_user()
    return render_template(
        "admin/setup.html",
        account_label=admin_setup_account_label(user),
        confirmation_phrase=FIRST_ADMIN_CONFIRMATION,
        error=None,
    )


@admin_bp.post("/setup")
def setup_post():
    user = _first_admin_setup_user()
    try:
        promote_first_local_admin(
            user.id,
            request.form.get("confirmation", ""),
        )
    except AdminSetupError as error:
        if first_admin_setup_completed():
            abort(404)
        return (
            render_template(
                "admin/setup.html",
                account_label=admin_setup_account_label(user),
                confirmation_phrase=FIRST_ADMIN_CONFIRMATION,
                error=str(error),
            ),
            400,
        )

    flash("Administrator access is ready. This first-admin setup page is now disabled.", "success")
    return redirect(url_for("admin.dashboard"))


@admin_bp.post("/users/<int:user_id>/password-setup")
@admin_required
def create_password_setup(user_id: int):
    user = current_user()
    try:
        setup = create_password_setup_token(user_id, user.id)
    except PasswordSetupError as error:
        flash(error.message, "error")
        return redirect(url_for("admin.dashboard"))

    return render_template(
        "admin/password_setup_created.html",
        account_label=setup.account_label,
        expires_at=setup.expires_at,
        setup_url=url_for("auth.set_password", token=setup.token, _external=True),
    )


@admin_bp.post("/export/<file_format>")
@admin_required
def export_profiles(file_format: str):
    if file_format not in {"csv", "json"}:
        return Response("Not found", status=404)
    user = current_user()
    try:
        payload = build_export(file_format)
        record_export_audit(
            user.id,
            payload.exported_at,
            file_format,
            payload.record_count,
        )
    except Exception:
        current_app.logger.exception(
            "Admin profile export failed format=%s admin_user_id=%s",
            file_format,
            user.id,
        )
        flash("The export could not be prepared. Please try again.", "error")
        return redirect(url_for("admin.dashboard"))

    flash(
        f"{file_format.upper()} export prepared with {payload.record_count} records.",
        "success",
    )
    return Response(
        payload.content,
        content_type=payload.media_type,
        headers={
            "Content-Disposition": f'attachment; filename="{payload.filename}"',
            "Content-Length": str(len(payload.content)),
        },
    )


@admin_bp.errorhandler(403)
def access_denied(_error):
    return render_template("admin/access_denied.html"), 403


def _first_admin_setup_user():
    if not is_development_environment() or first_admin_setup_completed():
        abort(404)
    user = current_user()
    if user is None or not user_has_email_login(user):
        abort(403)
    return user


def _positive_int(value: str | None, default: int) -> int:
    try:
        return max(1, int(value or default))
    except (TypeError, ValueError):
        return default
