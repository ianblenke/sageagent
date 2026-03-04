"""Tool base class and result types."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel, Field


class ToolResult(BaseModel):
    """Result returned by tool execution."""

    output: Any = ""
    status: str = "success"
    metadata: dict[str, Any] = Field(default_factory=dict)

    @property
    def is_error(self) -> bool:
        """Check if the result represents an error."""
        return self.status == "error"


class Tool(ABC):
    """Abstract base class for all tools."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique tool name."""

    @property
    @abstractmethod
    def description(self) -> str:
        """Human-readable description."""

    @property
    @abstractmethod
    def parameters_schema(self) -> dict[str, Any]:
        """JSON Schema defining accepted parameters."""

    @abstractmethod
    async def execute(self, **kwargs: Any) -> ToolResult:
        """Execute the tool with given parameters."""

    def to_llm_schema(self) -> dict[str, Any]:
        """Convert to LLM tool-use format."""
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": self.parameters_schema,
        }

    @property
    def tags(self) -> list[str]:
        """Capability tags for registry lookup."""
        return []
