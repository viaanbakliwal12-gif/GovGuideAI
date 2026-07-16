from __future__ import annotations

from flask import Blueprint, jsonify, redirect, render_template, request, session, url_for

from app.auth.guest_service import end_guest_session, start_guest_session
from app.auth.password_setup import (
    PasswordSetupError,
    complete_password_setup,
    get_password_setup_state,
)
from app.auth.services import (
    AccountCreationError,
    current_user,
    delete_user,
    establish_user_session,
    find_or_create_supabase_user,
    login_required,
)
from app.auth.supabase import (
    SupabaseAuthenticationError,
    SupabaseConfigurationError,
    SupabaseNetworkError,
    public_supabase_config,
    verify_supabase_access_token,
)
from app.auth.validators import (
    IdentifierValidationError,
    normalize_email,
    password_validation_error,
)
from app.profiles.services import get_profile, normalize_language, update_profile_language


auth_bp = Blueprint("auth", __name__)


@auth_bp.after_request
def protect_auth_responses(response):
    response.headers["Cache-Control"] = "no-store, private"
    response.headers["Pragma"] = "no-cache"
    response.headers["Referrer-Policy"] = "no-referrer"
    return response


@auth_bp.get("/signup")
def signup():
    return redirect(url_for("auth.login", next=request.args.get("next")))


@auth_bp.get("/login")
def login():
    user = current_user()
    if user is not None:
        return redirect(
            url_for("profiles.setup_profile")
            if get_profile(user.id) is None
            else url_for("index")
        )
    return render_template(
        "login.html",
        message=request.args.get("message"),
        next_url=_safe_local_next_url(request.args.get("next")),
    )


@auth_bp.get("/api/auth/config")
def supabase_config():
    status = 200
    try:
        url, anon_key = public_supabase_config()
    except SupabaseConfigurationError:
        url, anon_key, status = "", "", 503
    response = jsonify(
        {
            "SUPABASE_URL": url,
            "SUPABASE_ANON_KEY": anon_key,
        }
    )
    response.status_code = status
    response.headers["Cache-Control"] = "no-store"
    return response


@auth_bp.post("/api/auth/session")
def create_supabase_session():
    payload = request.get_json(silent=True) or {}
    try:
        identity = verify_supabase_access_token(payload.get("access_token", ""))
        user = find_or_create_supabase_user(identity)
    except SupabaseConfigurationError as error:
        return jsonify({"error": str(error)}), 503
    except SupabaseAuthenticationError as error:
        return jsonify({"error": str(error)}), 401
    except SupabaseNetworkError as error:
        return jsonify({"error": str(error)}), 502
    except AccountCreationError as error:
        return jsonify({"error": error.message}), 409

    selected_language = normalize_language(
        payload.get("selected_language")
        or session.get("selected_language")
        or "en"
    )
    establish_user_session(user)
    session["supabase_authenticated"] = True
    session["language_selected"] = True
    session["selected_language"] = selected_language
    profile = get_profile(user.id)
    if profile is not None and profile.preferred_language != selected_language:
        update_profile_language(user.id, selected_language)

    requested_next = _safe_local_next_url(payload.get("next"))
    next_url = (
        url_for("profiles.setup_profile")
        if profile is None
        else requested_next or url_for("index")
    )
    if next_url in {url_for("auth.login"), url_for("auth.signup")}:
        next_url = url_for("index")
    return jsonify({"ok": True, "next": next_url})


@auth_bp.get("/account/set-password/<token>")
def set_password(token: str):
    state = get_password_setup_state(token)
    return (
        render_template(
            "set_password.html",
            token=token,
            state=state,
            errors={},
            email="",
        ),
        200 if state is not None else 404,
    )


@auth_bp.post("/account/set-password/<token>")
def set_password_post(token: str):
    state = get_password_setup_state(token)
    email = request.form.get("email", "").strip()
    password = request.form.get("password", "")
    confirm_password = request.form.get("confirm_password", "")
    errors: dict[str, str] = {}

    if state is None:
        return (
            render_template(
                "set_password.html",
                token=token,
                state=None,
                errors={"form": "This password setup link is invalid or has expired."},
                email=email,
            ),
            400,
        )
    if password != confirm_password:
        errors["confirm_password"] = "Passwords do not match."
    password_error = password_validation_error(password)
    if password_error:
        errors["password"] = password_error
    if state.email_required:
        try:
            normalize_email(email)
        except IdentifierValidationError:
            errors["email"] = "Enter a valid email address."
    if errors:
        return (
            render_template(
                "set_password.html",
                token=token,
                state=state,
                errors=errors,
                email=email,
            ),
            400,
        )

    try:
        user = complete_password_setup(
            token,
            email=email,
            password=password,
        )
    except PasswordSetupError as error:
        return (
            render_template(
                "set_password.html",
                token=token,
                state=get_password_setup_state(token),
                errors={error.field: error.message},
                email=email,
            ),
            400,
        )

    establish_user_session(user)
    session["language_selected"] = True
    session["selected_language"] = normalize_language(
        session.get("selected_language") or "en"
    )
    return redirect(
        url_for("index")
        if get_profile(user.id) is not None
        else url_for("profiles.setup_profile")
    )


@auth_bp.post("/guest")
def continue_as_guest():
    language = normalize_language(request.form.get("selected_language"))
    start_guest_session(language)
    return redirect(url_for("index"))


@auth_bp.post("/logout")
def logout():
    selected_language = normalize_language(
        session.get("selected_language") or session.get("guest_language")
    )
    end_guest_session()
    session.clear()
    session["language_selected"] = True
    session["selected_language"] = selected_language
    return redirect(url_for("auth.login"))


@auth_bp.post("/account/delete")
@login_required
def delete_account():
    user = current_user()
    if user is not None:
        delete_user(user.id)
    session.clear()
    return redirect(url_for("auth.signup"))


def _safe_local_next_url(value: str | None) -> str:
    next_url = str(value or "").strip()
    if not next_url or not next_url.startswith("/") or next_url.startswith("//"):
        return ""
    return next_url
