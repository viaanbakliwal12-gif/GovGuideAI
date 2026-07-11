from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AgentResponse:
    answer: str
    response_id: str
    tools_used: list[str]
