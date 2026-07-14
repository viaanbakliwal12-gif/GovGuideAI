from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from app.agent import AgentActivity, AgentResponse, GovernmentHelpAgent
from app.database.session import get_connection
from app.server import _chat_status_for_activity, create_app


def _response(response_id: str, answer: str, output: list) -> SimpleNamespace:
    return SimpleNamespace(id=response_id, output_text=answer, output=output)


def _completed(response: SimpleNamespace) -> SimpleNamespace:
    return SimpleNamespace(type="response.completed", response=response)


class _FakeResponses:
    def __init__(self, streams: list[list[SimpleNamespace]]) -> None:
        self.streams = streams
        self.requests: list[dict] = []

    def create(self, **request):
        self.requests.append(request)
        return iter(self.streams.pop(0))


def _agent_with_streams(*streams: list[SimpleNamespace]) -> tuple[GovernmentHelpAgent, _FakeResponses]:
    responses = _FakeResponses(list(streams))
    agent = object.__new__(GovernmentHelpAgent)
    agent.client = SimpleNamespace(responses=responses)
    return agent, responses


class AgentActivityTests(unittest.TestCase):
    def test_simple_response_has_no_tool_activity(self) -> None:
        agent, responses = _agent_with_streams(
            [_completed(_response("response-1", "Hello!", []))]
        )

        events = list(agent.respond_events("Hello"))

        self.assertEqual(events, [AgentResponse("Hello!", "response-1", [])])
        self.assertTrue(responses.requests[0]["stream"])

    def test_web_search_activity_is_emitted_from_real_stream_event(self) -> None:
        action = SimpleNamespace(
            query="today's weather in Delhi",
            queries=None,
            url=None,
            sources=None,
        )
        web_item = SimpleNamespace(type="web_search_call", action=action)
        final_response = _response("response-2", "It is sunny.", [web_item])
        agent, _ = _agent_with_streams(
            [
                SimpleNamespace(type="response.output_item.added", item=web_item),
                SimpleNamespace(type="response.web_search_call.searching"),
                _completed(final_response),
            ]
        )

        events = list(agent.respond_events("What is the weather?"))

        self.assertEqual(events[0].tool, "web_search")
        self.assertEqual(events[0].queries, ("today's weather in Delhi",))
        self.assertEqual(events[-1].tools_used, ["Web Search"])

    def test_scheme_activity_is_emitted_before_local_tool_followup(self) -> None:
        function_item = SimpleNamespace(
            type="function_call",
            name="search_government_schemes",
            arguments='{"query":"student scholarships"}',
            call_id="call-1",
        )
        agent, responses = _agent_with_streams(
            [
                SimpleNamespace(type="response.output_item.added", item=function_item),
                _completed(_response("response-tool", "", [function_item])),
            ],
            [_completed(_response("response-final", "Two schemes match.", []))],
        )

        events = list(agent.respond_events("Scholarships for me", profile={"occupation": "student"}))

        self.assertEqual(events[0], AgentActivity("search_government_schemes"))
        self.assertEqual(events[-1].tools_used, ["Scheme Search"])
        self.assertEqual(responses.requests[1]["previous_response_id"], "response-tool")


class ChatStatusTests(unittest.TestCase):
    def test_no_tool_and_generic_web_statuses(self) -> None:
        self.assertEqual(_chat_status_for_activity(AgentActivity("none"), "Hello"), "thinking")
        self.assertEqual(
            _chat_status_for_activity(
                AgentActivity("web_search", queries=("today's weather in Delhi",)),
                "What is the weather?",
            ),
            "web_search",
        )

    def test_official_search_statuses(self) -> None:
        self.assertEqual(
            _chat_status_for_activity(AgentActivity("search_government_schemes"), "Schemes for me"),
            "official_sources",
        )


class ChatStreamRouteTests(unittest.TestCase):
    def test_route_starts_thinking_then_reports_real_tool_activity(self) -> None:
        class FakeAgent:
            @staticmethod
            def respond_events(**_request):
                yield AgentActivity(
                    "web_search",
                    queries=("passport documents site:passportindia.gov.in",),
                )
                yield AgentResponse("Bring your identity documents.", "response-3", ["Web Search"])

        with TemporaryDirectory(ignore_cleanup_errors=True) as directory:
            database_path = Path(directory) / "test.sqlite3"
            with patch("app.database.session.DATABASE_PATH", database_path):
                app = create_app()
                app.config.update(TESTING=True, SECRET_KEY="test-secret")
                with get_connection() as database:
                    database.execute(
                        "INSERT INTO users (id, email, password_hash, created_date) VALUES (1, ?, ?, ?)",
                        ("user@example.com", "unused", "2026-01-01"),
                    )
                    database.execute(
                        """
                        INSERT INTO profiles (
                            user_id, full_name, age, state, district, occupation,
                            location_type, preferred_language, updated_date
                        ) VALUES (1, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        ("Test User", "20", "Delhi", "New Delhi", "student", "urban", "en", "2026-01-01"),
                    )

                client = app.test_client()
                with client.session_transaction() as session:
                    session["user_id"] = 1

                with patch("app.server.get_agent", return_value=FakeAgent()):
                    response = client.post(
                        "/api/chat/stream",
                        json={"message": "What passport documents do I need?"},
                    )
                    response_text = response.get_data(as_text=True)
                    response.close()

        self.assertEqual(response.status_code, 200)
        events = [json.loads(line) for line in response_text.splitlines()]
        self.assertEqual(
            [event["status"] for event in events if event["type"] == "status"],
            ["thinking", "official_sources"],
        )
        self.assertEqual(events[-1]["type"], "result")
        self.assertEqual(events[-1]["toolsUsed"], ["Web Search"])
        self.assertEqual(
            _chat_status_for_activity(
                AgentActivity(
                    "web_search",
                    queries=("passport renewal documents site:passportindia.gov.in",),
                ),
                "What documents do I need?",
            ),
            "official_sources",
        )


if __name__ == "__main__":
    unittest.main()
