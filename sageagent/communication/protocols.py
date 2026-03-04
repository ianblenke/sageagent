"""Message types and coordination protocols for inter-agent communication."""

from __future__ import annotations

import enum
from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field

from sageagent.core.types import AgentId, TaskId


class MessageType(enum.StrEnum):
    """Types of messages on the bus."""

    TASK_COMPLETED = "task_completed"
    TASK_FAILED = "task_failed"
    TASK_STARTED = "task_started"
    AGENT_SPAWNED = "agent_spawned"
    SHUTDOWN_REQUEST = "shutdown_request"
    CUSTOM = "custom"


class Message(BaseModel):
    """Base message on the bus."""

    type: MessageType
    sender: AgentId
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    payload: dict[str, Any] = Field(default_factory=dict)


class TaskCompleted(Message):
    """Signal that an agent has completed its task."""

    type: MessageType = MessageType.TASK_COMPLETED
    task_id: TaskId = TaskId("")


class TaskFailed(Message):
    """Signal that an agent has failed its task."""

    type: MessageType = MessageType.TASK_FAILED
    task_id: TaskId = TaskId("")
    error: str = ""


class TaskStarted(Message):
    """Signal that an agent has started working on a task."""

    type: MessageType = MessageType.TASK_STARTED
    task_id: TaskId = TaskId("")


class AgentSpawned(Message):
    """Signal that a new agent has been spawned."""

    type: MessageType = MessageType.AGENT_SPAWNED
    child_agent_id: AgentId = AgentId("")
    role: str = ""


class ShutdownRequest(Message):
    """Request all agents to shut down gracefully."""

    type: MessageType = MessageType.SHUTDOWN_REQUEST
