from __future__ import annotations

from functools import lru_cache
import os
import re
from uuid import uuid4

from dotenv import load_dotenv
from flask import Flask, jsonify, redirect, render_template, request, session, url_for

from app.agent import GovernmentHelpAgent
from app.auth import auth_bp
from app.auth.services import current_user, login_required
from app.database import init_db
from app.profiles import profiles_bp
from app.profiles.services import get_profile
from app.services import ConversationMemory
from app.tools.word_count import count_words


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

        if not message:
            return jsonify({"error": "Please enter a message."}), 400

        if not conversation_id:
            conversation_id = uuid4().hex

        word_count_answer = _maybe_answer_word_count(message)
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

    @app.post("/api/clear")
    @login_required
    def clear():
        user = current_user()
        payload = request.get_json(silent=True) or {}
        conversation_id = str(payload.get("conversationId", "")).strip()

        conversation_memory.clear(user.id, conversation_id or None)

        return jsonify({"ok": True})

    return app


def _maybe_answer_word_count(message: str) -> str | None:
    """Keep the old word-count behaviour without exposing it as an agent tool."""

    if "word count" not in message.lower() and "count the words" not in message.lower():
        return None

    text = message
    match = re.search(r":\s*(.+)$", message, flags=re.DOTALL)
    if match:
        text = match.group(1)

    total = count_words(text)
    return f"The text has {total} words."
