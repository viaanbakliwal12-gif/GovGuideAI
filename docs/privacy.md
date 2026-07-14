# Privacy

GovGuideAI stores only basic profile details needed for government-service and scheme personalization.

## Collected

- Email
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
- OTPs
- Exact home address
- Plain-text passwords
- Identity documents
- Voiceprints
- Audio for identification

## Voice

Voice recording starts only when the user presses the microphone button. The app shows a visible recording indicator while recording is active.

Recorded audio is sent to the Flask backend for transcription and is not intentionally stored by GovGuideAI. Temporary audio files are deleted after transcription. Generated speech is returned to the browser from memory and is not permanently saved.

Profile information and language choice are used only to personalize government-service and scheme guidance. They are not used for advertising or unrelated analytics.
