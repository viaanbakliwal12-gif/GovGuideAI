# GovGuideAI

GovGuideAI is a Flask application that helps Indian citizens understand government schemes, services, passport processes, required documents, and grievance procedures.

It keeps OpenAI API calls on the server, uses the existing GovGuideAI agent, and personalizes answers with the logged-in user's saved profile.

## Main Features

- Text chat with the existing OpenAI Responses API agent
- Multilingual voice input and spoken answers
- First-time language selection before login
- Local UI translations in `static/js/i18n.js`
- Login, sign-up, profile setup, and profile editing
- Guest access without mandatory personal details or a database user account
- Email or international phone-number login with 6-digit OTP verification
- Simplified occupation-based profile
- Conversation memory per user and browser conversation
- Official-source guidance with Web Search, Scheme Search, and Word Count

## Install

```powershell
& "$HOME\.local\bin\uv.exe" pip install --python .\.venv\Scripts\python.exe -r requirements.txt
```

Apply the safe in-place SQLite migration (startup also runs it automatically):

```powershell
powershell -ExecutionPolicy Bypass -File .\migrate.ps1
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

Copy `.env.example` to `.env`, then configure at least:

```text
OPENAI_API_KEY=your_openai_api_key_here
SECRET_KEY=replace-with-a-long-random-value
APP_ENV=development
OTP_TEST_MODE=true
```

`OTP_TEST_MODE=true` is only for local development. The code is shown in a
clearly labelled development notice on the verification page; it is never
printed to logs. The app refuses to start with test mode enabled when
`APP_ENV=production`.

For real email delivery, set `EMAIL_PROVIDER` to `resend` or `sendgrid`, plus
`EMAIL_API_KEY` and `EMAIL_FROM_ADDRESS`. For real SMS delivery, set
`SMS_PROVIDER=twilio`, `SMS_ACCOUNT_ID`, `SMS_API_KEY`, and `SMS_SENDER_ID`.
Keep every API key server-side; never put provider credentials in HTML or
JavaScript. See `docs/authentication.md` for the full configuration.

For Render, use `pip install -r requirements.txt` as the build command and
`gunicorn main:app --bind 0.0.0.0:$PORT` as the start command. Configure
`OPENAI_API_KEY`, `SECRET_KEY`, `APP_ENV=production`, OTP security values, and
the selected email/SMS provider values in the Render environment. Keep
`OTP_TEST_MODE=false` in production.

## Project Structure

- `app/agent/` - GovGuideAI Responses API agent and prompt
- `app/auth/` - guest sessions, legacy password login, OTP auth, providers, validation
- `app/database/` - SQLite connection, table creation, compatibility updates
- `app/profiles/` - profile setup, editing, language saving
- `app/tools/` - Scheme Search and Word Count helpers
- `app/voice/` - voice transcription and speech generation endpoints
- `static/js/chat.js` - text chat and shared message sending
- `static/js/voice.js` - MediaRecorder, transcription, playback controls
- `static/js/i18n.js` - local UI translations and language storage
- `templates/` - Flask HTML templates
- `docs/` - architecture, data flow, database, and privacy notes

## Guest Sessions

Guest mode creates a random anonymous browser-session token and stores only its
HMAC hash in `guest_sessions`; it does not create a row in `users`. The Flask
cookie is HttpOnly and non-permanent, while the server record expires after 24
hours by default. Guest conversation response IDs stay only in process memory,
so there is no permanent profile, saved history, or cross-device access.

Guests retain text chat, voice input, spoken answers, language selection, Web
Search, Scheme Search, Word Count, and official-source rules. Details shared in
conversation can influence that temporary response chain without becoming a
saved profile.

## Verification Semantics

Email and phone formats are validated before delivery. A successful OTP proves
that the user controlled the destination during verification; it cannot prove
in advance that an address or number exists, and delivery delays are not treated
as evidence that a destination is fake.

Phone input is parsed with `phonenumbers`, validated for the selected country,
and stored in E.164 form such as `+919876543210`. OTP values are generated with
`secrets`, stored only as salted hashes combined with a server secret, expire,
have attempt/resend limits, and are invalidated after use or replacement.

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
