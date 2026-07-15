# Authentication

## Active website flow

GovGuideAI currently uses email and password authentication. OTP verification is temporarily disabled and may be reintroduced later.

Sign-up validates and normalizes the email, requires a password of 10 to 128 characters containing at least one letter and one number, checks confirmation, prevents duplicate active emails, hashes the password with Werkzeug `scrypt`, creates a secure session, and redirects to profile setup.

Login normalizes the email and checks the stored hash. Every failure returns the same `Incorrect email or password.` message. Completed users go to chat; users without a profile go to profile setup.

Guest mode uses the existing server-side anonymous sessions. CSRF validation and secure cookie settings apply to authentication forms and registered sessions.

## Passwordless historical accounts

The migration does not modify existing account IDs, profiles, roles, contact fields, or historical hashes. An administrator can create a one-time password setup link from `/admin` for an active account whose `password_hash` is empty.

The token secret is random, stored only as a keyed hash, expires after `PASSWORD_SETUP_TOKEN_MINUTES` (30 by default), and is consumed once. Creating a replacement invalidates every earlier unused link. A historical phone-only account chooses a unique email while setting its password.

## Temporarily dormant OTP support

The following modules remain in the repository for possible future reintroduction but are not imported by active routes or startup:

- `app/auth/otp_service.py`
- `app/auth/email_provider.py`
- `app/auth/sms_provider.py`

The historical `otp_challenges` table and identifier columns remain untouched. `/auth/request-code`, `/verify`, and `/auth/resend-code` are not registered routes. No provider configuration is checked, and no OTP values or controls are rendered by the website.
