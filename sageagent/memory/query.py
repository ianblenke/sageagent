"""Query and traversal operations for the memory graph."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sageagent.core.types import AgentId, NodeId
from sageagent.memory.node import MemoryNode, NodeType

if TYPE_CHECKING:
    from sageagent.memory.graph import MemoryGraph


class MemoryQuery:
    """Query interface for the memory graph."""

    def __init__(self, graph: MemoryGraph) -> None:
        self._graph = graph

    def by_type(
        self,
        node_type: NodeType,
        agent_id: AgentId | None = None,
        after: datetime | None = None,
        before: datetime | None = None,
    ) -> list[MemoryNode]:
        """Query nodes by type with optional filters."""
        results = []
        for node in self._graph.all_nodes():
            if node.node_type != node_type:
                continue
            if agent_id is not None and node.agent_id != agent_id:
                continue
            if after is not None and node.timestamp <= after:
                continue
            if before is not None and node.timestamp >= before:
                continue
            results.append(node)
        return results

    def context_for_task(self, task_node_id: NodeId) -> list[MemoryNode]:
        """Traverse the graph from a task context node to gather all related context."""
        visited: set[NodeId] = set()
        result: list[MemoryNode] = []
        self._traverse(task_node_id, visited, result)
        return result

    def _traverse(self, node_id: NodeId, visited: set[NodeId], result: list[MemoryNode]) -> None:
        """Recursively traverse from a node following all edges."""
        if node_id in visited:
            return
        visited.add(node_id)
        result.append(self._graph.get_node(node_id))
        for related_node, _ in self._graph.get_related(node_id):
            self._traverse(related_node.id, visited, result)

    def search(self, text: str) -> list[MemoryNode]:
        """Full-text search across node payloads."""
        results = []
        lower_text = text.lower()
        for node in self._graph.all_nodes():
            payload_str = node.payload.model_dump_json().lower()
            if lower_text in payload_str:
                results.append(node)
        return results
