"""Tool registry for discovery, registration, and lookup."""

from __future__ import annotations

from sageagent.tools.base import Tool


class ToolRegistry:
    """Manages tool discovery, registration, and lookup."""

    def __init__(self) -> None:
        self._tools: dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        """Register a tool in the registry."""
        self._tools[tool.name] = tool

    def unregister(self, name: str) -> None:
        """Remove a tool from the registry."""
        if name not in self._tools:
            raise KeyError(f"Tool '{name}' not found in registry")
        del self._tools[name]

    def get(self, name: str) -> Tool:
        """Get a tool by name."""
        if name not in self._tools:
            raise KeyError(f"Tool '{name}' not found in registry")
        return self._tools[name]

    def list_tools(self) -> list[Tool]:
        """Return all registered tools."""
        return list(self._tools.values())

    def find_by_tag(self, tag: str) -> list[Tool]:
        """Find tools matching a capability tag."""
        return [t for t in self._tools.values() if tag in t.tags]

    def find_by_description(self, query: str) -> list[Tool]:
        """Find tools whose name or description matches a query string."""
        lower_query = query.lower()
        return [
            t
            for t in self._tools.values()
            if lower_query in t.name.lower() or lower_query in t.description.lower()
        ]

    def to_llm_schemas(self) -> list[dict]:
        """Convert all registered tools to LLM tool-use format."""
        return [t.to_llm_schema() for t in self._tools.values()]

    def __contains__(self, name: str) -> bool:
        return name in self._tools

    def __len__(self) -> int:
        return len(self._tools)
