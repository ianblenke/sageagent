"""Task DAG data structure for decomposition and dependency tracking."""

from __future__ import annotations

from typing import Any

import networkx as nx
from pydantic import BaseModel, Field

from sageagent.core.types import TaskId, TaskStatus, new_task_id


class TaskNode(BaseModel):
    """A node representing a task in the DAG."""

    id: TaskId = Field(default_factory=new_task_id)
    description: str
    status: TaskStatus = TaskStatus.PENDING
    complexity: float = Field(default=1.0, ge=0.0)
    role_hint: str = ""
    result: Any = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class TaskDAG:
    """Directed acyclic graph of tasks with dependency tracking."""

    def __init__(self) -> None:
        self._graph: nx.DiGraph = nx.DiGraph()
        self._tasks: dict[TaskId, TaskNode] = {}

    def add_task(self, task: TaskNode) -> None:
        """Add a task to the DAG."""
        self._tasks[task.id] = task
        self._graph.add_node(task.id)

    def add_dependency(self, from_id: TaskId, to_id: TaskId) -> None:
        """Add a dependency edge: from_id must complete before to_id can start."""
        if from_id not in self._tasks:
            raise KeyError(f"Task {from_id} not found")
        if to_id not in self._tasks:
            raise KeyError(f"Task {to_id} not found")
        self._graph.add_edge(from_id, to_id)
        if not nx.is_directed_acyclic_graph(self._graph):
            self._graph.remove_edge(from_id, to_id)
            raise ValueError(f"Dependency {from_id} -> {to_id} would create a cycle")

    def get_task(self, task_id: TaskId) -> TaskNode:
        """Get a task by ID."""
        if task_id not in self._tasks:
            raise KeyError(f"Task {task_id} not found")
        return self._tasks[task_id]

    def mark_completed(self, task_id: TaskId, result: Any = None) -> None:
        """Mark a task as completed with an optional result."""
        task = self.get_task(task_id)
        task.status = TaskStatus.COMPLETED
        task.result = result

    def mark_failed(self, task_id: TaskId) -> None:
        """Mark a task as failed."""
        task = self.get_task(task_id)
        task.status = TaskStatus.FAILED

    def get_ready_tasks(self) -> list[TaskNode]:
        """Return tasks whose dependencies are all completed and that are still pending."""
        ready = []
        for task_id, task in self._tasks.items():
            if task.status != TaskStatus.PENDING:
                continue
            predecessors = list(self._graph.predecessors(task_id))
            all_done = all(
                self._tasks[TaskId(p)].status == TaskStatus.COMPLETED for p in predecessors
            )
            if all_done:
                ready.append(task)
        return ready

    def topological_order(self) -> list[TaskNode]:
        """Return tasks in topological order."""
        order = nx.topological_sort(self._graph)
        return [self._tasks[TaskId(tid)] for tid in order]

    def all_completed(self) -> bool:
        """Check if all tasks are completed."""
        return all(t.status == TaskStatus.COMPLETED for t in self._tasks.values())

    def has_failures(self) -> bool:
        """Check if any task has failed."""
        return any(t.status == TaskStatus.FAILED for t in self._tasks.values())

    @property
    def task_count(self) -> int:
        """Number of tasks in the DAG."""
        return len(self._tasks)

    def all_tasks(self) -> list[TaskNode]:
        """Return all tasks."""
        return list(self._tasks.values())
