from __future__ import annotations


def count_words(text: str) -> int:
    """Small helper kept for the old word-count behaviour, but not exposed as an agent tool."""

    return len(text.split())
