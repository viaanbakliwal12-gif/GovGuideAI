from __future__ import annotations

from flask import Blueprint, redirect, render_template, request, session, url_for

from app.auth.guest_service import end_guest_session, start_guest_session
from app.auth.otp_service import (
    OTPServiceError,
    get_challenge_state,
    request_otp,
    resend_otp,
    verify_otp,
)
from app.auth.services import (
    authenticate_user,
    create_user,
    current_user,
    delete_user,
    establish_user_session,
    login_required,
)
from app.auth.validators import IdentifierValidationError, country_options
from app.profiles.services import get_profile, normalize_language, update_profile_language


auth_bp = Blueprint("auth", __name__)


@auth_bp.get("/signup")
def signup():
    if current_user() is not None:
        return redirect(url_for("index"))
    return _render_auth_page("signup")


@auth_bp.post("/signup")
def signup_post():
    """Preserve password sign-up as an optional legacy-compatible path."""

    ok, message = create_user(
        request.form.get("email", ""),
        request.form.get("password", ""),
    )
    if not ok:
        return _render_auth_page("signup", error=message, active_mode="email"), 400
    return redirect(url_for("auth.login", message=message))


@auth_bp.get("/login")
def login():
    if current_user() is not None:
        return redirect(url_for("index"))
    return _render_auth_page("login", message=request.args.get("message"))


@auth_bp.post("/login")
def login_post():
    """Keep existing password accounts usable while OTP is the primary flow."""

    user = authenticate_user(
        request.form.get("email", ""),
        request.form.get("password", ""),
    )
    if user is None:
        return (
            _render_auth_page(
                "login",
                error="Incorrect email or password.",
                error_key="incorrectPassword",
                active_mode="email",
            ),
            401,
        )

    establish_user_session(user)
    selected_language = request.form.get("selected_language")
    profile = get_profile(user.id)
    if profile is None:
        return redirect(url_for("profiles.setup_profile"))
    if selected_language:
        update_profile_language(user.id, selected_language)
    return redirect(url_for("index"))


@auth_bp.post("/auth/request-code")
def request_code():
    purpose = request.form.get("purpose", "login")
    if purpose not in {"login", "signup"}:
        purpose = "login"
    channel = request.form.get("channel", "email")
    destination = (
        request.form.get("email", "")
        if channel == "email"
        else request.form.get("phone_number", "")
    )
    country = request.form.get("country", "IN")
    selected_language = normalize_language(request.form.get("selected_language"))

    try:
        challenge = request_otp(
            channel=channel,
            destination_value=destination,
            country_code=country,
            purpose=purpose,
            request_ip=request.remote_addr or "unknown",
        )
    except IdentifierValidationError as error:
        error_key = "invalidEmail" if channel == "email" else "invalidPhone"
        return (
            _render_auth_page(
                purpose,
                error=str(error),
                error_key=error_key,
                active_mode="email" if channel == "email" else "phone",
                email=request.form.get("email", ""),
                phone_number=request.form.get("phone_number", ""),
                selected_country=country,
            ),
            400,
        )
    except OTPServiceError as error:
        return (
            _render_auth_page(
                purpose,
                error=str(error),
                error_key=error.error_key,
                active_mode="email" if channel == "email" else "phone",
                email=request.form.get("email", ""),
                phone_number=request.form.get("phone_number", ""),
                selected_country=country,
            ),
            error.status_code,
        )

    session["pending_otp"] = challenge.public_id
    session["pending_auth_language"] = selected_language
    return redirect(url_for("auth.verification"))


@auth_bp.get("/verify")
def verification():
    challenge_id = str(session.get("pending_otp", ""))
    state = get_challenge_state(challenge_id)
    if state is None:
        return redirect(url_for("auth.login"))
    return render_template(
        "verify_otp.html",
        challenge=state,
        error="That code is incorrect or has expired." if state.expired else None,
        error_key="codeExpired" if state.expired else None,
        verified=False,
        next_url=None,
    )


@auth_bp.post("/verify")
def verification_post():
    challenge_id = str(session.get("pending_otp", ""))
    if not challenge_id or request.form.get("challenge_id") != challenge_id:
        return redirect(url_for("auth.login"))

    try:
        result = verify_otp(challenge_id, request.form.get("code", ""))
    except OTPServiceError as error:
        state = get_challenge_state(challenge_id)
        if state is None:
            return redirect(url_for("auth.login"))
        return (
            render_template(
                "verify_otp.html",
                challenge=state,
                error=str(error),
                error_key=error.error_key,
                verified=False,
                next_url=None,
            ),
            error.status_code,
        )

    selected_language = session.get("pending_auth_language")
    establish_user_session(result.user)
    profile = get_profile(result.user.id)
    if profile is not None and selected_language:
        update_profile_language(result.user.id, str(selected_language))
    next_url = (
        url_for("profiles.setup_profile") if profile is None else url_for("index")
    )
    return render_template(
        "verify_otp.html",
        challenge=None,
        error=None,
        error_key=None,
        verified=True,
        next_url=next_url,
    )


@auth_bp.post("/auth/resend-code")
def resend_code():
    challenge_id = str(session.get("pending_otp", ""))
    if not challenge_id or request.form.get("challenge_id") != challenge_id:
        return redirect(url_for("auth.login"))

    try:
        challenge = resend_otp(challenge_id, request.remote_addr or "unknown")
    except OTPServiceError as error:
        state = get_challenge_state(challenge_id)
        if state is None:
            return redirect(url_for("auth.login"))
        return (
            render_template(
                "verify_otp.html",
                challenge=state,
                error=str(error),
                error_key=error.error_key,
                verified=False,
                next_url=None,
            ),
            error.status_code,
        )

    session["pending_otp"] = challenge.public_id
    return redirect(url_for("auth.verification"))


@auth_bp.post("/guest")
def continue_as_guest():
    language = normalize_language(request.form.get("selected_language"))
    start_guest_session(language)
    return redirect(url_for("index"))


@auth_bp.post("/logout")
def logout():
    end_guest_session()
    session.clear()
    return redirect(url_for("auth.login"))


@auth_bp.post("/account/delete")
@login_required
def delete_account():
    user = current_user()
    if user is not None:
        delete_user(user.id)
    session.clear()
    return redirect(url_for("auth.signup"))


def _render_auth_page(
    purpose: str,
    *,
    error: str | None = None,
    error_key: str | None = None,
    message: str | None = None,
    active_mode: str | None = None,
    email: str = "",
    phone_number: str = "",
    selected_country: str = "IN",
):
    template = "signup.html" if purpose == "signup" else "login.html"
    requested_mode = active_mode or request.args.get("mode", "email")
    return render_template(
        template,
        error=error,
        error_key=error_key,
        message=message,
        purpose=purpose,
        active_mode="phone" if requested_mode == "phone" else "email",
        countries=country_options(),
        email=email,
        phone_number=phone_number,
        selected_country=selected_country,
    )
