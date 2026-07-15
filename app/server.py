from __future__ import annotations

from datetime import timedelta
from functools import lru_cache
import json
import logging
import os
import re
from uuid import uuid4

# Import configuration before application services so .env is available when
# any authentication or database module reads its settings.
from app.config import application_environment, load_app_environment

load_app_environment()

from flask import (
    Flask,
    Response,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    stream_with_context,
    url_for,
)

from app.agent import AgentActivity, AgentResponse, GovernmentHelpAgent
from app.admin import admin_bp
from app.admin.services import admin_setup_available_for_user, count_admin_accounts
from app.auth import auth_bp
from app.auth.services import (
    assistant_access_required,
    current_subject_key,
    current_user,
    is_guest,
)
from app.database import init_db
from app.profiles import profiles_bp
from app.profiles.services import get_profile, normalize_language
from app.security import init_security
from app.services import ConversationMemory
from app.tools.word_count import count_words
from app.voice import voice_bp


conversation_memory = ConversationMemory()


@lru_cache(maxsize=1)
def get_agent() -> GovernmentHelpAgent:
    return GovernmentHelpAgent.from_environment()


def create_app() -> Flask:
    load_app_environment()
    secret_key = os.getenv("SECRET_KEY")
    if not secret_key:
        raise RuntimeError(
            "SECRET_KEY was not found. Add it to your .env file or deployment environment."
        )

    app = Flask(
        __name__,
        template_folder="../templates",
        static_folder="../static",
    )
    app.config["SECRET_KEY"] = secret_key
    app.logger.setLevel(logging.INFO)
    app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(days=14)
    app.config["SESSION_COOKIE_SECURE"] = os.getenv(
        "APP_ENV", os.getenv("FLASK_ENV", "development")
    ).strip().lower() in {"production", "prod"}
    init_security(app)
    init_db()
    app.logger.info("Environment: %s", application_environment())
    app.logger.info("Authentication: email and password")
    app.logger.info("Admin accounts: %d", count_admin_accounts())

    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(profiles_bp)
    app.register_blueprint(voice_bp)

    @app.context_processor
    def provide_admin_navigation():
        user = current_user()
        return {
            "show_admin_dashboard_link": bool(user and user.is_admin),
            "show_admin_setup_link": admin_setup_available_for_user(user),
        }

    @app.get("/health")
    def health():
        return jsonify({"status": "ok"})

    @app.get("/language")
    def language_select():
        next_url = _safe_local_next_url(request.args.get("next"))
        return render_template("language_select.html", next_url=next_url)

    @app.post("/language")
    def language_select_post():
        selected_language = normalize_language(request.form.get("selected_language"))
        session["language_selected"] = True
        session["selected_language"] = selected_language
        return redirect(_safe_local_next_url(request.form.get("next")))

    @app.get("/")
    @assistant_access_required
    def index():
        user = current_user()
        guest = is_guest()
        profile = get_profile(user.id) if user is not None else None
        if not guest and profile is None:
            return redirect(url_for("profiles.setup_profile"))

        return render_template(
            "index.html",
            user=user,
            profile=profile,
            is_guest=guest,
            guest_language=session.get("guest_language", "en"),
        )

    @app.post("/api/chat")
    @assistant_access_required
    def chat():
        user = current_user()
        guest = is_guest()
        profile = get_profile(user.id) if user is not None else None
        if not guest and profile is None:
            return jsonify({"error": "Please complete your profile first."}), 403

        payload = request.get_json(silent=True) or {}
        message = str(payload.get("message", "")).strip()
        conversation_id = str(payload.get("conversationId", "")).strip()
        selected_language = normalize_language(
            payload.get("selectedLanguage")
            or (profile.preferred_language if profile else session.get("guest_language"))
        )
        subject_key = current_subject_key()

        if not message:
            return jsonify({"error": "Please enter a message."}), 400

        if not conversation_id:
            conversation_id = uuid4().hex

        word_count_answer = _maybe_answer_word_count(message, selected_language)
        if word_count_answer:
            return jsonify(
                {
                    "answer": word_count_answer,
                    "conversationId": conversation_id,
                    "toolsUsed": ["Word Count"],
                }
            )

        previous_response_id = conversation_memory.get_previous_response_id(
            subject_key,
            conversation_id,
        )

        try:
            agent_response = get_agent().respond(
                user_message=message,
                previous_response_id=previous_response_id,
                profile=(profile.to_agent_context(message) if profile else None),
                selected_language=selected_language,
            )
        except Exception:
            app.logger.exception("Agent request failed")
            return (
                jsonify(
                    {
                        "error": (
                            "GovGuideAI could not respond right now. Check the server "
                            "logs and confirm your OpenAI API key is configured."
                        )
                    }
                ),
                500,
            )

        conversation_memory.save_response_id(subject_key, conversation_id, agent_response.response_id)

        return jsonify(
            {
                "answer": agent_response.answer,
                "conversationId": conversation_id,
                "toolsUsed": agent_response.tools_used,
            }
        )

    @app.post("/api/chat/stream")
    @assistant_access_required
    def chat_stream():
        """Stream tool activity, then deliver the same completed chat payload."""

        user = current_user()
        guest = is_guest()
        profile = get_profile(user.id) if user is not None else None
        if not guest and profile is None:
            return jsonify({"error": "Please complete your profile first."}), 403

        payload = request.get_json(silent=True) or {}
        message = str(payload.get("message", "")).strip()
        conversation_id = str(payload.get("conversationId", "")).strip() or uuid4().hex
        selected_language = normalize_language(
            payload.get("selectedLanguage")
            or (profile.preferred_language if profile else session.get("guest_language"))
        )
        subject_key = current_subject_key()

        if not message:
            return jsonify({"error": "Please enter a message."}), 400

        previous_response_id = conversation_memory.get_previous_response_id(
            subject_key,
            conversation_id,
        )
        profile_context = profile.to_agent_context(message) if profile else {}

        def generate():
            yield _ndjson_event({"type": "status", "status": "thinking"})

            word_count_answer = _maybe_answer_word_count(message, selected_language)
            if word_count_answer:
                yield _ndjson_event(
                    {
                        "type": "result",
                        "answer": word_count_answer,
                        "conversationId": conversation_id,
                        "toolsUsed": ["Word Count"],
                    }
                )
                return

            try:
                agent_response = None
                for event in get_agent().respond_events(
                    user_message=message,
                    previous_response_id=previous_response_id,
                    profile=profile_context,
                    selected_language=selected_language,
                ):
                    if isinstance(event, AgentActivity):
                        yield _ndjson_event(
                            {
                                "type": "status",
                                "status": _chat_status_for_activity(event, message),
                            }
                        )
                    elif isinstance(event, AgentResponse):
                        agent_response = event

                if agent_response is None:
                    raise RuntimeError("The agent did not return a completed response.")

                conversation_memory.save_response_id(
                    subject_key,
                    conversation_id,
                    agent_response.response_id,
                )
                yield _ndjson_event(
                    {
                        "type": "result",
                        "answer": agent_response.answer,
                        "conversationId": conversation_id,
                        "toolsUsed": agent_response.tools_used,
                    }
                )
            except Exception:
                app.logger.exception("Streamed agent request failed")
                yield _ndjson_event(
                    {
                        "type": "error",
                        "error": (
                            "GovGuideAI could not respond right now. Check the server "
                            "logs and confirm your OpenAI API key is configured."
                        ),
                    }
                )

        return Response(
            stream_with_context(generate()),
            mimetype="application/x-ndjson",
            headers={
                "Cache-Control": "no-store",
                "X-Accel-Buffering": "no",
            },
        )

    @app.post("/api/clear")
    @assistant_access_required
    def clear():
        subject_key = current_subject_key()
        payload = request.get_json(silent=True) or {}
        conversation_id = str(payload.get("conversationId", "")).strip()

        conversation_memory.clear(subject_key, conversation_id or None)

        return jsonify({"ok": True})

    return app


