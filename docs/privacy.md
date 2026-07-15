# Privacy

GovGuideAI stores account and profile information in its private SQLite database so it can provide personalized government-service and scheme recommendations. Profile data is not used for advertising.

## Profile and account information

Depending on how an account is used, GovGuideAI may store an account email, password hash, historical phone contact, account dates, name, age or date of birth, State or Union Territory, district, occupation, custom occupation, rural or urban location, preferred language, and optional eligibility-related profile fields.

Only authenticated, authorized administrators can access the protected profile dashboard or request an export. Dashboard contacts are masked. Exports are generated in memory only when requested and are never placed in `static/` or a public URL. Export auditing stores only the admin user ID, timestamp, format, and record count—not exported profile values.

Users can edit or delete their profile and can delete their account from the profile page. Account/profile forms cannot grant admin access.

## Information users must not enter

Do not enter Aadhaar numbers, PAN numbers, bank or card details, passwords, PINs, OTPs, authentication tokens, exact home addresses, identity-document images, or other highly sensitive information in a profile or chat.

GovGuideAI does not store plaintext passwords. Historical one-time-code tables remain dormant and preserve only the former hashed challenge data. GovGuideAI does not intentionally store voice recordings. Temporary transcription uploads are deleted after use, and generated speech is returned from memory.

## Guest privacy

Guest mode does not create a permanent user or profile. A random browser-session token maps to a hashed, expiring server record. Guest conversation response IDs remain process-local and do not provide permanent history or cross-device access.

## AI data minimization

The complete user dataset is never sent to the AI. For a logged-in request, GovGuideAI considers only the current user and selects only profile fields relevant to that specific question. Names, contact identifiers, admin roles, password hashes, OTP data, sessions, exports, and other users' records are excluded from the agent context.
