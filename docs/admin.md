# Secure Admin Dashboard

## Promote the first admin

1. Put the intended email in `.env` without hardcoding it in source:

   ```text
   ADMIN_EMAIL=admin@example.com
   ```

2. Log in once with that email OTP so the account has a verified email.
3. From the project root, run the one-time guarded command:

   ```powershell
   python -m app.admin.promote_admin admin@example.com
   ```

If `python` is not the project virtual environment, use:

```powershell
$env:PYTHONPATH = Join-Path $PWD ".venv\Lib\site-packages"
& .\.venv\Scripts\python.exe -m app.admin.promote_admin admin@example.com
```

The supplied normalized email must exactly match `ADMIN_EMAIL`, must belong to an active verified user, and is displayed only in masked form by the command. Re-running the command is safe and idempotent.

## Open the dashboard

Restart the application, sign in as the promoted user, and open:

```text
http://127.0.0.1:5000/admin
```

Guests and normal users receive HTTP 403. Every admin route verifies the server-side session and `is_admin` role. Profile editing cannot change this role.

The table supports search, allow-listed sorting, and 10/25/50/100-row pagination. Deleted users are excluded. Contacts are masked on screen.

## Export

Use **Export CSV** or **Export JSON** on the dashboard. Both actions are CSRF-protected POST requests and repeat the admin authorization check. Files are created in memory, downloaded with `Cache-Control: no-store`, and are not retained on disk or exposed through `static/`.

Exports use UTF-8, ISO timestamps, stable user-ID ordering, and exclude passwords, hashes, OTPs, attempts, session IDs, provider references, tokens, API keys, credentials, voice recordings, and chat messages. CSV also neutralizes spreadsheet-formula prefixes in text cells.

Each requested export adds one `export_audit_log` row with admin ID, UTC timestamp, format, and record count only.
