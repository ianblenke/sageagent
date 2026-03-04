"""Topology manager: orchestrates agent hierarchy and task execution."""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Any

from sageagent.communication.protocols import AgentSpawned, TaskCompleted, TaskFailed, TaskStarted
from sageagent.core.types import AgentId, AgentStatus, new_agent_id
from sageagent.topology.dag import TaskDAG, TaskNode

if TYPE_CHECKING:
    from sageagent.communication.bus import MessageBus
    from sageagent.core.config import AgentConfig
    from sageagent.llm.base import LLMBackend
    from sageagent.memory.graph import MemoryGraph
    from sageagent.tools.registry import ToolRegistry
    from sageagent.topology.decomposer import TaskDecomposer


class TopologyManager:
    """Manages dynamic agent hierarchies and task execution."""

    def __init__(
        self,
        decomposer: TaskDecomposer,
        llm: LLMBackend,
        tool_registry: ToolRegistry,
        memory: MemoryGraph,
        bus: MessageBus,
        config: AgentConfig,
    ) -> None:
        self._decomposer = decomposer
        self._llm = llm
        self._tools = tool_registry
        self._memory = memory
        self._bus = bus
        self._config = config
        self._active_agents: dict[AgentId, dict[str, Any]] = {}

    async def execute_task(self, task_description: str, depth: int = 0) -> dict[str, Any]:
        """Execute a task, decomposing and spawning sub-agents as needed."""
        if depth >= self._config.max_hierarchy_depth:
            return await self._execute_directly(task_description)

        dag = await self._decomposer.decompose(task_description)

        if dag.task_count == 1:
            return await self._execute_directly(task_description)

        return await self._execute_dag(dag, depth)

    async def _execute_dag(self, dag: TaskDAG, depth: int) -> dict[str, Any]:
        """Execute all tasks in a DAG, respecting dependencies."""
        results: dict[str, Any] = {}

        while not dag.all_completed():
            if dag.has_failures():
                break

            ready = dag.get_ready_tasks()
            if not ready:
                break

            tasks_coros = [self._spawn_and_execute(task, depth) for task in ready]
            completed = await asyncio.gather(*tasks_coros, return_exceptions=True)

            for task, result in zip(ready, completed, strict=True):
                if isinstance(result, Exception):
                    dag.mark_failed(task.id)
                    results[task.id] = {"error": str(result)}
                else:
                    dag.mark_completed(task.id, result)
                    results[task.id] = result

        return results

    async def _spawn_and_execute(self, task: TaskNode, depth: int) -> dict[str, Any]:
        """Spawn a sub-agent for a task and execute it."""
        agent_id = new_agent_id()
        self._active_agents[agent_id] = {"task": task, "status": AgentStatus.CREATED}

        await self._bus.publish(
            AgentSpawned(sender=AgentId("topology"), child_agent_id=agent_id, role=task.role_hint)
        )
        await self._bus.publish(TaskStarted(sender=agent_id, task_id=task.id))

        self._active_agents[agent_id]["status"] = AgentStatus.RUNNING
        try:
            result = await self.execute_task(task.description, depth + 1)
            self._active_agents[agent_id]["status"] = AgentStatus.COMPLETED
            await self._bus.publish(TaskCompleted(sender=agent_id, task_id=task.id))
            return result
        except Exception as e:
            self._active_agents[agent_id]["status"] = AgentStatus.FAILED
            await self._bus.publish(TaskFailed(sender=agent_id, task_id=task.id, error=str(e)))
            raise

    async def _execute_directly(self, task_description: str) -> dict[str, Any]:
        """Execute a task directly using the LLM without further decomposition."""
        tools = self._tools.to_llm_schemas()
        response = await self._llm.generate_with_tools(
            messages=[{"role": "user", "content": task_description}],
            tools=tools,
            system="You are an agent. Complete the given task using available tools.",
        )

        result: dict[str, Any] = {"content": response.content, "tool_calls": []}

        if response.has_tool_calls:
            for tc in response.tool_calls:
                try:
                    tool = self._tools.get(tc.tool_name)
                    tool_result = await tool.execute(**tc.arguments)
                    result["tool_calls"].append(
                        {
                            "tool": tc.tool_name,
                            "args": tc.arguments,
                            "result": tool_result.model_dump(),
                        }
                    )
                except KeyError:
                    result["tool_calls"].append(
                        {
                            "tool": tc.tool_name,
                            "error": f"Tool '{tc.tool_name}' not found",
                        }
                    )

        return result

    @property
    def active_agent_count(self) -> int:
        """Number of currently tracked agents."""
        return len(self._active_agents)
