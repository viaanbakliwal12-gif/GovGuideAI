# GovGuideAI

GovGuideAI is a Flask application for beginner-friendly guidance about Indian government schemes, services, documents, passports, and grievance procedures. It includes text chat, multilingual UI, voice transcription and speech, guest mode, profile personalization, conversation memory, Web Search, official-source Scheme Search, Word Count, and official-government-source rules.

## Authentication status

OTP verification is **temporarily disabled** and may be added back later. The active website authentication flow uses email and password only. There are no verification-code pages, phone-login controls, delivery-provider checks, or development-code notices in the website.

New passwords are hashed with Werkzeug's memory-hard `scrypt` format. Plain-text passwords are never stored or logged. Historical OTP tables and provider modules remain dormant so an eventual reintroduction does not require destructive database changes; they are not imported by the active routes or startup path.

## Install

From the project root in PowerShell:

```powershell
python -m pip install -r requirements.txt
```

Or use the project virtual environment directly:

```powershell
& .\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

## Configure

Copy `.env.example` to `.env`. Keep real secrets private:

```text
OPENAI_API_KEY=
SECRET_KEY=
FLASK_ENV=development
APP_ENV=development
PASSWORD_SETUP_TOKEN_MINUTES=30
```

Email/SMS provider and development-OTP variables are not used by the active application.

## Migrate safely

Apply in-place migrations before restarting:

```powershell
powershell -ExecutionPolicy Bypass -File .\migrate.ps1
```

Migration 4 adds only the hashed, expiring `password_setup_tokens` table used to recover passwordless legacy accounts. Startup also applies migrations. They preserve the existing `govguideai.sqlite3`, user IDs, profiles, admin roles, and historical authentication tables.

## Run and restart

Stop an old Flask process with `Ctrl+C`, then run:

```powershell
python main.py
```

Or:

```powershell
powershell -ExecutionPolicy Bypass -File .\run_ui.ps1
```

Open `http://127.0.0.1:5000/`.

## Website sign-up and login

At `/signup`, enter an email, a password of at least 10 characters containing a letter and a number, and the matching confirmation. A successful sign-up creates a secure session and opens profile setup. Saving the profile opens chat.

At `/login`, enter the saved email and password. Incorrect credentials always show the same generic message. Completed users go to chat; incomplete users go to profile setup. Guest mode remains available on both pages.

## Passwordless legacy accounts

No shared or default password is assigned. An administrator can open `/admin` and select **Create setup link** beside a passwordless account. The one-time link:

- expires after 30 minutes by default;
- is invalidated when a replacement is created;
- stores only a keyed hash of its secret;
- stops working after one use;
- lets a phone-only legacy user choose an email before setting a password.

The full link appears only on the administrator result page and must be shared privately with the account owner.

## First admin through the website

1. Create or log in to a password account in local development.
2. Open `http://127.0.0.1:5000/admin/setup`.
3. Type the displayed confirmation phrase and click **Make this account the administrator**.
4. Continue at `http://127.0.0.1:5000/admin`.

The setup page is disabled in production, for guests, for passwordless accounts, and permanently after the first administrator exists. The guarded `python -m app.admin.promote_admin` command remains an optional recovery backup.

## Admin exports

The admin dashboard keeps the searchable, sortable, paginated user/profile dataset and CSV/JSON browser downloads. Exports are generated in memory, encoded as UTF-8, returned with private no-store headers, and audited with administrator ID, UTC time, format, and record count.

Exports exclude password hashes, historical authentication hashes, setup tokens, sessions, provider credentials, API keys, voice recordings, and chat messages.

## Tests

```powershell
& .\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

## Project structure

- `app/auth/routes.py` — active email/password, guest, logout, and password-setup website routes
- `app/auth/services.py` — password hashing, account creation, sessions, and authentication
- `app/auth/password_setup.py` — admin-authorized one-time legacy-account setup links
- `app/auth/otp_service.py`, `email_provider.py`, `sms_provider.py` — dormant future-use code, not part of the active website
- `app/admin/` — protected setup, dashboard, legacy recovery links, exports, and audits
- `app/database/` — SQLite connections and non-destructive migrations
- `app/profiles/`, `app/agent/`, `app/tools/`, `app/voice/` — existing profiles, chat, tools, and voice features

## Privacy and Git safety

SQLite remains the source of truth. User records are not mirrored into public files, browser JavaScript, logs, Git, or the AI. `.gitignore` excludes `.env`, databases, exports, logs, virtual environments, and caches.
