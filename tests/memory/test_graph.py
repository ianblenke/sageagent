"""Tests for memory graph operations."""

from datetime import UTC, datetime, timedelta

import pytest

from sageagent.core.config import MemoryConfig
from sageagent.core.types import NodeId
from sageagent.memory.graph import CycleError, MemoryGraph
from sageagent.memory.node import (
    DiscoveryPayload,
    ExecutionPayload,
    MemoryNode,
    NodeType,
    TaskContextPayload,
)


def _make_node(
    node_type: NodeType = NodeType.TASK_CONTEXT, node_id: NodeId | None = None, **kwargs
) -> MemoryNode:
    payloads = {
        NodeType.TASK_CONTEXT: TaskContextPayload(task_description="test"),
        NodeType.DISCOVERY: DiscoveryPayload(finding_type="test", details="test"),
        NodeType.EXECUTION: ExecutionPayload(tool_name="test"),
    }
    node = MemoryNode(
        node_type=node_type,
        payload=payloads[node_type],
        **kwargs,
    )
    if node_id:
        node.id = node_id
    return node


def test_add_node(memory_graph):
    node = _make_node()
    memory_graph.add_node(node)
    assert memory_graph.node_count == 1
    assert memory_graph.get_node(node.id) is node


def test_get_node_not_found(memory_graph):
    with pytest.raises(KeyError, match="not found"):
        memory_graph.get_node(NodeId("nonexistent"))


def test_add_edge(memory_graph):
    n1 = _make_node(node_id=NodeId("n1"))
    n2 = _make_node(node_id=NodeId("n2"))
    memory_graph.add_node(n1)
    memory_graph.add_node(n2)
    memory_graph.add_edge(NodeId("n1"), NodeId("n2"), label="derived_from")
    successors = memory_graph.get_successors(NodeId("n1"))
    assert len(successors) == 1
    assert successors[0][0].id == NodeId("n2")
    assert successors[0][1] == "derived_from"


def test_add_edge_source_not_found(memory_graph):
    n2 = _make_node(node_id=NodeId("n2"))
    memory_graph.add_node(n2)
    with pytest.raises(KeyError, match="Source node"):
        memory_graph.add_edge(NodeId("missing"), NodeId("n2"))


def test_add_edge_target_not_found(memory_graph):
    n1 = _make_node(node_id=NodeId("n1"))
    memory_graph.add_node(n1)
    with pytest.raises(KeyError, match="Target node"):
        memory_graph.add_edge(NodeId("n1"), NodeId("missing"))


def test_add_edge_cycle_detection(memory_graph):
    n1 = _make_node(node_id=NodeId("n1"))
    n2 = _make_node(node_id=NodeId("n2"))
    memory_graph.add_node(n1)
    memory_graph.add_node(n2)
    memory_graph.add_edge(NodeId("n1"), NodeId("n2"))
    with pytest.raises(CycleError, match="would create a cycle"):
        memory_graph.add_edge(NodeId("n2"), NodeId("n1"))


def test_get_successors(memory_graph):
    n1 = _make_node(node_id=NodeId("n1"))
    n2 = _make_node(node_id=NodeId("n2"))
    memory_graph.add_node(n1)
    memory_graph.add_node(n2)
    memory_graph.add_edge(NodeId("n1"), NodeId("n2"), label="test")
    succs = memory_graph.get_successors(NodeId("n1"))
    assert len(succs) == 1


def test_get_successors_not_found(memory_graph):
    with pytest.raises(KeyError):
        memory_graph.get_successors(NodeId("missing"))


def test_get_predecessors(memory_graph):
    n1 = _make_node(node_id=NodeId("n1"))
    n2 = _make_node(node_id=NodeId("n2"))
    memory_graph.add_node(n1)
    memory_graph.add_node(n2)
    memory_graph.add_edge(NodeId("n1"), NodeId("n2"))
    preds = memory_graph.get_predecessors(NodeId("n2"))
    assert len(preds) == 1
    assert preds[0][0].id == NodeId("n1")


def test_get_predecessors_not_found(memory_graph):
    with pytest.raises(KeyError):
        memory_graph.get_predecessors(NodeId("missing"))


