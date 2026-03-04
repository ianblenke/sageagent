"""Tests for topology manager."""

import json

import pytest

from sageagent.communication.bus import MessageBus
from sageagent.core.config import AgentConfig
from sageagent.llm.base import LLMResponse, ToolCall
from sageagent.memory.graph import MemoryGraph
from sageagent.tools.registry import ToolRegistry
from sageagent.topology.decomposer import TaskDecomposer
from sageagent.topology.manager import TopologyManager
from tests.conftest import MockLLMBackend, MockTool


def _make_manager(llm: MockLLMBackend, max_depth: int = 3) -> TopologyManager:
    decomposer = TaskDecomposer(llm)
    registry = ToolRegistry()
    registry.register(MockTool(name="test_tool"))
    memory = MemoryGraph()
    bus = MessageBus()
    config = AgentConfig(max_iterations=10, max_hierarchy_depth=max_depth)
    return TopologyManager(decomposer, llm, registry, memory, bus, config)


@pytest.mark.asyncio
async def test_execute_simple_task():
    llm = MockLLMBackend(
        responses=[
            # Decomposer says don't decompose
            LLMResponse(content=json.dumps({"decompose": False})),
            # Direct execution response
            LLMResponse(content="TASK_COMPLETE: Done"),
        ]
    )
    manager = _make_manager(llm)
    result = await manager.execute_task("Simple task")
    assert "content" in result


@pytest.mark.asyncio
async def test_execute_with_tool_calls():
    llm = MockLLMBackend(
        responses=[
            # Decomposer says don't decompose
            LLMResponse(content=json.dumps({"decompose": False})),
            # Direct execution with tool call
            LLMResponse(
                content="Using tool",
                tool_calls=[ToolCall(tool_name="test_tool", arguments={"input": "data"})],
            ),
        ]
    )
    manager = _make_manager(llm)
    result = await manager.execute_task("Tool task")
    assert len(result["tool_calls"]) == 1
    assert result["tool_calls"][0]["tool"] == "test_tool"


@pytest.mark.asyncio
async def test_execute_with_missing_tool():
    llm = MockLLMBackend(
        responses=[
            LLMResponse(content=json.dumps({"decompose": False})),
            LLMResponse(
                content="Using missing tool",
                tool_calls=[ToolCall(tool_name="nonexistent", arguments={})],
            ),
        ]
    )
    manager = _make_manager(llm)
    result = await manager.execute_task("Task")
    assert "error" in result["tool_calls"][0]


@pytest.mark.asyncio
async def test_depth_limit_enforcement():
    # At max depth, should execute directly without decomposing
    llm = MockLLMBackend(
        responses=[
            LLMResponse(content="Direct result"),
        ]
    )
    manager = _make_manager(llm, max_depth=1)
    result = await manager.execute_task("Task", depth=1)
    assert result["content"] == "Direct result"


@pytest.mark.asyncio
async def test_execute_dag_with_parallel_tasks():
    dag_response = json.dumps(
        {
            "decompose": True,
            "subtasks": [
                {"description": "Task A", "depends_on": []},
                {"description": "Task B", "depends_on": []},
            ],
        }
    )
    llm = MockLLMBackend(
        responses=[
            LLMResponse(content=dag_response),  # decomposition
            # Task A decomposes as single
            LLMResponse(content=json.dumps({"decompose": False})),
            LLMResponse(content="Result A"),
            # Task B decomposes as single
            LLMResponse(content=json.dumps({"decompose": False})),
            LLMResponse(content="Result B"),
        ]
    )
    manager = _make_manager(llm)
    result = await manager.execute_task("Multi-task")
    assert isinstance(result, dict)


@pytest.mark.asyncio
async def test_active_agent_count():
    llm = MockLLMBackend(
        responses=[
            LLMResponse(content=json.dumps({"decompose": False})),
            LLMResponse(content="Done"),
        ]
    )
    manager = _make_manager(llm)
    assert manager.active_agent_count == 0
    await manager.execute_task("Task")
    # After single-task execution (no agents spawned)
    assert manager.active_agent_count == 0


