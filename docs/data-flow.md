# Data Flow

1. A visitor opens `/`.
2. If not logged in, Flask redirects to `/login`.
3. A new user creates an account at `/signup`.
4. After login, the app checks whether a profile exists.
5. If no profile exists, the user completes `/profile/setup`.
6. The protected chat page loads the saved profile.
7. The browser sends messages to `/api/chat`.
8. The backend loads the logged-in user's profile and conversation ID.
9. The agent receives the user message plus relevant profile details.
10. The agent may use web search or the local scheme-search tool.
11. The backend saves the latest OpenAI response ID for conversation memory.
12. The frontend displays the answer and the tools used.

Conversation memory is isolated by user ID and conversation ID.
