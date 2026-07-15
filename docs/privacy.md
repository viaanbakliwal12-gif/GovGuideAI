# Privacy

GovGuideAI stores only basic profile details needed for government-service and scheme personalization.

## Collected

- Verified email (when an account uses email)
- Verified E.164 phone number (when an account uses phone)
- Password hash
- Created date
- Last login date
- Name
- Age or date of birth
- State or Union Territory
- District
- Occupation
- Optional custom occupation text when occupation is `other`
- Rural or urban location type
- Preferred language
- Optional eligibility-related details such as income range, disability status, marital status, gender, and social category

## Not Collected

- Aadhaar number
- PAN number
- Bank details
- Plain-text OTPs
- Exact home address
- Plain-text passwords
- Identity documents
- Voiceprints
- Audio for identification

## Voice

Voice recording starts only when the user presses the microphone button. The app shows a visible recording indicator while recording is active.

Recorded audio is sent to the Flask backend for transcription and is not intentionally stored by GovGuideAI. Temporary audio files are deleted after transcription. Generated speech is returned to the browser from memory and is not permanently saved.

Profile information and language choice are used only to personalize government-service and scheme guidance. They are not used for advertising or unrelated analytics.

## Verification and Guest Privacy

Verification challenges contain a one-way destination hash, encrypted delivery
destination, salted/peppered OTP hash, expiry, counters, and a one-way IP hash.
Plaintext codes are not stored or logged. Development-only codes appear only on
the local verification page when explicitly enabled outside production.

Guests do not provide an email, phone number, name, or profile. A random token
in an HttpOnly browser-session cookie maps to a hashed, expiring server record.
Guest chat history is not written to the database and has no cross-device access.