@pytest.mark.asyncio
async def test_execute_dag_with_failure():
    """Test DAG execution where a subtask fails (covers has_failures branch)."""
    dag_response = json.dumps(
        {
            "decompose": True,
            "subtasks": [
                {"description": "Will fail", "depends_on": []},
                {"description": "Depends on failure", "depends_on": [0]},
            ],
        }
    )

    call_count = 0

    class FailingLLM(MockLLMBackend):
        async def generate(self, messages, system="", model=""):
            return LLMResponse(content=dag_response)

        async def generate_with_tools(self, messages, tools, system="", model=""):
            nonlocal call_count
            call_count += 1
            if call_count <= 1:
                # First call is decomposition
                return LLMResponse(content=dag_response)
            raise RuntimeError("LLM failure")

    llm = FailingLLM()
    manager = _make_manager(llm, max_depth=1)
    # At depth 1, subtasks execute directly via generate_with_tools which raises
    # The exception is caught by asyncio.gather(return_exceptions=True)
    result = await manager.execute_task("Failing task")
    assert isinstance(result, dict)


@pytest.mark.asyncio
async def test_execute_dag_successful_subtasks():
    """Test DAG with successful subtasks that complete normally (covers else branch in _execute_dag)."""
    dag_response = json.dumps(
        {
            "decompose": True,
            "subtasks": [
                {"description": "Task A", "depends_on": []},
            ],
        }
    )
    llm = MockLLMBackend(
        responses=[
            LLMResponse(content=dag_response),
            # Direct execution at max depth
            LLMResponse(content="Success A"),
        ]
    )
    manager = _make_manager(llm, max_depth=1)
    result = await manager.execute_task("Multi")
    assert isinstance(result, dict)


@pytest.mark.asyncio
async def test_execute_dag_no_ready_tasks():
    """Test _execute_dag when no tasks are ready (deadlock case - covers line 63 break)."""
    from sageagent.core.types import TaskId, TaskStatus
    from sageagent.topology.dag import TaskDAG, TaskNode

    # Manually create a DAG with tasks that can never become ready
    # This simulates a situation where all pending tasks are blocked
    llm = MockLLMBackend()
    manager = _make_manager(llm)

    dag = TaskDAG()
    t1 = TaskNode(id=TaskId("t1"), description="A")
    t2 = TaskNode(id=TaskId("t2"), description="B")
    dag.add_task(t1)
    dag.add_task(t2)
    dag.add_dependency(TaskId("t1"), TaskId("t2"))
    # Mark t1 as running (not completed) so t2 stays blocked, and t1 is not pending
    t1.status = TaskStatus.RUNNING

    # Call _execute_dag directly
    result = await manager._execute_dag(dag, depth=0)
    # Should exit loop because no tasks are ready
    assert isinstance(result, dict)
    assert len(result) == 0


@pytest.mark.asyncio
async def test_spawn_and_execute_exception():
    """Test _spawn_and_execute when inner execute_task raises (covers except branch and failure in _execute_dag)."""
    # Need >= 2 subtasks so we enter _execute_dag path
    dag_response = json.dumps(
        {
            "decompose": True,
            "subtasks": [
                {"description": "Will error A", "depends_on": []},
                {"description": "Will error B", "depends_on": []},
            ],
        }
    )

    gen_call = 0

    class ErrorLLM(MockLLMBackend):
        async def generate(self, messages, system="", model=""):
            nonlocal gen_call
            gen_call += 1
            if gen_call == 1:
                return LLMResponse(content=dag_response)
            # Subtask decomposition returns single task
            return LLMResponse(content=json.dumps({"decompose": False}))

        async def generate_with_tools(self, messages, tools, system="", model=""):
            raise RuntimeError("Execution error")

    llm = ErrorLLM()
    # depth 0 -> decompose into 2 subtasks -> _execute_dag -> _spawn_and_execute for each
    # Each subtask at depth 1 -> decompose (single) -> _execute_directly -> raises RuntimeError
    # RuntimeError caught by asyncio.gather(return_exceptions=True) in _execute_dag
    manager = _make_manager(llm, max_depth=3)
    result = await manager.execute_task("Error task")
    assert isinstance(result, dict)
    # At least one key should have an error
    has_error = any("error" in str(v) for v in result.values())
    assert has_error