def test_get_related(memory_graph):
    n1 = _make_node(node_id=NodeId("n1"))
    n2 = _make_node(node_id=NodeId("n2"))
    n3 = _make_node(node_id=NodeId("n3"))
    memory_graph.add_node(n1)
    memory_graph.add_node(n2)
    memory_graph.add_node(n3)
    memory_graph.add_edge(NodeId("n1"), NodeId("n2"))
    memory_graph.add_edge(NodeId("n3"), NodeId("n2"))
    related = memory_graph.get_related(NodeId("n2"))
    assert len(related) == 2  # n1 predecessor + n3 predecessor (no successors)


def test_remove_node(memory_graph):
    n1 = _make_node(node_id=NodeId("n1"))
    memory_graph.add_node(n1)
    assert memory_graph.node_count == 1
    memory_graph.remove_node(NodeId("n1"))
    assert memory_graph.node_count == 0


def test_remove_node_not_found(memory_graph):
    with pytest.raises(KeyError):
        memory_graph.remove_node(NodeId("missing"))


def test_all_nodes(memory_graph):
    n1 = _make_node()
    n2 = _make_node()
    memory_graph.add_node(n1)
    memory_graph.add_node(n2)
    all_nodes = memory_graph.all_nodes()
    assert len(all_nodes) == 2


def test_garbage_collect_unreachable(memory_graph):
    n1 = _make_node(node_id=NodeId("root"))
    n2 = _make_node(node_id=NodeId("connected"))
    n3 = _make_node(node_id=NodeId("orphan"))
    memory_graph.add_node(n1)
    memory_graph.add_node(n2)
    memory_graph.add_node(n3)
    memory_graph.add_edge(NodeId("root"), NodeId("connected"))
    removed = memory_graph.garbage_collect(active_root_ids={NodeId("root")})
    assert removed == 1
    assert memory_graph.node_count == 2


def test_garbage_collect_age_based():
    config = MemoryConfig(max_age_seconds=10)
    graph = MemoryGraph(config)
    old_node = _make_node(node_id=NodeId("old"))
    old_node.timestamp = datetime.now(UTC) - timedelta(seconds=100)
    graph.add_node(old_node)
    removed = graph.garbage_collect(active_root_ids={NodeId("old")})
    assert removed == 1
    assert graph.node_count == 0


def test_garbage_collect_pinned_survives():
    config = MemoryConfig(max_age_seconds=10)
    graph = MemoryGraph(config)
    pinned = _make_node(node_id=NodeId("pinned"))
    pinned.pinned = True
    pinned.timestamp = datetime.now(UTC) - timedelta(seconds=100)
    graph.add_node(pinned)
    removed = graph.garbage_collect()
    assert removed == 0
    assert graph.node_count == 1


def test_garbage_collect_no_active_roots(memory_graph):
    n1 = _make_node()
    memory_graph.add_node(n1)
    removed = memory_graph.garbage_collect()
    assert removed == 1


def test_garbage_collect_empty_graph(memory_graph):
    removed = memory_graph.garbage_collect()
    assert removed == 0


def test_garbage_collect_missing_root_id(memory_graph):
    """Test GC with active_root_id that doesn't exist in graph."""
    n1 = _make_node(node_id=NodeId("existing"))
    memory_graph.add_node(n1)
    # Pass a root ID that doesn't exist - should not crash, and existing node is unreachable
    removed = memory_graph.garbage_collect(active_root_ids={NodeId("nonexistent")})
    assert removed == 1


def test_garbage_collect_with_ancestors():
    """Test GC preserves nodes reachable as ancestors of active roots."""
    graph = MemoryGraph()
    parent = _make_node(node_id=NodeId("parent"))
    child = _make_node(node_id=NodeId("child"))
    graph.add_node(parent)
    graph.add_node(child)
    graph.add_edge(NodeId("parent"), NodeId("child"))
    # child is root - parent is an ancestor and should be preserved
    removed = graph.garbage_collect(active_root_ids={NodeId("child")})
    assert removed == 0
    assert graph.node_count == 2


def test_default_config():
    graph = MemoryGraph()
    assert graph.node_count == 0
