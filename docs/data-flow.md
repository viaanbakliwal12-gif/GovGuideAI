# Data Flow

## Text Chat

1. A visitor opens `/`.
2. If no browser language is selected, the frontend sends the user to `/language`.
3. If neither logged in nor a guest, Flask redirects to `/login`.
4. A visitor may continue as a guest or verify an email/phone number.
5. After verified login, the app checks whether a profile exists.
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

## OTP Authentication

1. The browser submits an email or a phone number plus country to Flask.
2. Flask validates and normalizes the identifier (`phonenumbers` produces E.164).
3. Rate/cooldown limits are checked by HMAC destination and IP hashes.
4. Flask creates a random six-digit code and stores only a salted/peppered hash.
5. The destination is encrypted in the challenge row and the provider sends the code.
6. The browser receives only a public challenge reference and masked destination.
7. Successful verification invalidates every active code for that destination.
8. An existing identifier reuses its account; otherwise a new user is created.
9. Returning users enter chat, while new verified users complete profile setup.

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
