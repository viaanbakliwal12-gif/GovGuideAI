from __future__ import annotations

from flask import Blueprint, redirect, render_template, request, session, url_for

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
    find_or_create_local_user,
    login_required,
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
        error=None,
        email="",
    )


@auth_bp.post("/login")
def login_post():
    email = request.form.get("email", "").strip()
    try:
        user, created = find_or_create_local_user(email)
    except AccountCreationError as error:
        return (
            render_template(
                "login.html",
                message=None,
                error=error.message,
                email=email,
            ),
            400,
        )

    selected_language = normalize_language(
        session.get("selected_language") or "en"
    )
    establish_user_session(user)
    session["language_selected"] = True
    session["selected_language"] = selected_language
    profile = get_profile(user.id)
    if profile is not None and profile.preferred_language != selected_language:
        update_profile_language(user.id, selected_language)

    return redirect(
        url_for("profiles.setup_profile")
        if created
        else url_for("index")
    )


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
