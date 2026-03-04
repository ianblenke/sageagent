"""Tests for message types and protocols."""

from datetime import datetime

from sageagent.communication.protocols import (
    AgentSpawned,
    Message,
    MessageType,
    ShutdownRequest,
    TaskCompleted,
    TaskFailed,
    TaskStarted,
)
from sageagent.core.types import AgentId, TaskId


def test_message_type_values():
    assert MessageType.TASK_COMPLETED == "task_completed"
    assert MessageType.TASK_FAILED == "task_failed"
    assert MessageType.TASK_STARTED == "task_started"
    assert MessageType.AGENT_SPAWNED == "agent_spawned"
    assert MessageType.SHUTDOWN_REQUEST == "shutdown_request"
    assert MessageType.CUSTOM == "custom"


def test_base_message():
    msg = Message(type=MessageType.CUSTOM, sender=AgentId("agent-1"), payload={"key": "val"})
    assert msg.type == MessageType.CUSTOM
    assert msg.sender == "agent-1"
    assert isinstance(msg.timestamp, datetime)
    assert msg.payload == {"key": "val"}


def test_task_completed():
    msg = TaskCompleted(sender=AgentId("agent-1"), task_id=TaskId("task-1"))
    assert msg.type == MessageType.TASK_COMPLETED
    assert msg.task_id == "task-1"


def test_task_failed():
    msg = TaskFailed(sender=AgentId("agent-1"), task_id=TaskId("task-1"), error="boom")
    assert msg.type == MessageType.TASK_FAILED
    assert msg.error == "boom"


def test_task_failed_defaults():
    msg = TaskFailed(sender=AgentId("a"))
    assert msg.task_id == ""
    assert msg.error == ""


def test_task_started():
    msg = TaskStarted(sender=AgentId("agent-1"), task_id=TaskId("task-1"))
    assert msg.type == MessageType.TASK_STARTED


def test_agent_spawned():
    msg = AgentSpawned(
        sender=AgentId("parent"),
        child_agent_id=AgentId("child"),
        role="analyzer",
    )
    assert msg.type == MessageType.AGENT_SPAWNED
    assert msg.child_agent_id == "child"
    assert msg.role == "analyzer"


def test_agent_spawned_defaults():
    msg = AgentSpawned(sender=AgentId("a"))
    assert msg.child_agent_id == ""
    assert msg.role == ""


def test_shutdown_request():
    msg = ShutdownRequest(sender=AgentId("engine"))
    assert msg.type == MessageType.SHUTDOWN_REQUEST


def test_task_completed_defaults():
    msg = TaskCompleted(sender=AgentId("a"))
    assert msg.task_id == ""
