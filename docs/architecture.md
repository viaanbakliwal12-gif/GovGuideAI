# Architecture

GovGuideAI keeps the existing Flask application and organizes new features into small modules.

## Main Pieces

- `main.py` starts the local Flask server.
- `app/config.py` loads the project `.env` before services inspect configuration and classifies development/production safely.
- `app/server.py` creates the Flask app, registers route groups, initializes SQLite, and exposes the chat API.
- `app/agent/` contains the OpenAI Responses API setup, system prompt, tool schema, and response model.
- `app/auth/` contains active local email-only login, retained legacy password
  setup links, guest sessions, validation, logout, and account deletion.
- `app/admin/` contains admin authorization, one-time website setup, summary/profile queries, in-memory exports, export auditing, and an optional backup promotion command.
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

Guest and logged-in sessions share the same chat, agent, tool, language, and
voice paths. Only identity/profile lookup differs. The browser submits account
email only to Flask over the normal form route; it never receives stored hashes
or server credentials.

`app/security.py` supplies per-session CSRF tokens and secure cookie defaults.
All state-changing forms and browser API requests send the CSRF token.

The admin blueprint uses the same CSRF layer plus an independent server-side
`is_admin` check on every route. Export content is built only for an authorized
request and never written under `static/`.

`/admin/setup` is a development-only bootstrap route. It requires a logged-in
local email account, succeeds only while no first-admin completion record exists,
and atomically writes both the role and permanent setup marker.
