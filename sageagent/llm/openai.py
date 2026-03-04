"""OpenAI LLM backend."""

from __future__ import annotations

import json
from typing import Any

import openai

from sageagent.llm.base import LLMBackend, LLMResponse, ToolCall

DEFAULT_MODEL = "gpt-4o"


class OpenAIBackend(LLMBackend):
    """LLM backend using the OpenAI API."""

    def __init__(self, api_key: str, model: str = "") -> None:
        self._client = openai.AsyncOpenAI(api_key=api_key)
        self._model = model or DEFAULT_MODEL

    async def generate(
        self,
        messages: list[dict[str, Any]],
        system: str = "",
        model: str = "",
    ) -> LLMResponse:
        """Generate a text response from OpenAI."""
        msgs = list(messages)
        if system:
            msgs = [{"role": "system", "content": system}] + msgs
        response = await self._client.chat.completions.create(
            model=model or self._model,
            messages=msgs,
        )
        choice = response.choices[0]
        return LLMResponse(
            content=choice.message.content or "",
            stop_reason=choice.finish_reason or "",
            raw={"id": response.id, "model": response.model},
        )

    async def generate_with_tools(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]],
        system: str = "",
        model: str = "",
    ) -> LLMResponse:
        """Generate a response that may include tool calls."""
        msgs = list(messages)
        if system:
            msgs = [{"role": "system", "content": system}] + msgs
        openai_tools = [
            {
                "type": "function",
                "function": {
                    "name": t["name"],
                    "description": t.get("description", ""),
                    "parameters": t.get("input_schema", t.get("parameters", {})),
                },
            }
            for t in tools
        ]
        response = await self._client.chat.completions.create(
            model=model or self._model,
            messages=msgs,
            tools=openai_tools,
        )
        choice = response.choices[0]
        content = choice.message.content or ""
        tool_calls: list[ToolCall] = []
        if choice.message.tool_calls:
            for tc in choice.message.tool_calls:
                args = tc.function.arguments
                parsed = json.loads(args) if isinstance(args, str) else args
                tool_calls.append(
                    ToolCall(
                        tool_name=tc.function.name,
                        arguments=parsed if isinstance(parsed, dict) else {},
                        call_id=tc.id,
                    )
                )
        return LLMResponse(
            content=content,
            tool_calls=tool_calls,
            stop_reason=choice.finish_reason or "",
            raw={"id": response.id, "model": response.model},
        )
