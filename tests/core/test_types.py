"""Tests for core type definitions."""

from sageagent.core.types import (
    AgentId,
    AgentStatus,
    NodeId,
    TaskId,
    TaskStatus,
    ToolId,
    new_agent_id,
    new_node_id,
    new_task_id,
    new_tool_id,
)


def test_agent_status_values():
    assert AgentStatus.CREATED == "created"
    assert AgentStatus.RUNNING == "running"
    assert AgentStatus.COMPLETED == "completed"
    assert AgentStatus.FAILED == "failed"
    assert AgentStatus.TERMINATED == "terminated"


def test_task_status_values():
    assert TaskStatus.PENDING == "pending"
    assert TaskStatus.RUNNING == "running"
    assert TaskStatus.COMPLETED == "completed"
    assert TaskStatus.FAILED == "failed"


def test_new_agent_id():
    aid = new_agent_id()
    assert aid.startswith("agent-")
    assert len(aid) > 6
    # Uniqueness
    assert new_agent_id() != new_agent_id()


def test_new_task_id():
    tid = new_task_id()
    assert tid.startswith("task-")
    assert new_task_id() != new_task_id()


def test_new_tool_id():
    tid = new_tool_id()
    assert tid.startswith("tool-")
    assert new_tool_id() != new_tool_id()


def test_new_node_id():
    nid = new_node_id()
    assert nid.startswith("node-")
    assert new_node_id() != new_node_id()


def test_newtype_identity():
    """Verify NewType wrappers are strings."""
    assert isinstance(AgentId("test"), str)
    assert isinstance(TaskId("test"), str)
    assert isinstance(ToolId("test"), str)
    assert isinstance(NodeId("test"), str)
