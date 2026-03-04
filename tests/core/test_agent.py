"""Tests for Agent lifecycle."""

import pytest

from sageagent.communication.bus import MessageBus
from sageagent.communication.protocols import MessageType
from sageagent.core.agent import Agent
from sageagent.core.config import AgentConfig
from sageagent.core.types import AgentId, AgentStatus
from sageagent.llm.base import LLMResponse, ToolCall
from sageagent.memory.graph import MemoryGraph
from sageagent.memory.node import NodeType
from sageagent.memory.query import MemoryQuery
from sageagent.tools.base import ToolResult
from sageagent.tools.registry import ToolRegistry
from tests.conftest import MockLLMBackend, MockTool


def _make_agent(llm: MockLLMBackend, **kwargs) -> Agent:
    memory = kwargs.pop("memory", MemoryGraph())
    bus = kwargs.pop("bus", MessageBus())
    registry = kwargs.pop("registry", ToolRegistry())
    config = kwargs.pop("config", AgentConfig(max_iterations=10))
    return Agent(
        role=kwargs.pop("role", "tester"),
        task=kwargs.pop("task", "test task"),
        llm=llm,
        tool_registry=registry,
        memory=memory,
        bus=bus,
        config=config,
        agent_id=kwargs.pop("agent_id", None),
    )


@pytest.mark.asyncio
async def test_agent_creation_with_role():
    llm = MockLLMBackend()
    agent = _make_agent(llm, role="analyzer", agent_id=AgentId("agent-test"))
    assert agent.id == "agent-test"
    assert agent.role == "analyzer"
    assert agent.status == AgentStatus.CREATED


@pytest.mark.asyncio
async def test_agent_auto_id():
    llm = MockLLMBackend()
    agent = _make_agent(llm)
    assert agent.id.startswith("agent-")


@pytest.mark.asyncio
async def test_agent_execution_loop():
    llm = MockLLMBackend(
        responses=[
            LLMResponse(content="Working on it..."),
        ]
    )
    memory = MemoryGraph()
    bus = MessageBus()
    agent = _make_agent(llm, memory=memory, bus=bus)
    result = await agent.run()
    assert agent.status == AgentStatus.COMPLETED
    assert result["content"] == "Working on it..."
    # Should have written task context to memory
    query = MemoryQuery(memory)
    ctx_nodes = query.by_type(NodeType.TASK_CONTEXT)
    assert len(ctx_nodes) == 1


@pytest.mark.asyncio
async def test_agent_execution_with_tools():
    llm = MockLLMBackend(
        responses=[
            LLMResponse(
                content="Using tool",
                tool_calls=[ToolCall(tool_name="mock", arguments={"input": "x"})],
            ),
            LLMResponse(content="TASK_COMPLETE"),
        ]
    )
    registry = ToolRegistry()
    registry.register(MockTool(name="mock", result=ToolResult(output="tool output")))
    memory = MemoryGraph()
    agent = _make_agent(llm, registry=registry, memory=memory)
    result = await agent.run()
    assert len(result["tool_results"]) == 1
    assert result["tool_results"][0]["output"] == "tool output"
    # Execution node should be in memory
    query = MemoryQuery(memory)
    exec_nodes = query.by_type(NodeType.EXECUTION)
    assert len(exec_nodes) == 1


@pytest.mark.asyncio
async def test_agent_execution_missing_tool():
    llm = MockLLMBackend(
        responses=[
            LLMResponse(
                content="Using tool",
                tool_calls=[ToolCall(tool_name="nonexistent", arguments={})],
            ),
            LLMResponse(content="TASK_COMPLETE"),
        ]
    )
    agent = _make_agent(llm)
    await agent.run()
    assert agent.status == AgentStatus.COMPLETED


@pytest.mark.asyncio
async def test_agent_task_complete_in_content():
    llm = MockLLMBackend(
        responses=[
            LLMResponse(
                content="TASK_COMPLETE result here",
                tool_calls=[ToolCall(tool_name="mock", arguments={})],
            ),
        ]
    )
    registry = ToolRegistry()
    registry.register(MockTool(name="mock"))
    agent = _make_agent(llm, registry=registry)
    await agent.run()
    assert agent.status == AgentStatus.COMPLETED


@pytest.mark.asyncio
async def test_agent_max_iterations():
    # LLM always returns tool calls, should stop at max_iterations
    responses = [
        LLMResponse(
            content="Still working",
            tool_calls=[ToolCall(tool_name="mock", arguments={})],
        )
        for _ in range(15)
    ]
    llm = MockLLMBackend(responses=responses)
    registry = ToolRegistry()
    registry.register(MockTool(name="mock"))
    config = AgentConfig(max_iterations=3)
    agent = _make_agent(llm, registry=registry, config=config)
    await agent.run()
    assert agent.status == AgentStatus.COMPLETED
    assert agent._iterations == 3


@pytest.mark.asyncio
async def test_agent_failure():
    llm = MockLLMBackend()
    # Override generate_with_tools to raise

    async def failing_generate(*args, **kwargs):
        raise RuntimeError("LLM error")

    llm.generate_with_tools = failing_generate
    bus = MessageBus()
    agent = _make_agent(llm, bus=bus)
    with pytest.raises(RuntimeError, match="LLM error"):
        await agent.run()
    assert agent.status == AgentStatus.FAILED
    # Should have published failure
    failures = bus.get_history(MessageType.TASK_FAILED)
    assert len(failures) == 1


@pytest.mark.asyncio
async def test_agent_publishes_completion():
    llm = MockLLMBackend(responses=[LLMResponse(content="Done")])
    bus = MessageBus()
    agent = _make_agent(llm, bus=bus)
    await agent.run()
    completions = bus.get_history(MessageType.TASK_COMPLETED)
    assert len(completions) == 1


def test_agent_terminate():
    llm = MockLLMBackend()
    agent = _make_agent(llm)
    agent.terminate()
    assert agent.status == AgentStatus.TERMINATED
