from __future__ import annotations

import os
from pathlib import Path
import tempfile

from dotenv import load_dotenv
from openai import OpenAI
from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename


MAX_AUDIO_BYTES = 15 * 1024 * 1024
MAX_SPEECH_TEXT_CHARS = 3000
TRANSCRIPTION_MODEL = "gpt-4o-mini-transcribe"
SPEECH_MODEL = "gpt-4o-mini-tts"
SPEECH_FORMAT = "mp3"
SPEECH_MIME_TYPE = "audio/mpeg"

SUPPORTED_AUDIO_EXTENSIONS = {".webm", ".mp3", ".mp4", ".mpeg", ".mpga", ".m4a", ".wav"}
SUPPORTED_AUDIO_MIME_TYPES = {
    "audio/webm",
    "video/webm",
    "audio/mpeg",
    "audio/mp3",
    "audio/mp4",
    "audio/m4a",
    "audio/wav",
    "audio/x-wav",
}

LANGUAGE_HINTS = {
    "en": "English",
    "hi": "Hindi",
    "mr": "Marathi",
    "bn": "Bengali",
    "ta": "Tamil",
    "te": "Telugu",
    "gu": "Gujarati",
    "kn": "Kannada",
    "ml": "Malayalam",
    "pa": "Punjabi",
    "ur": "Urdu",
}

VOICE_CHOICES = {
    "alloy",
    "ash",
    "ballad",
    "cedar",
    "coral",
    "echo",
    "fable",
    "marin",
    "nova",
    "onyx",
    "sage",
    "shimmer",
    "verse",
}


class VoiceServiceError(ValueError):
    """Raised for clear user-facing voice errors."""


def transcribe_audio_upload(
    audio_file: FileStorage | None,
    preferred_language: str | None = None,
) -> dict[str, str | None]:
    if audio_file is None or not audio_file.filename:
        raise VoiceServiceError("Please upload a recorded audio file.")

    filename = secure_filename(audio_file.filename)
    suffix = Path(filename).suffix.lower() or _suffix_from_mime(audio_file.mimetype)
    if suffix not in SUPPORTED_AUDIO_EXTENSIONS or audio_file.mimetype not in SUPPORTED_AUDIO_MIME_TYPES:
        raise VoiceServiceError("Unsupported audio format. Please use browser-recorded WebM, MP3, WAV, M4A, MP4, MPEG, or MPGA audio.")

    temporary_path = _save_upload_to_temporary_file(audio_file, suffix)
    try:
        if temporary_path.stat().st_size == 0:
            raise VoiceServiceError("The recording was empty. Please try again.")

        client = _openai_client()
        request = {"model": TRANSCRIPTION_MODEL, "response_format": "json"}
        language_hint = LANGUAGE_HINTS.get(str(preferred_language or "").strip())
        if language_hint:
            request["prompt"] = f"The speaker may be speaking {language_hint} or another Indian language."

        with temporary_path.open("rb") as file:
            transcript_response = client.audio.transcriptions.create(file=file, **request)

        transcript = _read_response_field(transcript_response, "text")
        if not transcript:
            raise VoiceServiceError("No speech was detected. Please try again.")

        return {
            "transcript": transcript.strip(),
            "detectedLanguage": _read_response_field(transcript_response, "language"),
        }
    finally:
        temporary_path.unlink(missing_ok=True)


def generate_speech_audio(
    text: str,
    preferred_language: str | None = None,
    voice: str | None = None,
) -> bytes:
    clean_text = text.strip()
    if not clean_text:
        raise VoiceServiceError("Please provide text to speak.")
    if len(clean_text) > MAX_SPEECH_TEXT_CHARS:
        raise VoiceServiceError("The answer is too long to speak at once.")

    selected_voice = voice if voice in VOICE_CHOICES else "alloy"
    language_instruction = _speech_language_instruction(preferred_language)
    response = _openai_client().audio.speech.create(
        model=SPEECH_MODEL,
        voice=selected_voice,
        input=clean_text,
        instructions=language_instruction,
        response_format=SPEECH_FORMAT,
    )
    return response.content


def _openai_client() -> OpenAI:
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise VoiceServiceError("OpenAI API key is not configured on the server.")
    return OpenAI(api_key=api_key)


def _save_upload_to_temporary_file(audio_file: FileStorage, suffix: str) -> Path:
    total = 0
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temporary_file:
        temporary_path = Path(temporary_file.name)
        while True:
            chunk = audio_file.stream.read(1024 * 1024)
            if not chunk:
                break
            total += len(chunk)
            if total > MAX_AUDIO_BYTES:
                temporary_file.close()
                temporary_path.unlink(missing_ok=True)
                raise VoiceServiceError("The recording is too large. Please record a shorter message.")
            temporary_file.write(chunk)
    return temporary_path


def _suffix_from_mime(mime_type: str | None) -> str:
    return {
        "audio/webm": ".webm",
        "video/webm": ".webm",
        "audio/mpeg": ".mp3",
        "audio/mp3": ".mp3",
        "audio/mp4": ".mp4",
        "audio/m4a": ".m4a",
        "audio/wav": ".wav",
        "audio/x-wav": ".wav",
    }.get(mime_type or "", "")


def _read_response_field(response, field: str) -> str | None:
    if isinstance(response, dict):
        value = response.get(field)
    else:
        value = getattr(response, field, None)
    return str(value).strip() if value else None


def _speech_language_instruction(language: str | None) -> str:
    names = {
        "en": "English",
        "hi": "Hindi",
        "mr": "Marathi",
        "bn": "Bengali",
        "ta": "Tamil",
        "te": "Telugu",
        "gu": "Gujarati",
        "kn": "Kannada",
        "ml": "Malayalam",
        "pa": "Punjabi",
        "ur": "Urdu",
    }
    language_name = names.get(str(language or "").strip(), "the same language as the text")
    return f"Speak naturally and clearly in {language_name}. Do not add extra words."
