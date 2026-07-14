from __future__ import annotations

import json
import os
from collections.abc import Iterator

from dotenv import load_dotenv
from openai import OpenAI

from app.agent.models import AgentActivity, AgentResponse
from app.agent.prompts import SYSTEM_PROMPT, build_user_input
from app.tools.scheme_search import search_government_schemes


TOOLS = [
    {"type": "web_search"},
    {
        "type": "function",
        "name": "search_government_schemes",
        "description": (
            "Search the local official-source Indian government schemes dataset. "
            "Use this before recommending schemes."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "state": {"type": "string"},
                "age": {"type": "string"},
                "occupation": {"type": "string"},
                "gender": {"type": "string"},
                "annual_income": {"type": "string"},
                "disability_status": {"type": "string"},
            },
            "required": ["query"],
            "additionalProperties": False,
        },
    },
]


class GovernmentHelpAgent:
    """OpenAI-backed assistant for Indian government service guidance."""

    def __init__(self, api_key: str) -> None:
        self.client = OpenAI(api_key=api_key)

    @classmethod
    def from_environment(cls) -> GovernmentHelpAgent:
        load_dotenv()
        api_key = os.getenv("OPENAI_API_KEY")

        if not api_key:
            raise RuntimeError("OPENAI_API_KEY was not found. Add it to your .env file.")

        return cls(api_key=api_key)

    def respond(
        self,
        user_message: str,
        previous_response_id: str | None = None,
        profile: dict[str, str] | None = None,
        selected_language: str | None = None,
    ) -> AgentResponse:
        for event in self.respond_events(
            user_message=user_message,
            previous_response_id=previous_response_id,
            profile=profile,
            selected_language=selected_language,
        ):
            if isinstance(event, AgentResponse):
                return event

        raise RuntimeError("The agent response ended without a completed response.")

    def respond_events(
        self,
        user_message: str,
        previous_response_id: str | None = None,
        profile: dict[str, str] | None = None,
        selected_language: str | None = None,
    ) -> Iterator[AgentActivity | AgentResponse]:
        """Yield real tool activity while preserving the existing final response."""

        request = {
            "model": "gpt-5-mini",
            "instructions": SYSTEM_PROMPT,
            "input": build_user_input(user_message, profile, selected_language),
            "tools": TOOLS,
        }

        if previous_response_id is not None:
            request["previous_response_id"] = previous_response_id

        tools_used: list[str] = []
        announced_activities: dict[str, AgentActivity] = {}

        while True:
            response = None

            for stream_event in self.client.responses.create(**request, stream=True):
                activity = self._activity_from_stream_event(stream_event)
                if activity is not None and self._should_announce_activity(
                    activity,
                    announced_activities,
                ):
                    self._record_tool(activity.tool, tools_used)
                    yield activity

                if getattr(stream_event, "type", "") == "response.completed":
                    response = stream_event.response

            if response is None:
                raise RuntimeError("The agent response stream ended before completion.")

            function_outputs = []

            for item in response.output:
                if item.type == "web_search_call":
                    activity = self._activity_from_output_item(item)
                    if activity is not None and self._should_announce_activity(
                        activity,
                        announced_activities,
                    ):
                        self._record_tool(activity.tool, tools_used)
                        yield activity

                elif item.type == "function_call":
                    activity = self._activity_from_output_item(item)
                    if activity is not None and self._should_announce_activity(
                        activity,
                        announced_activities,
                    ):
                        self._record_tool(activity.tool, tools_used)
                        yield activity

                    arguments = self._parse_arguments(item.arguments)
                    result = self._run_function(item.name, arguments, profile or {})

                    function_outputs.append(
                        {
                            "type": "function_call_output",
                            "call_id": item.call_id,
                            "output": result,
                        }
                    )

            if not function_outputs:
                yield AgentResponse(
                    answer=response.output_text,
                    response_id=response.id,
                    tools_used=tools_used,
                )
                return

            request = {
                "model": "gpt-5-mini",
                "instructions": SYSTEM_PROMPT,
                "previous_response_id": response.id,
                "input": function_outputs,
                "tools": TOOLS,
            }

    @classmethod
    def _activity_from_stream_event(cls, event) -> AgentActivity | None:
        event_type = getattr(event, "type", "")
        if event_type in {"response.output_item.added", "response.output_item.done"}:
            return cls._activity_from_output_item(getattr(event, "item", None))
        if event_type in {
            "response.web_search_call.in_progress",
            "response.web_search_call.searching",
        }:
            return AgentActivity(tool="web_search")
        return None

    @staticmethod
    def _activity_from_output_item(item) -> AgentActivity | None:
        item_type = getattr(item, "type", "")
        if (
            item_type == "function_call"
            and getattr(item, "name", "") == "search_government_schemes"
        ):
            return AgentActivity(tool="search_government_schemes")

        if item_type != "web_search_call":
            return None

        action = getattr(item, "action", None)
        queries = []
        query = getattr(action, "query", None)
        if query:
            queries.append(str(query))
        queries.extend(str(value) for value in (getattr(action, "queries", None) or []) if value)

        urls = []
        url = getattr(action, "url", None)
        if url:
            urls.append(str(url))
        urls.extend(
            str(source.url)
            for source in (getattr(action, "sources", None) or [])
            if getattr(source, "url", None)
        )

        return AgentActivity(tool="web_search", queries=tuple(queries), urls=tuple(urls))

    @staticmethod
    def _should_announce_activity(
        activity: AgentActivity,
        announced: dict[str, AgentActivity],
    ) -> bool:
        previous = announced.get(activity.tool)
        if previous is None:
            announced[activity.tool] = activity
            return True

        previous_has_details = bool(previous.queries or previous.urls)
        activity_has_details = bool(activity.queries or activity.urls)
        if activity.tool == "web_search" and not previous_has_details and activity_has_details:
            announced[activity.tool] = activity
            return True

        return False

    @staticmethod
    def _record_tool(tool: str, tools_used: list[str]) -> None:
        labels = {
            "web_search": "Web Search",
            "search_government_schemes": "Scheme Search",
        }
        label = labels.get(tool)
        if label and label not in tools_used:
            tools_used.append(label)

    @staticmethod
    def _run_function(function_name: str, arguments: dict, profile: dict[str, str]) -> str:
        if function_name == "search_government_schemes":
            return search_government_schemes(
                query=arguments.get("query", ""),
                state=arguments.get("state") or profile.get("state"),
                age=arguments.get("age") or profile.get("age"),
                occupation=arguments.get("occupation") or profile.get("occupation"),
                gender=arguments.get("gender") or profile.get("gender"),
                annual_income=arguments.get("annual_income")
                or profile.get("annual_household_income_range"),
                disability_status=arguments.get("disability_status")
                or profile.get("disability_status"),
            )

        return f"Error: Unknown function called: {function_name}"

    @staticmethod
    def _parse_arguments(arguments: str) -> dict:
        try:
            parsed = json.loads(arguments)
        except json.JSONDecodeError:
            return {}

        return parsed if isinstance(parsed, dict) else {}
