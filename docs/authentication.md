# Authentication

## Active website flow

GovGuideAI uses a local email-only login form.

The browser submits one email address to Flask. Flask normalizes it and searches active local users by both `email` and `verified_email`. A matching row is reused without changing its ID, profile, role, password hash, or historical contact fields. When no row matches, Flask creates a passwordless local user.

The existing Flask session is established immediately. Newly created users are redirected to profile setup. Returning users are redirected to chat; the existing chat guard sends any account without a profile to profile setup.

There is no password check, OTP, magic link, email verification, email delivery, provider token, or browser authentication SDK in the active login flow.

Guest mode continues to use server-side anonymous sessions. CSRF validation and secure cookie settings apply to login, guest, account, profile, and admin forms.

## Historical account compatibility

Historical authentication columns and tables are preserved so migrations do not delete or rewrite user data. They are not consulted to authorize the active email-only login.

The optional administrator-created password setup link remains available for historical phone-only accounts that need an email attached. A password created through that tool is retained for compatibility but is not required by the active login form.
