"""Tests for memory node types."""

from datetime import datetime

from sageagent.core.types import AgentId
from sageagent.memory.node import (
    DiscoveryPayload,
    ExecutionPayload,
    MemoryNode,
    NodeType,
    RelationshipPayload,
    TaskContextPayload,
)


def test_task_context_payload():
    payload = TaskContextPayload(
        task_description="Test task",
        decomposition_decisions=["split into 2"],
        assigned_agent="agent-1",
    )
    assert payload.task_description == "Test task"
    assert payload.decomposition_decisions == ["split into 2"]
    assert payload.assigned_agent == "agent-1"


def test_task_context_payload_defaults():
    payload = TaskContextPayload(task_description="Test")
    assert payload.decomposition_decisions == []
    assert payload.assigned_agent == ""


def test_discovery_payload():
    payload = DiscoveryPayload(
        finding_type="vulnerability",
        details="SQL injection found",
        confidence=0.9,
        metadata={"file": "app.py"},
    )
    assert payload.finding_type == "vulnerability"
    assert payload.confidence == 0.9


def test_discovery_payload_defaults():
    payload = DiscoveryPayload(finding_type="pattern", details="test")
    assert payload.confidence == 1.0
    assert payload.metadata == {}


def test_execution_payload():
    payload = ExecutionPayload(
        tool_name="shell",
        parameters={"command": "ls"},
        output="file1.py",
        status="success",
    )
    assert payload.tool_name == "shell"
    assert payload.status == "success"


def test_execution_payload_defaults():
    payload = ExecutionPayload(tool_name="test")
    assert payload.parameters == {}
    assert payload.output == ""
    assert payload.status == "success"


def test_relationship_payload():
    payload = RelationshipPayload(
        source_task="task-1",
        target_task="task-2",
        relationship_type="depends_on",
        description="task-2 needs task-1",
    )
    assert payload.relationship_type == "depends_on"


def test_relationship_payload_defaults():
    payload = RelationshipPayload(source_task="a", target_task="b", relationship_type="r")
    assert payload.description == ""


def test_memory_node_creation():
    payload = TaskContextPayload(task_description="Test")
    node = MemoryNode(
        node_type=NodeType.TASK_CONTEXT,
        payload=payload,
        agent_id=AgentId("agent-1"),
    )
    assert node.id.startswith("node-")
    assert node.node_type == NodeType.TASK_CONTEXT
    assert node.agent_id == "agent-1"
    assert isinstance(node.timestamp, datetime)
    assert node.pinned is False
    assert node.metadata == {}


def test_memory_node_pinned():
    node = MemoryNode(
        node_type=NodeType.DISCOVERY,
        payload=DiscoveryPayload(finding_type="test", details="x"),
        pinned=True,
    )
    assert node.pinned is True


def test_node_type_values():
    assert NodeType.TASK_CONTEXT == "task_context"
    assert NodeType.DISCOVERY == "discovery"
    assert NodeType.EXECUTION == "execution"
    assert NodeType.RELATIONSHIP == "relationship"