def _safe_local_next_url(value: str | None) -> str:
    next_url = str(value or "/login").strip()
    if not next_url.startswith("/") or next_url.startswith("//"):
        return "/login"
    return next_url


def _ndjson_event(payload: dict) -> str:
    return f"{json.dumps(payload, ensure_ascii=False)}\n"


def _chat_status_for_activity(activity: AgentActivity, user_message: str) -> str:
    if activity.tool == "search_government_schemes":
        return "official_sources"
    if activity.tool == "web_search" and _is_official_source_action(activity, user_message):
        return "official_sources"
    if activity.tool == "web_search":
        return "web_search"
    return "thinking"


def _is_official_source_action(activity: AgentActivity, user_message: str) -> bool:
    action_text = " ".join((*activity.queries, *activity.urls)).lower()
    if re.search(r"\b(?:[a-z0-9-]+\.)*(?:gov\.in|nic\.in)\b", action_text):
        return True
    if "site:gov.in" in action_text or "site:nic.in" in action_text:
        return True

    official_topics = (
        "scheme",
        "programme",
        "service",
        "document",
        "passport",
        "certificate",
        "licence",
        "license",
        "eligib",
        "procedure",
        "application process",
        "how to apply",
        "official portal",
        "grievance",
        "cpgrams",
        "scholarship",
        "pension",
        "subsidy",
        "ration card",
        "voter id",
        "aadhaar",
        "permit",
        "योजना",
        "सेवा",
        "दस्तावेज",
        "पात्रता",
        "प्रक्रिया",
        "आवेदन",
        "पासपोर्ट",
        "प्रमाणपत्र",
        "छात्रवृत्ति",
    )
    request_text = f"{user_message.lower()} {action_text}"
    return any(topic in request_text for topic in official_topics)


def _maybe_answer_word_count(message: str, language: str = "en") -> str | None:
    """Keep the old word-count behaviour without exposing it as an agent tool."""

    if "word count" not in message.lower() and "count the words" not in message.lower():
        return None

    text = message
    match = re.search(r":\s*(.+)$", message, flags=re.DOTALL)
    if match:
        text = match.group(1)

    total = count_words(text)
    templates = {
        "hi": "इस पाठ में {total} शब्द हैं.",
        "mr": "या मजकुरात {total} शब्द आहेत.",
        "bn": "এই লেখায় {total}টি শব্দ আছে.",
        "ta": "இந்த உரையில் {total} சொற்கள் உள்ளன.",
        "te": "ఈ వచనంలో {total} పదాలు ఉన్నాయి.",
        "gu": "આ લખાણમાં {total} શબ્દો છે.",
        "kn": "ಈ ಪಠ್ಯದಲ್ಲಿ {total} ಪದಗಳಿವೆ.",
        "ml": "ഈ വാചകത്തിൽ {total} വാക്കുകളുണ്ട്.",
        "pa": "ਇਸ ਲਿਖਤ ਵਿੱਚ {total} ਸ਼ਬਦ ਹਨ.",
        "ur": "اس متن میں {total} الفاظ ہیں.",
    }
    return templates.get(language, "The text has {total} words.").format(total=total)
