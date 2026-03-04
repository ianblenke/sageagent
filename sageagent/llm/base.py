"""Abstract LLM backend interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel, Field


class ToolCall(BaseModel):
    """A standardized tool call parsed from LLM output."""

    tool_name: str
    arguments: dict[str, Any] = Field(default_factory=dict)
    call_id: str = ""


class LLMResponse(BaseModel):
    """Standardized response from any LLM backend."""

    content: str = ""
    tool_calls: list[ToolCall] = Field(default_factory=list)
    stop_reason: str = ""
    raw: dict[str, Any] = Field(default_factory=dict)

    @property
    def has_tool_calls(self) -> bool:
        """Check if the response contains tool calls."""
        return len(self.tool_calls) > 0


class LLMBackend(ABC):
    """Abstract interface for LLM providers."""

    @abstractmethod
    async def generate(
        self,
        messages: list[dict[str, Any]],
        system: str = "",
        model: str = "",
    ) -> LLMResponse:
        """Generate a text response from the LLM."""

    @abstractmethod
    async def generate_with_tools(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]],
        system: str = "",
        model: str = "",
    ) -> LLMResponse:
        """Generate a response that may include tool calls."""
