"""Agent base class with lifecycle management."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from sageagent.communication.protocols import TaskCompleted, TaskFailed
from sageagent.core.types import AgentId, AgentStatus, TaskId, new_agent_id
from sageagent.memory.node import ExecutionPayload, MemoryNode, NodeType, TaskContextPayload

if TYPE_CHECKING:
    from sageagent.communication.bus import MessageBus
    from sageagent.core.config import AgentConfig
    from sageagent.llm.base import LLMBackend
    from sageagent.memory.graph import MemoryGraph
    from sageagent.tools.registry import ToolRegistry


class Agent:
    """An LLM-powered autonomous agent with full lifecycle management."""

    def __init__(
        self,
        role: str,
        task: str,
        llm: LLMBackend,
        tool_registry: ToolRegistry,
        memory: MemoryGraph,
        bus: MessageBus,
        config: AgentConfig,
        agent_id: AgentId | None = None,
    ) -> None:
        self.id = agent_id or new_agent_id()
        self.role = role
        self.task = task
        self.status = AgentStatus.CREATED
        self._llm = llm
        self._tools = tool_registry
        self._memory = memory
        self._bus = bus
        self._config = config
        self._messages: list[dict[str, Any]] = []
        self._task_id = TaskId("")
        self._iterations = 0

    async def run(self) -> dict[str, Any]:
        """Execute the agent's task through an iterative loop."""
        self.status = AgentStatus.RUNNING

        # Write task context to memory
        ctx_node = MemoryNode(
            node_type=NodeType.TASK_CONTEXT,
            payload=TaskContextPayload(
                task_description=self.task,
                assigned_agent=self.id,
            ),
            agent_id=self.id,
        )
        self._memory.add_node(ctx_node)

        system = f"You are an agent with role: {self.role}. Complete the assigned task using available tools. When done, respond with TASK_COMPLETE."
        self._messages = [{"role": "user", "content": self.task}]
        result: dict[str, Any] = {"content": "", "tool_results": []}

        try:
            while self._iterations < self._config.max_iterations:
                self._iterations += 1
                tools = self._tools.to_llm_schemas()
                response = await self._llm.generate_with_tools(
                    messages=self._messages,
                    tools=tools,
                    system=system,
                )

                result["content"] = response.content

                if response.has_tool_calls:
                    tool_results_msg = await self._execute_tools(response.tool_calls, result)
                    self._messages.append({"role": "assistant", "content": response.content})
                    self._messages.append({"role": "user", "content": tool_results_msg})
                else:
                    break

                if "TASK_COMPLETE" in response.content:
                    break

            self.status = AgentStatus.COMPLETED
            await self._bus.publish(TaskCompleted(sender=self.id, task_id=self._task_id))
            return result

        except Exception as e:
            self.status = AgentStatus.FAILED
            await self._bus.publish(TaskFailed(sender=self.id, task_id=self._task_id, error=str(e)))
            raise

    async def _execute_tools(self, tool_calls: list, result: dict[str, Any]) -> str:
        """Execute tool calls and record results in memory."""
        parts = []
        for tc in tool_calls:
            try:
                tool = self._tools.get(tc.tool_name)
                tool_result = await tool.execute(**tc.arguments)

                # Write execution to memory
                exec_node = MemoryNode(
                    node_type=NodeType.EXECUTION,
                    payload=ExecutionPayload(
                        tool_name=tc.tool_name,
                        parameters=tc.arguments,
                        output=str(tool_result.output),
                        status=tool_result.status,
                    ),
                    agent_id=self.id,
                )
                self._memory.add_node(exec_node)

                result["tool_results"].append({"tool": tc.tool_name, "output": tool_result.output})
                parts.append(f"Tool {tc.tool_name} result: {tool_result.output}")
            except KeyError:
                parts.append(f"Tool {tc.tool_name} not found")
        return "\n".join(parts)

    def terminate(self) -> None:
        """Gracefully terminate the agent."""
        self.status = AgentStatus.TERMINATED
