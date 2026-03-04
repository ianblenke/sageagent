"""Inter-agent communication system."""

from sageagent.communication.bus import MessageBus
from sageagent.communication.protocols import (
    AgentSpawned,
    Message,
    MessageType,
    ShutdownRequest,
    TaskCompleted,
    TaskFailed,
    TaskStarted,
)

__all__ = [
    "Message",
    "MessageType",
    "TaskCompleted",
    "TaskFailed",
    "TaskStarted",
    "AgentSpawned",
    "ShutdownRequest",
    "MessageBus",
]
