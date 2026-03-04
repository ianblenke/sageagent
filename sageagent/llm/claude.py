"""Anthropic Claude LLM backend."""

from __future__ import annotations

from typing import Any

import anthropic

from sageagent.llm.base import LLMBackend, LLMResponse, ToolCall

DEFAULT_MODEL = "claude-sonnet-4-20250514"


class ClaudeBackend(LLMBackend):
    """LLM backend using the Anthropic Claude API."""

    def __init__(self, api_key: str, model: str = "") -> None:
        self._client = anthropic.AsyncAnthropic(api_key=api_key)
        self._model = model or DEFAULT_MODEL

    async def generate(
        self,
        messages: list[dict[str, Any]],
        system: str = "",
        model: str = "",
    ) -> LLMResponse:
        """Generate a text response from Claude."""
        kwargs: dict[str, Any] = {
            "model": model or self._model,
            "max_tokens": 4096,
            "messages": messages,
        }
        if system:
            kwargs["system"] = system
        response = await self._client.messages.create(**kwargs)
        content = ""
        for block in response.content:
            if block.type == "text":
                content += block.text
        return LLMResponse(
            content=content,
            stop_reason=response.stop_reason or "",
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
        kwargs: dict[str, Any] = {
            "model": model or self._model,
            "max_tokens": 4096,
            "messages": messages,
            "tools": tools,
        }
        if system:
            kwargs["system"] = system
        response = await self._client.messages.create(**kwargs)
        content = ""
        tool_calls: list[ToolCall] = []
        for block in response.content:
            if block.type == "text":
                content += block.text
            elif block.type == "tool_use":
                tool_calls.append(
                    ToolCall(
                        tool_name=block.name,
                        arguments=block.input if isinstance(block.input, dict) else {},
                        call_id=block.id,
                    )
                )
        return LLMResponse(
            content=content,
            tool_calls=tool_calls,
            stop_reason=response.stop_reason or "",
            raw={"id": response.id, "model": response.model},
        )
