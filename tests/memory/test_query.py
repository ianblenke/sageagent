"""Tests for memory query and traversal."""

from datetime import UTC, datetime, timedelta

import pytest

from sageagent.core.types import AgentId, NodeId
from sageagent.memory.graph import MemoryGraph
from sageagent.memory.node import (
    DiscoveryPayload,
    ExecutionPayload,
    MemoryNode,
    NodeType,
    TaskContextPayload,
)
from sageagent.memory.query import MemoryQuery


@pytest.fixture
def populated_graph():
    graph = MemoryGraph()
    now = datetime.now(UTC)

    task_node = MemoryNode(
        id=NodeId("task-1"),
        node_type=NodeType.TASK_CONTEXT,
        payload=TaskContextPayload(task_description="Find bugs"),
        agent_id=AgentId("agent-a"),
        timestamp=now,
    )
    disc_node = MemoryNode(
        id=NodeId("disc-1"),
        node_type=NodeType.DISCOVERY,
        payload=DiscoveryPayload(finding_type="bug", details="null pointer"),
        agent_id=AgentId("agent-a"),
        timestamp=now + timedelta(seconds=1),
    )
    exec_node = MemoryNode(
        id=NodeId("exec-1"),
        node_type=NodeType.EXECUTION,
        payload=ExecutionPayload(tool_name="shell", output="error found"),
        agent_id=AgentId("agent-b"),
        timestamp=now + timedelta(seconds=2),
    )

    graph.add_node(task_node)
    graph.add_node(disc_node)
    graph.add_node(exec_node)
    graph.add_edge(NodeId("task-1"), NodeId("disc-1"), label="produced")
    graph.add_edge(NodeId("disc-1"), NodeId("exec-1"), label="verified_by")

    return graph


def test_query_by_type(populated_graph):
    query = MemoryQuery(populated_graph)
    discoveries = query.by_type(NodeType.DISCOVERY)
    assert len(discoveries) == 1
    assert discoveries[0].id == NodeId("disc-1")


def test_query_by_type_with_agent_filter(populated_graph):
    query = MemoryQuery(populated_graph)
    results = query.by_type(NodeType.EXECUTION, agent_id=AgentId("agent-b"))
    assert len(results) == 1
    results = query.by_type(NodeType.EXECUTION, agent_id=AgentId("agent-a"))
    assert len(results) == 0


def test_query_by_type_with_time_filters(populated_graph):
    query = MemoryQuery(populated_graph)
    now = datetime.now(UTC)
    past = now - timedelta(hours=1)
    future = now + timedelta(hours=1)

    # After filter
    results = query.by_type(NodeType.TASK_CONTEXT, after=future)
    assert len(results) == 0

    results = query.by_type(NodeType.TASK_CONTEXT, after=past)
    assert len(results) == 1

    # Before filter
    results = query.by_type(NodeType.TASK_CONTEXT, before=past)
    assert len(results) == 0

    results = query.by_type(NodeType.TASK_CONTEXT, before=future)
    assert len(results) == 1


def test_context_for_task(populated_graph):
    query = MemoryQuery(populated_graph)
    context = query.context_for_task(NodeId("task-1"))
    assert len(context) == 3  # task + discovery + execution (all connected)
    ids = {n.id for n in context}
    assert NodeId("task-1") in ids
    assert NodeId("disc-1") in ids
    assert NodeId("exec-1") in ids


def test_context_for_task_single_node():
    graph = MemoryGraph()
    node = MemoryNode(
        id=NodeId("solo"),
        node_type=NodeType.TASK_CONTEXT,
        payload=TaskContextPayload(task_description="solo"),
    )
    graph.add_node(node)
    query = MemoryQuery(graph)
    context = query.context_for_task(NodeId("solo"))
    assert len(context) == 1


def test_search(populated_graph):
    query = MemoryQuery(populated_graph)
    results = query.search("null pointer")
    assert len(results) == 1
    assert results[0].id == NodeId("disc-1")


def test_search_no_results(populated_graph):
    query = MemoryQuery(populated_graph)
    results = query.search("nonexistent")
    assert len(results) == 0


def test_search_case_insensitive(populated_graph):
    query = MemoryQuery(populated_graph)
    results = query.search("NULL POINTER")
    assert len(results) == 1
