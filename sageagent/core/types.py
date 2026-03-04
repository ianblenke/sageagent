"""Shared type definitions used across SageAgent."""

from __future__ import annotations

import enum
import uuid
from typing import NewType

AgentId = NewType("AgentId", str)
TaskId = NewType("TaskId", str)
ToolId = NewType("ToolId", str)
NodeId = NewType("NodeId", str)


class AgentStatus(enum.StrEnum):
    """Lifecycle status of an agent."""

    CREATED = "created"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TERMINATED = "terminated"


class TaskStatus(enum.StrEnum):
    """Status of a task in the DAG."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


def new_agent_id() -> AgentId:
    """Generate a unique AgentId."""
    return AgentId(f"agent-{uuid.uuid4().hex[:12]}")


def new_task_id() -> TaskId:
    """Generate a unique TaskId."""
    return TaskId(f"task-{uuid.uuid4().hex[:12]}")


def new_tool_id() -> ToolId:
    """Generate a unique ToolId."""
    return ToolId(f"tool-{uuid.uuid4().hex[:12]}")


def new_node_id() -> NodeId:
    """Generate a unique NodeId."""
    return NodeId(f"node-{uuid.uuid4().hex[:12]}")
