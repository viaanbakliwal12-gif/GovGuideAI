# GovGuideAI

GovGuideAI is a Flask website for beginner-friendly guidance about Indian government schemes, services, documents, passports, and grievance procedures. It includes Supabase email OTP login, guest mode, profile personalization, multilingual UI, text and voice chat, conversation memory, and official-source search rules.

> This repository currently runs Flask, despite some earlier project descriptions referring to FastAPI. `main.py` loads the Flask factory in `app/server.py`; the Supabase endpoints are implemented in that existing application so no unrelated framework migration is required.

## Authentication

The website uses the official `@supabase/supabase-js` v2 browser client. Supabase generates, sends, and verifies every six-digit email OTP. GovGuideAI does not generate, hash, log, or store OTP values.

After Supabase verifies the OTP, the browser sends the returned access token to `POST /api/auth/session`. The server validates that token against the project's Supabase Auth `/auth/v1/user` endpoint before linking it to the existing local user/profile record and creating the GovGuideAI session cookie. A browser-provided email or user ID is never trusted by itself.

`GET /api/auth/config` exposes exactly these public browser values:

- `SUPABASE_URL`
- `SUPABASE_ANON_KEY`

It does not expose `SECRET_KEY`, `OPENAI_API_KEY`, service-role keys, or any other environment values. The app rejects `sb_secret_` and legacy JWT keys whose role is `service_role`.

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

Copy the example file, then fill in private/local values:

```powershell
Copy-Item .env.example .env
```

Required authentication settings:

```dotenv
SUPABASE_URL=https://your-project-ref.supabase.co
SUPABASE_ANON_KEY=your_supabase-publishable-or-anon-key
```

Use only the public publishable key (`sb_publishable_...`) or legacy anon key. Never use a service-role key or `sb_secret_...` key. `SECRET_KEY` is also required by the Flask application, and `OPENAI_API_KEY` is required for live AI chat.

The root `.env` is ignored by Git through the `.env` and `.env.*` rules in `.gitignore`; `.env.example` is the only exception and contains placeholders only.

## Supabase dashboard setup

1. Open the Supabase project and go to **Authentication → Providers → Email**. Enable the Email provider.
2. Go to **Authentication → Email Templates → Magic Link** (shown as the Magic Link/OTP template in some dashboard versions).
3. Make the email body include the six-digit token variable, for example:

   ```html
   <h2>Your GovGuideAI login code</h2>
   <p>Enter this code in GovGuideAI: <strong>{{ .Token }}</strong></p>
   ```

   Using `{{ .Token }}` is what makes `signInWithOtp` send a code instead of only a magic link.
4. Under **Authentication → URL Configuration**, set the Site URL to the deployed GovGuideAI origin. For local testing, use `http://127.0.0.1:5000`.
5. Keep the OTP request interval at 60 seconds or longer. The website's Resend Code button uses the same 60-second cooldown.
6. For production delivery, configure a supported custom SMTP provider in **Authentication → SMTP Settings** and test delivery before launch.

No Supabase database table, service-role key, Auth admin API, or manually generated OTP is needed by this integration.

## Migrate and run

Apply the non-destructive SQLite migration that adds the Supabase user ID link:

```powershell
powershell -ExecutionPolicy Bypass -File .\migrate.ps1
```

Startup also applies migrations automatically. Run the website:

```powershell
& .\.venv\Scripts\python.exe main.py
```

Then open `http://127.0.0.1:5000/`.

## Test the OTP flow in the website

1. Open `http://127.0.0.1:5000/`, choose a language, and continue to Login.
2. Enter a real email inbox and click **Send OTP**.
3. Confirm that the six-digit field, **Verify OTP**, **Change Email**, and disabled **Resend Code** countdown appear.
4. Copy the six-digit code from the Supabase email, paste it into the field, and press Enter or click **Verify OTP**.
5. A new user should open `/profile/setup`; a user with a completed GovGuideAI profile should open `/chat` (or the originally requested protected page).
6. Refresh the page and confirm the Supabase browser session is restored without requesting another code.
7. Click **Logout** and confirm the site returns to `/login` and does not immediately sign back in.
8. Try a malformed email, a wrong code, an expired code, and repeated sends. Confirm that the page shows clear validation, invalid/expired, network, and rate-limit messages.
9. Open `/profile` in a signed-out/private browser. Confirm it redirects to `/login?next=/profile`.

If the email contains only a link instead of a six-digit code, update the Supabase Magic Link/OTP email template to include `{{ .Token }}`.

## Automated tests and startup checks

Run all tests:

```powershell
& .\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Compile the Python source:

```powershell
& .\.venv\Scripts\python.exe -m compileall -q app main.py
```

Start the application for a local health check:

```powershell
& .\.venv\Scripts\python.exe main.py
```

Then visit `http://127.0.0.1:5000/health`; it should return `{"status":"ok"}`.

## Project structure

- `app/auth/supabase.py` — safe public configuration and server-side Supabase access-token validation
- `app/auth/routes.py` — login, configuration, session exchange, guest, logout, and legacy account setup routes
- `app/auth/services.py` — local user/profile linking and GovGuideAI sessions
- `static/js/auth.js` — official Supabase client initialization, OTP UI, session restore, guards, and logout
- `templates/login.html` — responsive email OTP login page
- `app/database/` — SQLite connections and non-destructive migrations
- `app/profiles/`, `app/agent/`, `app/tools/`, `app/voice/` — existing profiles, chat, tools, and voice features

## Privacy and repository safety

SQLite remains the source of truth for GovGuideAI profiles. Supabase Auth is the identity provider. Access tokens and OTP codes are not written to the database or logs. `.gitignore` excludes `.env`, databases, exports, logs, virtual environments, caches, and generated audio.
