# Architecture

GovGuideAI keeps the existing Flask application and organizes it into small modules.

## Main Pieces

- `main.py` starts the local Flask server.
- `app/server.py` creates the Flask app, registers route groups, initializes SQLite, and exposes the chat API.
- `app/agent/` contains the OpenAI Responses API setup, system prompt, and response model.
- `app/auth/` contains signup, login, logout, account deletion, and password hashing services.
- `app/profiles/` contains profile setup, editing, deletion, and database access helpers.
- `app/database/` contains SQLite connection setup, table creation, and small dataclasses.
- `app/tools/` contains local tool code, including `search_government_schemes`.
- `app/services/conversation_service.py` keeps per-user conversation response IDs in memory.

## Design Rules

Each file has one clear job. The frontend stays in `templates/` and `static/`. The OpenAI API key stays server-side in `.env`.
