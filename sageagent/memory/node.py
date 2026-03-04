"""Memory node types for the graph-based memory system."""

from __future__ import annotations

import enum
from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field

from sageagent.core.types import AgentId, NodeId, new_node_id


class NodeType(enum.StrEnum):
    """Types of memory nodes."""

    TASK_CONTEXT = "task_context"
    DISCOVERY = "discovery"
    EXECUTION = "execution"
    RELATIONSHIP = "relationship"


class TaskContextPayload(BaseModel):
    """Payload for task context nodes."""

    task_description: str
    decomposition_decisions: list[str] = Field(default_factory=list)
    assigned_agent: str = ""


class DiscoveryPayload(BaseModel):
    """Payload for discovery nodes (findings about code, vulnerabilities, patterns)."""

    finding_type: str
    details: str
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ExecutionPayload(BaseModel):
    """Payload for execution nodes (tool outputs)."""

    tool_name: str
    parameters: dict[str, Any] = Field(default_factory=dict)
    output: str = ""
    status: str = "success"


class RelationshipPayload(BaseModel):
    """Payload for relationship nodes (dependencies between subtasks)."""

    source_task: str
    target_task: str
    relationship_type: str
    description: str = ""


PayloadType = TaskContextPayload | DiscoveryPayload | ExecutionPayload | RelationshipPayload


class MemoryNode(BaseModel):
    """A node in the memory graph."""

    id: NodeId = Field(default_factory=new_node_id)
    node_type: NodeType
    payload: PayloadType
    agent_id: AgentId = AgentId("")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    pinned: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)
