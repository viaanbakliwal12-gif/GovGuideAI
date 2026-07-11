from __future__ import annotations

import json
import os

from dotenv import load_dotenv
from openai import OpenAI

from app.agent.models import AgentResponse
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
                "student_status": {"type": "string"},
                "farmer_status": {"type": "string"},
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
    ) -> AgentResponse:
        request = {
            "model": "gpt-5-mini",
            "instructions": SYSTEM_PROMPT,
            "input": build_user_input(user_message, profile),
            "tools": TOOLS,
        }

        if previous_response_id is not None:
            request["previous_response_id"] = previous_response_id

        response = self.client.responses.create(**request)
        tools_used: list[str] = []

        while True:
            function_outputs = []

            for item in response.output:
                if item.type == "web_search_call":
                    if "Web Search" not in tools_used:
                        tools_used.append("Web Search")

                elif item.type == "function_call":
                    arguments = self._parse_arguments(item.arguments)
                    result = self._run_function(item.name, arguments, profile or {})

                    if item.name == "search_government_schemes" and "Scheme Search" not in tools_used:
                        tools_used.append("Scheme Search")

                    function_outputs.append(
                        {
                            "type": "function_call_output",
                            "call_id": item.call_id,
                            "output": result,
                        }
                    )

            if not function_outputs:
                return AgentResponse(
                    answer=response.output_text,
                    response_id=response.id,
                    tools_used=tools_used,
                )

            response = self.client.responses.create(
                model="gpt-5-mini",
                instructions=SYSTEM_PROMPT,
                previous_response_id=response.id,
                input=function_outputs,
                tools=TOOLS,
            )

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
                student_status=arguments.get("student_status") or profile.get("student_status"),
                farmer_status=arguments.get("farmer_status") or profile.get("farmer_status"),
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
