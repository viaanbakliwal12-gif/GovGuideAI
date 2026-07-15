# Secure Admin Dashboard

## Create the first admin through the website

1. Use local development settings:

   ```text
   FLASK_ENV=development
   APP_ENV=development
   ```

2. Create or log in to an email/password account through the website.
3. Open `http://127.0.0.1:5000/admin/setup`, or click **Administrator Setup** in the website navigation/profile-setup page.
4. Confirm the masked signed-in account, type `MAKE ME ADMIN`, and click **Make this account the administrator**.
5. The website redirects to `/admin` and permanently records first-admin completion.

The route requires a logged-in password account. It returns access denied for guests and passwordless accounts, returns not found in production, and becomes not found permanently after setup. The promotion is performed in a locked SQLite transaction so two users cannot both become the first admin.

## Optional terminal recovery backup

The normal workflow is the website. If recovery is ever necessary, set `ADMIN_EMAIL` and use the existing guarded command:

```powershell
.\.venv\Scripts\python.exe -m app.admin.promote_admin admin@example.com
```

The supplied normalized email must exactly match `ADMIN_EMAIL`, must belong to an active password account, and is displayed only in masked form.

## Passwordless legacy account setup

For a dashboard row marked **Password setup needed**, click **Create setup link**. Share the displayed one-time URL privately with the account owner. The secret is stored only as a keyed hash, expires after the configured interval, and is invalid after one successful use. A phone-only historical account must choose a unique email on that page.

## Open the dashboard

Restart the application, sign in as the promoted user, and open:

```text
http://127.0.0.1:5000/admin
```

Guests and normal users receive HTTP 403. Every admin route verifies the server-side session and `is_admin` role. Profile editing cannot change this role.

The dashboard shows total active users, completed profiles, active tracked guest sessions, and recent accounts. The main table supports search, allow-listed sorting, and 10/25/50/100-row pagination. Deleted users are excluded. Contacts are masked on screen.

## Export

Use **Export CSV** or **Export JSON** on the dashboard. The page immediately shows download-preparation status and the browser receives the attachment. Both actions are CSRF-protected POST requests and repeat the admin authorization check. Files are created in memory, downloaded with `Cache-Control: no-store`, and are not retained on disk or exposed through `static/`.

Exports use UTF-8, ISO timestamps, stable user-ID ordering, and exclude passwords, hashes, OTPs, attempts, session IDs, provider references, tokens, API keys, credentials, voice recordings, and chat messages. CSV also neutralizes spreadsheet-formula prefixes in text cells.

Each requested export adds one `export_audit_log` row with admin ID, UTC timestamp, format, and record count only.
