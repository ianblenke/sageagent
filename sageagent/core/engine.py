"""AgentEngine: top-level orchestrator wiring all components."""

from __future__ import annotations

from typing import Any

from sageagent.communication.bus import MessageBus
from sageagent.communication.protocols import ShutdownRequest
from sageagent.core.agent import Agent
from sageagent.core.config import EngineConfig
from sageagent.core.types import AgentId
from sageagent.llm.base import LLMBackend
from sageagent.llm.claude import ClaudeBackend
from sageagent.llm.openai import OpenAIBackend
from sageagent.memory.graph import MemoryGraph
from sageagent.memory.query import MemoryQuery
from sageagent.tools.builtins.file_ops import FileReadTool, FileSearchTool, FileWriteTool
from sageagent.tools.builtins.shell import ShellTool
from sageagent.tools.registry import ToolRegistry
from sageagent.topology.decomposer import TaskDecomposer
from sageagent.topology.manager import TopologyManager


class AgentEngine:
    """Top-level orchestrator for multi-agent workflows."""

    def __init__(self, config: EngineConfig | None = None) -> None:
        self._config = config or EngineConfig.from_env()
        self._llm = self._create_llm_backend()
        self._memory = MemoryGraph(self._config.memory)
        self._query = MemoryQuery(self._memory)
        self._bus = MessageBus()
        self._tools = ToolRegistry()
        self._register_default_tools()
        self._decomposer = TaskDecomposer(self._llm)
        self._topology = TopologyManager(
            decomposer=self._decomposer,
            llm=self._llm,
            tool_registry=self._tools,
            memory=self._memory,
            bus=self._bus,
            config=self._config.agent,
        )
        self._agents: list[Agent] = []

    def _create_llm_backend(self) -> LLMBackend:
        """Create the appropriate LLM backend based on config."""
        if self._config.llm_backend == "claude":
            return ClaudeBackend(
                api_key=self._config.anthropic_api_key,
                model=self._config.model_name,
            )
        return OpenAIBackend(
            api_key=self._config.openai_api_key,
            model=self._config.model_name,
        )

    def _register_default_tools(self) -> None:
        """Register built-in tools."""
        wd = self._config.tools.working_directory
        timeout = self._config.tools.execution_timeout_seconds
        self._tools.register(ShellTool(timeout=timeout))
        self._tools.register(FileReadTool(working_directory=wd))
        self._tools.register(FileWriteTool(working_directory=wd))
        self._tools.register(FileSearchTool(working_directory=wd))

    async def run(self, task: str) -> dict[str, Any]:
        """Submit a task and run the full agent workflow."""
        root = Agent(
            role="root",
            task=task,
            llm=self._llm,
            tool_registry=self._tools,
            memory=self._memory,
            bus=self._bus,
            config=self._config.agent,
        )
        self._agents.append(root)
        result = await root.run()
        return result

    async def run_with_topology(self, task: str) -> dict[str, Any]:
        """Submit a task using the topology manager for decomposition."""
        return await self._topology.execute_task(task)

    async def shutdown(self) -> None:
        """Shut down all active agents and clean up."""
        await self._bus.publish(ShutdownRequest(sender=AgentId("engine")))
        for agent in self._agents:
            if agent.status.value in ("created", "running"):
                agent.terminate()
        self._agents.clear()

    @property
    def memory(self) -> MemoryGraph:
        """Access the memory graph."""
        return self._memory

    @property
    def query(self) -> MemoryQuery:
        """Access the memory query interface."""
        return self._query

    @property
    def bus(self) -> MessageBus:
        """Access the message bus."""
        return self._bus

    @property
    def tools(self) -> ToolRegistry:
        """Access the tool registry."""
        return self._tools
