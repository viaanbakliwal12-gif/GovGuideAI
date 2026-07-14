from __future__ import annotations

from flask import Blueprint, jsonify, redirect, render_template, request, url_for

from app.auth.services import current_user, login_required
from app.profiles.services import (
    delete_profile,
    get_profile,
    profile_from_form,
    save_profile,
    update_profile_language,
    validate_profile,
)


profiles_bp = Blueprint("profiles", __name__)


@profiles_bp.get("/profile/setup")
@login_required
def setup_profile():
    user = current_user()
    profile = get_profile(user.id)
    if profile is not None:
        return redirect(url_for("index"))
    return render_template("profile_setup.html", profile=None, error=None)


@profiles_bp.post("/profile/setup")
@login_required
def setup_profile_post():
    user = current_user()
    data = profile_from_form(request.form)
    error = validate_profile(data)
    if error:
        return render_template("profile_setup.html", profile=data, error=error), 400
    save_profile(user.id, data)
    return redirect(url_for("index"))


@profiles_bp.get("/profile")
@login_required
def profile():
    user = current_user()
    return render_template(
        "profile.html",
        profile=get_profile(user.id),
        error=None,
        saved=request.args.get("saved") == "1",
    )


@profiles_bp.post("/profile")
@login_required
def profile_post():
    user = current_user()
    data = profile_from_form(request.form)
    error = validate_profile(data)
    if error:
        return render_template("profile.html", profile=data, error=error, saved=False), 400
    save_profile(user.id, data)
    return redirect(url_for("profiles.profile", saved="1"))


@profiles_bp.post("/api/profile/language")
@login_required
def profile_language():
    user = current_user()
    payload = request.get_json(silent=True) or {}
    language = update_profile_language(user.id, payload.get("language"))
    return jsonify({"language": language})


@profiles_bp.post("/profile/delete")
@login_required
def profile_delete():
    user = current_user()
    delete_profile(user.id)
    return redirect(url_for("profiles.setup_profile"))
