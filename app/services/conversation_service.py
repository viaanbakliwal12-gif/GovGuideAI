from __future__ import annotations

from threading import Lock


class ConversationMemory:
    """Keeps response IDs per authenticated or anonymous session and conversation."""

    def __init__(self) -> None:
        self._lock = Lock()
        self._response_ids: dict[tuple[str, str], str] = {}

    def get_previous_response_id(self, subject_key: str, conversation_id: str) -> str | None:
        with self._lock:
            return self._response_ids.get((subject_key, conversation_id))

    def save_response_id(self, subject_key: str, conversation_id: str, response_id: str) -> None:
        with self._lock:
            self._response_ids[(subject_key, conversation_id)] = response_id

    def clear(self, subject_key: str, conversation_id: str | None = None) -> None:
        with self._lock:
            if conversation_id:
                self._response_ids.pop((subject_key, conversation_id), None)
                return

            for key in list(self._response_ids):
                if key[0] == subject_key:
                    self._response_ids.pop(key, None)
