from __future__ import annotations

from io import BytesIO

from flask import Blueprint, jsonify, request, send_file

from app.auth.services import login_required
from app.profiles.services import normalize_language
from app.voice.services import (
    MAX_AUDIO_BYTES,
    SPEECH_MIME_TYPE,
    VoiceServiceError,
    generate_speech_audio,
    transcribe_audio_upload,
)


voice_bp = Blueprint("voice", __name__)


@voice_bp.post("/api/voice/transcribe")
@login_required
def transcribe():
    if request.content_length and request.content_length > MAX_AUDIO_BYTES + 1024 * 1024:
        return jsonify({"error": "The recording is too large. Please record a shorter message."}), 413

    try:
        result = transcribe_audio_upload(
            request.files.get("audio"),
            normalize_language(request.form.get("preferredLanguage")),
        )
    except VoiceServiceError as error:
        return jsonify({"error": str(error)}), 400
    except Exception:
        return jsonify({"error": "Voice transcription failed. Please try again or use text chat."}), 500

    return jsonify(result)


@voice_bp.post("/api/voice/speak")
@login_required
def speak():
    payload = request.get_json(silent=True) or {}
    try:
        audio = generate_speech_audio(
            str(payload.get("text", "")),
            normalize_language(payload.get("preferredLanguage")),
            str(payload.get("voice", "")),
        )
    except VoiceServiceError as error:
        return jsonify({"error": str(error)}), 400
    except Exception:
        return jsonify({"error": "Speech generation failed. The text answer is still available."}), 500

    return send_file(
        BytesIO(audio),
        mimetype=SPEECH_MIME_TYPE,
        as_attachment=False,
        download_name="govguideai-response.mp3",
    )
