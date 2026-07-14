from __future__ import annotations

from flask import Blueprint, redirect, render_template, request, session, url_for

from app.auth.services import authenticate_user, create_user, current_user, delete_user
from app.profiles.services import get_profile, update_profile_language


auth_bp = Blueprint("auth", __name__)


@auth_bp.get("/signup")
def signup():
    if current_user() is not None:
        return redirect(url_for("index"))
    return render_template("signup.html", error=None)


@auth_bp.post("/signup")
def signup_post():
    ok, message = create_user(
        request.form.get("email", ""),
        request.form.get("password", ""),
    )
    if not ok:
        return render_template("signup.html", error=message), 400
    return redirect(url_for("auth.login", message=message))


@auth_bp.get("/login")
def login():
    if current_user() is not None:
        return redirect(url_for("index"))
    return render_template("login.html", error=None, message=request.args.get("message"))


@auth_bp.post("/login")
def login_post():
    user = authenticate_user(
        request.form.get("email", ""),
        request.form.get("password", ""),
    )
    if user is None:
        return render_template("login.html", error="Incorrect email or password.", message=None), 401

    session.clear()
    session["user_id"] = user.id

    profile = get_profile(user.id)
    if profile is None:
        return redirect(url_for("profiles.setup_profile"))
    selected_language = request.form.get("selected_language")
    if selected_language:
        update_profile_language(user.id, selected_language)
    return redirect(url_for("index"))


@auth_bp.post("/logout")
def logout():
    session.clear()
    return redirect(url_for("auth.login"))


@auth_bp.post("/account/delete")
def delete_account():
    user = current_user()
    if user is not None:
        delete_user(user.id)
    session.clear()
    return redirect(url_for("auth.signup"))
