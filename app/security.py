from __future__ import annotations

import secrets

from flask import abort, request, session


def csrf_token() -> str:
    token = session.get("csrf_token")
    if not token:
        token = secrets.token_urlsafe(32)
        session["csrf_token"] = token
    return str(token)


def init_security(app) -> None:
    app.config.update(
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
    )

    @app.context_processor
    def provide_csrf_token():
        return {"csrf_token": csrf_token}

    @app.before_request
    def protect_state_changes():
        if request.method not in {"POST", "PUT", "PATCH", "DELETE"}:
            return None
        if app.config.get("TESTING"):
            return None

        supplied = request.headers.get("X-CSRF-Token") or request.form.get("_csrf_token")
        expected = session.get("csrf_token")
        if not supplied or not expected or not secrets.compare_digest(str(supplied), str(expected)):
            abort(400, description="The form expired. Refresh the page and try again.")
        return None
