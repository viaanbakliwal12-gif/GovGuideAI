# Data Flow

## Text Chat

1. A visitor opens `/`.
2. If no browser language is selected, the frontend sends the user to `/language`.
3. If neither logged in nor a guest, Flask redirects to `/login`.
4. A visitor may continue as a guest or sign in with email and password.
5. After password login, the app checks whether a profile exists.
6. If no profile exists, the user completes `/profile/setup`.
7. The protected chat page loads the saved profile.
8. The browser sends `message`, `conversationId`, and `selectedLanguage` to `/api/chat`.
9. The backend loads the logged-in user's profile and conversation ID.
10. The existing GovGuideAI agent receives the user message, selected language, and relevant profile details.
11. The agent may use web search or the local scheme-search tool.
12. The backend saves the latest OpenAI response ID for conversation memory.
13. The frontend displays the answer and the tools used.

Conversation memory is isolated by user ID and conversation ID.

For guests, the same memory is isolated by a server-validated anonymous session
hash and conversation ID. It is process-local and expires with the guest session.

## Password Authentication

1. Sign-up submits email, password, and confirmation to Flask.
2. Flask normalizes the email, validates password strength and matching confirmation, and rejects duplicates.
3. Werkzeug hashes the password with `scrypt`; plain text is discarded.
4. Flask establishes the secure session and sends the new user to profile setup.
5. Login compares the supplied password with the stored hash and returns one generic failure message on any mismatch.
6. Returning users enter chat; incomplete users return to profile setup.

## Admin export

1. Flask validates the authenticated session and `is_admin` role.
2. The dashboard queries only active users and joins their optional profile row.
3. A CSRF-protected export POST repeats the admin check.
4. Records are sorted by user ID and serialized to UTF-8 CSV or JSON in memory.
5. The response is a private, no-store attachment; no public file is created.
6. SQLite records only admin ID, timestamp, format, and record count.

## Voice Mode

1. The user presses the microphone button.
2. The browser asks for microphone permission.
3. MediaRecorder records browser audio.
4. The browser sends the temporary audio blob to `/api/voice/transcribe`.
5. Flask validates the upload, writes a temporary file, calls OpenAI speech-to-text, and deletes the temporary file.
6. The browser displays the transcript as the user's message.
7. The transcript is sent through the existing `/api/chat` route.
8. The normal text answer is displayed.
9. If voice responses are enabled, the browser calls `/api/voice/speak`.
10. Flask calls OpenAI text-to-speech and returns playable MP3 audio from memory.
11. The browser plays, stops, or replays the spoken answer.
