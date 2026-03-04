"""MemoryGraph: DAG-based memory storage using NetworkX."""

from __future__ import annotations

from datetime import UTC, datetime

import networkx as nx

from sageagent.core.config import MemoryConfig
from sageagent.core.types import NodeId
from sageagent.memory.node import MemoryNode


class CycleError(Exception):
    """Raised when adding an edge would create a cycle."""


class MemoryGraph:
    """Directed acyclic graph for hierarchical agent memory."""

    def __init__(self, config: MemoryConfig | None = None) -> None:
        self._graph: nx.DiGraph = nx.DiGraph()
        self._nodes: dict[NodeId, MemoryNode] = {}
        self._config = config or MemoryConfig()

    @property
    def node_count(self) -> int:
        """Return the number of nodes in the graph."""
        return len(self._nodes)

    def add_node(self, node: MemoryNode) -> None:
        """Add a memory node to the graph."""
        self._nodes[node.id] = node
        self._graph.add_node(node.id)

    def add_edge(self, from_id: NodeId, to_id: NodeId, label: str = "") -> None:
        """Add a directed edge between two nodes. Raises CycleError if it would create a cycle."""
        if from_id not in self._nodes:
            raise KeyError(f"Source node {from_id} not found")
        if to_id not in self._nodes:
            raise KeyError(f"Target node {to_id} not found")
        self._graph.add_edge(from_id, to_id, label=label)
        if not nx.is_directed_acyclic_graph(self._graph):
            self._graph.remove_edge(from_id, to_id)
            raise CycleError(f"Edge {from_id} -> {to_id} would create a cycle")

    def get_node(self, node_id: NodeId) -> MemoryNode:
        """Retrieve a node by its ID."""
        if node_id not in self._nodes:
            raise KeyError(f"Node {node_id} not found")
        return self._nodes[node_id]

    def get_successors(self, node_id: NodeId) -> list[tuple[MemoryNode, str]]:
        """Get nodes that this node points to, with edge labels."""
        if node_id not in self._nodes:
            raise KeyError(f"Node {node_id} not found")
        result = []
        for successor in self._graph.successors(node_id):
            edge_data = self._graph.edges[node_id, successor]
            result.append((self._nodes[NodeId(successor)], edge_data.get("label", "")))
        return result

    def get_predecessors(self, node_id: NodeId) -> list[tuple[MemoryNode, str]]:
        """Get nodes that point to this node, with edge labels."""
        if node_id not in self._nodes:
            raise KeyError(f"Node {node_id} not found")
        result = []
        for predecessor in self._graph.predecessors(node_id):
            edge_data = self._graph.edges[predecessor, node_id]
            result.append((self._nodes[NodeId(predecessor)], edge_data.get("label", "")))
        return result

    def get_related(self, node_id: NodeId) -> list[tuple[MemoryNode, str]]:
        """Get all directly connected nodes (both directions) with labels."""
        successors = self.get_successors(node_id)
        predecessors = self.get_predecessors(node_id)
        return successors + predecessors

    def remove_node(self, node_id: NodeId) -> None:
        """Remove a node and its edges from the graph."""
        if node_id not in self._nodes:
            raise KeyError(f"Node {node_id} not found")
        self._graph.remove_node(node_id)
        del self._nodes[node_id]

    def all_nodes(self) -> list[MemoryNode]:
        """Return all nodes in the graph."""
        return list(self._nodes.values())

    def garbage_collect(self, active_root_ids: set[NodeId] | None = None) -> int:
        """Remove unreachable and expired nodes. Returns count of removed nodes."""
        now = datetime.now(UTC)
        active_root_ids = active_root_ids or set()
        reachable: set[NodeId] = set()
        for root_id in active_root_ids:
            if root_id in self._nodes:
                reachable.add(root_id)
                for descendant in nx.descendants(self._graph, root_id):
                    reachable.add(NodeId(descendant))
                for ancestor in nx.ancestors(self._graph, root_id):
                    reachable.add(NodeId(ancestor))

        to_remove: list[NodeId] = []
        for node_id, node in self._nodes.items():
            if node.pinned:
                continue
            is_reachable = node_id in reachable
            age = (now - node.timestamp).total_seconds()
            is_expired = age > self._config.max_age_seconds
            if not is_reachable or is_expired:
                to_remove.append(node_id)

        for node_id in to_remove:
            self._graph.remove_node(node_id)
            del self._nodes[node_id]

        return len(to_remove)
