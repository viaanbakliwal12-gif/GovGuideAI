from __future__ import annotations

from flask import Blueprint, Response, render_template, request

from app.admin.export_service import build_export
from app.admin.services import admin_required, fetch_profile_page, record_export_audit
from app.auth.services import current_user


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
    return render_template("admin/dashboard.html", profile_page=page)


@admin_bp.post("/export/<file_format>")
@admin_required
def export_profiles(file_format: str):
    if file_format not in {"csv", "json"}:
        return Response("Not found", status=404)
    user = current_user()
    payload = build_export(file_format)
    record_export_audit(
        user.id,
        payload.exported_at,
        file_format,
        payload.record_count,
    )
    return Response(
        payload.content,
        content_type=payload.media_type,
        headers={
            "Content-Disposition": f'attachment; filename="{payload.filename}"',
            "Content-Length": str(len(payload.content)),
        },
    )


def _positive_int(value: str | None, default: int) -> int:
    try:
        return max(1, int(value or default))
    except (TypeError, ValueError):
        return default
