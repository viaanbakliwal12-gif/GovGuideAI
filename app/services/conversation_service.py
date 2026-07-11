from __future__ import annotations

from threading import Lock


class ConversationMemory:
    """Keeps OpenAI response IDs per logged-in user and browser conversation."""

    def __init__(self) -> None:
        self._lock = Lock()
        self._response_ids: dict[tuple[int, str], str] = {}

    def get_previous_response_id(self, user_id: int, conversation_id: str) -> str | None:
        with self._lock:
            return self._response_ids.get((user_id, conversation_id))

    def save_response_id(self, user_id: int, conversation_id: str, response_id: str) -> None:
        with self._lock:
            self._response_ids[(user_id, conversation_id)] = response_id

    def clear(self, user_id: int, conversation_id: str | None = None) -> None:
        with self._lock:
            if conversation_id:
                self._response_ids.pop((user_id, conversation_id), None)
                return

            for key in list(self._response_ids):
                if key[0] == user_id:
                    self._response_ids.pop(key, None)
