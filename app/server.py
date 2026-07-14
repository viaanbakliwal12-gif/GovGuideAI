from __future__ import annotations

from functools import lru_cache
import json
import os
import re
from uuid import uuid4

from dotenv import load_dotenv
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
from app.auth import auth_bp
from app.auth.services import current_user, login_required
from app.database import init_db
from app.profiles import profiles_bp
from app.profiles.services import get_profile, normalize_language
from app.services import ConversationMemory
from app.tools.word_count import count_words
from app.voice import voice_bp


conversation_memory = ConversationMemory()


@lru_cache(maxsize=1)
def get_agent() -> GovernmentHelpAgent:
    return GovernmentHelpAgent.from_environment()


def create_app() -> Flask:
    load_dotenv()
    app = Flask(
        __name__,
        template_folder="../templates",
        static_folder="../static",
    )
    app.config["SECRET_KEY"] = os.getenv("FLASK_SECRET_KEY", "dev-only-change-this-secret")

    init_db()
    app.register_blueprint(auth_bp)
    app.register_blueprint(profiles_bp)
    app.register_blueprint(voice_bp)

    @app.get("/language")
    def language_select():
        next_url = request.args.get("next", "/login")
        if not next_url.startswith("/"):
            next_url = "/login"
        return render_template("language_select.html", next_url=next_url)

    @app.get("/")
    @login_required
    def index():
        user = current_user()
        profile = get_profile(user.id)
        if profile is None:
            return redirect(url_for("profiles.setup_profile"))

        return render_template("index.html", user=user, profile=profile)

    @app.post("/api/chat")
    @login_required
    def chat():
        user = current_user()
        profile = get_profile(user.id)
        if profile is None:
            return jsonify({"error": "Please complete your profile first."}), 403

        payload = request.get_json(silent=True) or {}
        message = str(payload.get("message", "")).strip()
        conversation_id = str(payload.get("conversationId", "")).strip()
        selected_language = normalize_language(
            payload.get("selectedLanguage") or profile.preferred_language
        )

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
                    "toolsUsed": [],
                }
            )

        previous_response_id = conversation_memory.get_previous_response_id(
            user.id,
            conversation_id,
        )

        try:
            agent_response = get_agent().respond(
                user_message=message,
                previous_response_id=previous_response_id,
                profile=profile.to_agent_context(),
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

        conversation_memory.save_response_id(user.id, conversation_id, agent_response.response_id)

        return jsonify(
            {
                "answer": agent_response.answer,
                "conversationId": conversation_id,
                "toolsUsed": agent_response.tools_used,
            }
        )

    @app.post("/api/chat/stream")
    @login_required
    def chat_stream():
        """Stream tool activity, then deliver the same completed chat payload."""

        user = current_user()
        profile = get_profile(user.id)
        if profile is None:
            return jsonify({"error": "Please complete your profile first."}), 403

        payload = request.get_json(silent=True) or {}
        message = str(payload.get("message", "")).strip()
        conversation_id = str(payload.get("conversationId", "")).strip() or uuid4().hex
        selected_language = normalize_language(
            payload.get("selectedLanguage") or profile.preferred_language
        )

        if not message:
            return jsonify({"error": "Please enter a message."}), 400

        previous_response_id = conversation_memory.get_previous_response_id(
            user.id,
            conversation_id,
        )
        profile_context = profile.to_agent_context()

        def generate():
            yield _ndjson_event({"type": "status", "status": "thinking"})

            word_count_answer = _maybe_answer_word_count(message, selected_language)
            if word_count_answer:
                yield _ndjson_event(
                    {
                        "type": "result",
                        "answer": word_count_answer,
                        "conversationId": conversation_id,
                        "toolsUsed": [],
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
                    user.id,
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
    @login_required
    def clear():
        user = current_user()
        payload = request.get_json(silent=True) or {}
        conversation_id = str(payload.get("conversationId", "")).strip()

        conversation_memory.clear(user.id, conversation_id or None)

        return jsonify({"ok": True})

    return app


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
