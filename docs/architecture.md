# Architecture

GovGuideAI keeps the existing Flask application and organizes new features into small modules.

## Main Pieces

- `main.py` starts the local Flask server.
- `app/server.py` creates the Flask app, registers route groups, initializes SQLite, and exposes the chat API.
- `app/agent/` contains the OpenAI Responses API setup, system prompt, tool schema, and response model.
- `app/auth/` contains signup, login, logout, account deletion, and password hashing services.
- `app/profiles/` contains profile setup, editing, deletion, language saving, and database helpers.
- `app/database/` contains SQLite connection setup, table creation, and compatibility updates.
- `app/tools/` contains local tool code, including official-source Scheme Search.
- `app/voice/` contains only voice transcription and speech generation HTTP/service code.
- `app/services/conversation_service.py` keeps per-user conversation response IDs in memory.
- `static/js/i18n.js` contains local UI translations and browser language storage.
- `static/js/chat.js` keeps text chat and shared message sending.
- `static/js/voice.js` keeps MediaRecorder and audio playback controls.

## Design Rules

The frontend stays in `templates/` and `static/`. The OpenAI API key stays server-side in `.env`. Voice mode does not create a separate assistant; it transcribes speech, sends text through the existing `/api/chat` route, and speaks the returned answer.
