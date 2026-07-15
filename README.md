# GovGuideAI

GovGuideAI is a Flask application for beginner-friendly guidance about Indian government schemes, services, documents, passports, and grievance procedures. It preserves text chat, multilingual UI, voice transcription and speech, guest mode, profile personalization, conversation memory, Web Search, official-source Scheme Search, Word Count, and official-government-source rules.

## Install

From the project root in PowerShell:

```powershell
python -m pip install -r requirements.txt
```

If the project Python is not active:

```powershell
$env:PYTHONPATH = Join-Path $PWD ".venv\Lib\site-packages"
& .\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

## Configure

Copy `.env.example` to `.env`. Required core values are:

```text
OPENAI_API_KEY=
SECRET_KEY=
FLASK_ENV=development
APP_ENV=development
```

For local email and phone OTP testing without providers:

```text
OTP_DEVELOPMENT_MODE=true
```

This creates a fresh random code for every request, stores only its salted/peppered hash in SQLite, and shows the code only on the local verification page under **Development OTP — not for production**. It is never printed to application logs. The app refuses to start with this flag in production or without an explicit development environment.

For real Resend email OTP:

```text
OTP_DEVELOPMENT_MODE=false
EMAIL_PROVIDER=resend
RESEND_API_KEY=
EMAIL_FROM_ADDRESS=GovGuideAI <verified-sender@example.com>
```

For real Twilio Verify phone OTP:

```text
OTP_DEVELOPMENT_MODE=false
SMS_PROVIDER=twilio
TWILIO_ACCOUNT_SID=
TWILIO_AUTH_TOKEN=
TWILIO_VERIFY_SERVICE_SID=
```

Phone numbers keep the country selector, are validated with `phonenumbers`, and are normalized to E.164. See [docs/authentication.md](docs/authentication.md) for security settings and provider behavior.

## Migrate safely

Apply in-place migrations before restarting:

```powershell
powershell -ExecutionPolicy Bypass -File .\migrate.ps1
```

Startup also applies these migrations. They alter the existing database in place; they do not delete or recreate `govguideai.sqlite3`.

## Run and restart

Stop the old Flask process with `Ctrl+C`, then run either:

```powershell
python main.py
```

or the project helper:

```powershell
powershell -ExecutionPolicy Bypass -File .\run_ui.ps1
```

Open `http://127.0.0.1:5000/`.

## First admin

1. Add the intended verified email to `.env`:

   ```text
   ADMIN_EMAIL=admin@example.com
   ```

2. Log in once with that email OTP.
3. Run the guarded one-time command:

   ```powershell
   python -m app.admin.promote_admin admin@example.com
   ```

4. Restart, sign in as that user, and open `http://127.0.0.1:5000/admin`.

Guests and normal users receive HTTP 403. Profile forms cannot change `is_admin`. See [docs/admin.md](docs/admin.md) for the virtual-environment command and security details.

## Admin exports

The admin dashboard provides **Export CSV** and **Export JSON**. Both are CSRF-protected POST requests that repeat the server-side admin check. Records are generated in memory, encoded as UTF-8, sorted by user ID, and returned as private no-store downloads. No export is placed in `static/`, at a public URL, or permanently on disk.

Exports exclude password hashes, OTP hashes and attempts, sessions, authentication tokens, provider references and credentials, API keys, voice recordings, and chat messages. Audit rows contain only admin ID, UTC timestamp, format, and record count.

## Environment variables

Core:

- `OPENAI_API_KEY`
- `SECRET_KEY`
- `FLASK_ENV`
- `APP_ENV`
- optional `DATABASE_PATH`

OTP security:

- `OTP_DEVELOPMENT_MODE`
- `OTP_EXPIRY_MINUTES`
- `OTP_MAX_ATTEMPTS`
- `OTP_RESEND_COOLDOWN_SECONDS`
- `OTP_MAX_REQUESTS_PER_DESTINATION`
- `OTP_MAX_REQUESTS_PER_IP`
- `OTP_PEPPER`
- optional `OTP_DESTINATION_KEY`

Providers and administration:

- `EMAIL_PROVIDER`
- `RESEND_API_KEY`
- `EMAIL_FROM_ADDRESS`
- `SMS_PROVIDER`
- `TWILIO_ACCOUNT_SID`
- `TWILIO_AUTH_TOKEN`
- `TWILIO_VERIFY_SERVICE_SID`
- `ADMIN_EMAIL`
- `GUEST_SESSION_TTL_HOURS`

## Project structure

- `app/admin/` — admin authorization, profile queries, export generation/audit, first-admin command
- `app/agent/` — GovGuideAI Responses API agent, prompt, Web Search and tool activity
- `app/auth/` — OTP flow, providers, validation, legacy password login, guest sessions
- `app/database/` — SQLite connection and safe in-place migrations
- `app/profiles/` — profile setup, editing, deletion and language settings
- `app/tools/` — official-source Scheme Search and Word Count
- `app/voice/` — voice transcription and speech endpoints
- `templates/admin/` — protected admin dashboard UI
- `static/` — local UI styles, chat, voice, authentication and multilingual JavaScript
- `tests/` — OTP, provider, admin/export, privacy and regression tests
- `docs/` — architecture, authentication, admin, database, data-flow and privacy notes

## Privacy and Git safety

SQLite remains the source of truth. User records are not mirrored into public JSON/CSV files, browser JavaScript, logs, Git, or the AI. Only profile fields relevant to the current user's question are sent for personalization.

`.gitignore` excludes `.env`, the current database, `instance/*.db`, `exports/`, CSV files, user export JSON/CSV files, logs, environments, and caches. Existing databases are never automatically deleted or untracked.
