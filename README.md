# GovGuideAI

GovGuideAI is a Flask website for beginner-friendly guidance about Indian government schemes, services, documents, passports, and grievance procedures. It includes local email-only login, guest mode, profile personalization, multilingual UI, text and voice chat, conversation memory, admin tools, and official-source search rules.

## Authentication

Login is intentionally simple and local:

1. The user submits one email address to `POST /login`.
2. Flask validates and normalizes the email.
3. SQLite looks for an active user whose `email` or `verified_email` matches.
4. If no local user matches, Flask creates a passwordless local user automatically.
5. Flask starts the existing secure session immediately.
6. New users go to `/profile/setup`; returning users go to `/chat`.

No password, OTP, magic link, email message, email verification, external identity provider, SMTP configuration, or browser authentication SDK is used.

Existing local records remain compatible: old password hashes, verified contact fields, provider-link columns, profiles, roles, and user IDs are left unchanged. They are simply no longer required for login.

Because possession of an inbox is not checked, knowing an existing account email is sufficient to use that account. This flow is appropriate only where that tradeoff is explicitly intended.

## Install

From the project root in PowerShell:

```powershell
& .\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

If the existing virtual environment is unavailable:

```powershell
python -m venv .venv
& .\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

## Configure

Copy the example file:

```powershell
Copy-Item .env.example .env
```

Environment variables:

- `SECRET_KEY` is required for Flask sessions and CSRF protection.
- `OPENAI_API_KEY` is required for live AI chat, transcription, and speech generation.
- `APP_ENV` and `FLASK_ENV` are optional environment labels; development is the default.
- `DATABASE_PATH` is optional; the default is `govguideai.sqlite3`.
- `PORT` is optional; the default is `5000`.
- `GUEST_SESSION_TTL_HOURS` is optional; the default is `24`.
- `PASSWORD_SETUP_TOKEN_MINUTES` is optional and applies only to the retained legacy admin password-setup tool.
- `ADMIN_EMAIL` is optional and used only by the guarded terminal admin-promotion backup.

No authentication-provider or email-delivery environment variables are required.

The root `.env` is ignored by Git. `.env.example` contains placeholders only.

## Migrate and run

Apply the non-destructive SQLite compatibility migrations:

```powershell
powershell -ExecutionPolicy Bypass -File .\migrate.ps1
```

Startup also applies migrations automatically. Run the website:

```powershell
& .\.venv\Scripts\python.exe main.py
```

Then open `http://127.0.0.1:5000/`.

## Test the email-only login

1. Open the site, choose a language, and continue to Login.
2. Enter a valid email and click **Continue with Email**.
3. Confirm a new email opens `/profile/setup`.
4. Complete the profile, log out, and submit the same email again.
5. Confirm the returning account opens `/chat` and the saved profile remains.
6. Confirm **Continue as Guest**, chat, voice, language selection, profile editing, logout, and admin routes still work as expected.
7. Submit a malformed email and confirm the login page returns a clear validation error without creating a user.

## Automated checks

Run all tests:

```powershell
& .\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Compile the Python source:

```powershell
& .\.venv\Scripts\python.exe -m compileall -q app main.py
```

Import and create the Flask application:

```powershell
& .\.venv\Scripts\python.exe -c "from app.server import create_app; app = create_app(); print(app.url_map)"
```

## Project structure

- `app/auth/routes.py` — email-only login, guest, logout, account deletion, and retained legacy account-setup routes
- `app/auth/services.py` — local user lookup/creation and Flask session helpers
- `templates/login.html` — single-field email login page
- `app/database/` — SQLite connections and non-destructive compatibility migrations
- `app/profiles/`, `app/agent/`, `app/tools/`, `app/voice/` — profiles, chat, tools, and voice features
- `app/admin/` — admin setup, dashboard, exports, and promotion backup

## Privacy and repository safety

SQLite remains the source of truth for accounts and profiles. Login does not send email or contact an external authentication service. `.gitignore` excludes `.env`, databases, exports, logs, virtual environments, caches, and generated audio.
