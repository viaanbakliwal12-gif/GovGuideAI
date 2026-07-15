# Authentication and Guest Configuration

## What Verification Proves

GovGuideAI validates syntax before sending a code, then treats the identifier as
verified only after the correct one-time code is entered. Providers may report
an undeliverable destination, but an application generally cannot know with
certainty that an address or phone number exists before delivery. A delayed code
is not described as proof that the destination is fake.

## Email Providers

Supported values:

- `EMAIL_PROVIDER=resend`
- `EMAIL_PROVIDER=sendgrid`

Both require:

```text
EMAIL_API_KEY=
EMAIL_FROM_ADDRESS=
```

The from address/domain must be authorized in the selected provider.

## SMS Provider

Twilio Programmable Messaging is supported:

```text
SMS_PROVIDER=twilio
SMS_ACCOUNT_ID=
SMS_API_KEY=
SMS_SENDER_ID=
```

`SMS_API_KEY` is the Twilio auth token for this adapter. `SMS_SENDER_ID` may be
an authorized Twilio number or supported sender ID. Numbers are parsed and
validated with `phonenumbers`, then stored in E.164 form.

## OTP Security

Recommended production values:

```text
APP_ENV=production
OTP_TEST_MODE=false
OTP_EXPIRY_MINUTES=10
OTP_MAX_ATTEMPTS=5
OTP_RESEND_COOLDOWN_SECONDS=60
OTP_MAX_REQUESTS_PER_DESTINATION=5
OTP_MAX_REQUESTS_PER_IP=20
OTP_PEPPER=<separate long random secret>
OTP_DESTINATION_KEY=<Fernet key>
```

Generate values without placing them in source control:

```powershell
$env:PYTHONPATH = Join-Path $PWD ".venv\Lib\site-packages"
$python = Join-Path $PWD ".uv-python\cpython-3.11.15-windows-x86_64-none\python.exe"
& $python -c "import secrets; print(secrets.token_urlsafe(48))"
& $python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

If `OTP_DESTINATION_KEY` is omitted, GovGuideAI derives an encryption key from
`SECRET_KEY`. A separate production key is preferred. Changing that key while
challenges are active makes those short-lived challenges unreadable, requiring
users to request a new code.

## Development Test Mode

For local-only delivery testing:

```text
APP_ENV=development
OTP_TEST_MODE=true
```

No email or SMS is sent. The code is held only in process memory and displayed
in a clearly labelled development notice on the verification page. It is never
printed to application logs or stored as plaintext in SQLite. GovGuideAI refuses
to start if this mode is enabled with `APP_ENV=production`.

## Guest Expiry

`GUEST_SESSION_TTL_HOURS=24` controls the server-record lifetime. The guest
cookie is a non-permanent browser-session cookie, so closing the browser also
ends normal access. Expired server records are pruned when new guests start.
