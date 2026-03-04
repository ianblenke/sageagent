"""Topology management: task decomposition and agent hierarchies."""

from sageagent.topology.dag import TaskDAG, TaskNode
from sageagent.topology.decomposer import TaskDecomposer
from sageagent.topology.manager import TopologyManager

__all__ = ["TaskDAG", "TaskNode", "TaskDecomposer", "TopologyManager"]
