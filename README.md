# GovGuideAI

GovGuideAI is a Flask application that helps Indian citizens understand government schemes, services, passport processes, required documents, and grievance procedures.

It keeps OpenAI API calls on the server, uses the existing GovGuideAI agent, and personalizes answers with the logged-in user's saved profile.

## Main Features

- Text chat with the existing OpenAI Responses API agent
- Multilingual voice input and spoken answers
- First-time language selection before login
- Local UI translations in `static/js/i18n.js`
- Login, sign-up, profile setup, and profile editing
- Simplified occupation-based profile
- Conversation memory per user and browser conversation
- Official-source guidance with Web Search, Scheme Search, and Word Count

## Install

```powershell
pip install -r requirements.txt
```

## Run

```powershell
powershell -ExecutionPolicy Bypass -File .\run_ui.ps1
```

Then open:

```text
http://127.0.0.1:5000/
```

## Environment

Create a `.env` file with:

```text
OPENAI_API_KEY=your_openai_api_key_here
FLASK_SECRET_KEY=change-this-for-local-use
```

Never put the OpenAI API key in HTML or JavaScript.

## Project Structure

- `app/agent/` - GovGuideAI Responses API agent and prompt
- `app/auth/` - login, sign-up, logout, account deletion
- `app/database/` - SQLite connection, table creation, compatibility updates
- `app/profiles/` - profile setup, editing, language saving
- `app/tools/` - Scheme Search and Word Count helpers
- `app/voice/` - voice transcription and speech generation endpoints
- `static/js/chat.js` - text chat and shared message sending
- `static/js/voice.js` - MediaRecorder, transcription, playback controls
- `static/js/i18n.js` - local UI translations and language storage
- `templates/` - Flask HTML templates
- `docs/` - architecture, data flow, database, and privacy notes

## Voice Flow

Browser microphone recording stays user-initiated. The browser records audio with MediaRecorder, sends the temporary audio file to `/api/voice/transcribe`, sends the returned transcript through the existing `/api/chat` route, then requests spoken audio from `/api/voice/speak`.

Audio is not intentionally stored by GovGuideAI. Temporary uploaded files are deleted after transcription, and generated speech is returned from memory.

## Language Flow

The first-time language screen saves the selected language in browser localStorage. After login or profile setup, the selected language is saved in the user's profile. The selected language is sent with every chat request and is used for UI labels, greeting text, transcription hints, agent answers, and spoken responses.

If a translation key is missing, the UI falls back to English.

## Profile Simplification

The app now uses one stable `occupation` value instead of separate student, farmer, and employment-status fields. Existing old SQLite columns are preserved for compatibility but are no longer used in forms, agent context, or Scheme Search parameters.

Old missing occupation values are mapped safely when possible:

- student status -> `student`
- farmer status -> `farmer`
- unemployed employment status -> `unemployed`

Existing accounts and profiles are not deleted.
