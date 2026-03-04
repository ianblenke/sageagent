"""Shared test fixtures for SageAgent."""

from __future__ import annotations

from typing import Any

import pytest

from sageagent.communication.bus import MessageBus
from sageagent.core.config import AgentConfig, EngineConfig, MemoryConfig, ToolConfig
from sageagent.llm.base import LLMBackend, LLMResponse
from sageagent.memory.graph import MemoryGraph
from sageagent.tools.base import Tool, ToolResult
from sageagent.tools.registry import ToolRegistry


class MockLLMBackend(LLMBackend):
    """Mock LLM backend for testing."""

    def __init__(self, responses: list[LLMResponse] | None = None) -> None:
        self._responses = list(responses or [])
        self._call_index = 0
        self.generate_calls: list[dict[str, Any]] = []
        self.generate_with_tools_calls: list[dict[str, Any]] = []

    def add_response(self, response: LLMResponse) -> None:
        self._responses.append(response)

    def _next_response(self) -> LLMResponse:
        if self._call_index < len(self._responses):
            resp = self._responses[self._call_index]
            self._call_index += 1
            return resp
        return LLMResponse(content="TASK_COMPLETE", stop_reason="end_turn")

    async def generate(
        self, messages: list[dict[str, Any]], system: str = "", model: str = ""
    ) -> LLMResponse:
        self.generate_calls.append({"messages": messages, "system": system, "model": model})
        return self._next_response()

    async def generate_with_tools(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]],
        system: str = "",
        model: str = "",
    ) -> LLMResponse:
        self.generate_with_tools_calls.append(
            {"messages": messages, "tools": tools, "system": system, "model": model}
        )
        return self._next_response()


class MockTool(Tool):
    """A simple mock tool for testing."""

    def __init__(
        self,
        name: str = "mock_tool",
        result: ToolResult | None = None,
        tool_tags: list[str] | None = None,
    ) -> None:
        self._name = name
        self._result = result or ToolResult(output="mock output")
        self._tags = tool_tags or ["mock"]
        self.execute_calls: list[dict[str, Any]] = []

    @property
    def name(self) -> str:
        return self._name

    @property
    def description(self) -> str:
        return f"Mock tool: {self._name}"

    @property
    def parameters_schema(self) -> dict[str, Any]:
        return {"type": "object", "properties": {"input": {"type": "string"}}, "required": []}

    @property
    def tags(self) -> list[str]:
        return self._tags

    async def execute(self, **kwargs: Any) -> ToolResult:
        self.execute_calls.append(kwargs)
        return self._result


@pytest.fixture
def mock_llm() -> MockLLMBackend:
    return MockLLMBackend()


@pytest.fixture
def memory_config() -> MemoryConfig:
    return MemoryConfig(max_age_seconds=3600, gc_interval_seconds=300)


@pytest.fixture
def memory_graph(memory_config: MemoryConfig) -> MemoryGraph:
    return MemoryGraph(memory_config)


@pytest.fixture
def tool_registry() -> ToolRegistry:
    return ToolRegistry()


@pytest.fixture
def message_bus() -> MessageBus:
    return MessageBus()


@pytest.fixture
def agent_config() -> AgentConfig:
    return AgentConfig(max_iterations=10, max_hierarchy_depth=3)


@pytest.fixture
def engine_config() -> EngineConfig:
    return EngineConfig(
        llm_backend="claude",
        anthropic_api_key="test-key",
        agent=AgentConfig(max_iterations=10, max_hierarchy_depth=3),
        tools=ToolConfig(execution_timeout_seconds=10),
        memory=MemoryConfig(max_age_seconds=3600),
    )
