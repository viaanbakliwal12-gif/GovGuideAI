from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AgentResponse:
    answer: str
    response_id: str
    tools_used: list[str]


@dataclass(frozen=True)
class AgentActivity:
    """A tool action that has actually started during an agent response."""

    tool: str
    queries: tuple[str, ...] = ()
    urls: tuple[str, ...] = ()
