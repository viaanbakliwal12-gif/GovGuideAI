# Authentication and OTP Configuration

## What verification proves

GovGuideAI validates syntax before sending a code and marks an identifier verified only after a successful one-time-code check. Delivery failure is not described as proof that an address or phone number is fake.

At startup the server logs only this safe status summary, never secret values:

```text
Email OTP provider: configured
SMS OTP provider: not configured
Development OTP mode: enabled
```

## Local development OTP

Use this only for local development:

```text
FLASK_ENV=development
APP_ENV=development
OTP_DEVELOPMENT_MODE=true
```

No email or SMS is sent. A fresh random six-digit code is hashed in SQLite and held temporarily in process memory only so the local verification page can show:

```text
Development OTP — not for production
```

The code is not written to application logs. The app refuses to start if the switch is enabled in production or without an explicit development environment. The old `OTP_TEST_MODE` variable is ignored and cannot reveal codes.

## Real email with Resend

```text
OTP_DEVELOPMENT_MODE=false
EMAIL_PROVIDER=resend
RESEND_API_KEY=
EMAIL_FROM_ADDRESS=GovGuideAI <verified-sender@example.com>
```

The sending address or domain must be verified in Resend. GovGuideAI checks for a successful provider response containing a delivery ID and safely classifies authentication, sender, rejection, rate-limit, network, and provider-availability errors. Provider details remain server-side. Older deployments using SendGrid remain compatible through `EMAIL_PROVIDER=sendgrid`, `EMAIL_API_KEY`, and `EMAIL_FROM_ADDRESS`.

## Real phone with Twilio Verify

Create a Twilio Verify Service, then configure:

```text
OTP_DEVELOPMENT_MODE=false
SMS_PROVIDER=twilio
TWILIO_ACCOUNT_SID=
TWILIO_AUTH_TOKEN=
TWILIO_VERIFY_SERVICE_SID=
```

Phone input is parsed with `phonenumbers`, validated for the selected country, and normalized to E.164. Twilio Verify generates and delivers the code and checks the submitted code. GovGuideAI still records expiry, attempts, cooldown/rate limits, one-time use, and provider challenge state without storing the Twilio code. When possible, an earlier active Twilio verification is canceled before a replacement is sent.

## OTP security settings

Recommended production values:

```text
FLASK_ENV=production
APP_ENV=production
OTP_DEVELOPMENT_MODE=false
OTP_EXPIRY_MINUTES=10
OTP_MAX_ATTEMPTS=5
OTP_RESEND_COOLDOWN_SECONDS=60
OTP_MAX_REQUESTS_PER_DESTINATION=5
OTP_MAX_REQUESTS_PER_IP=20
OTP_PEPPER=<separate long random secret>
OTP_DESTINATION_KEY=<Fernet key>
```

Generate secrets without placing them in source control:

```powershell
python -c "import secrets; print(secrets.token_urlsafe(48))"
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

If `OTP_DESTINATION_KEY` is omitted, GovGuideAI derives one from `SECRET_KEY`. Changing either key while challenges are active makes those short-lived challenges unreadable, so users must request a new code.

OTP requests are limited by one-way destination and IP hashes. Codes expire, have limited attempts, obey resend cooldown, are invalidated on replacement, and are invalidated after successful use. SQLite stores a salted/peppered hash for locally generated codes, never the plaintext code.

## Guest expiry

`GUEST_SESSION_TTL_HOURS=24` controls server-record lifetime. Guest sessions do not create a user or profile and retain only temporary, process-local conversation memory.
