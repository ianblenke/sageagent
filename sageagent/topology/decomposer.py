"""LLM-driven task decomposition."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

from sageagent.topology.dag import TaskDAG, TaskNode

if TYPE_CHECKING:
    from sageagent.llm.base import LLMBackend

DECOMPOSITION_PROMPT = """Analyze this task and determine if it needs decomposition into subtasks.

Task: {task_description}

If this task is simple enough to execute directly, respond with:
{{"decompose": false}}

If it needs decomposition, respond with:
{{"decompose": true, "subtasks": [
  {{"description": "subtask description", "complexity": 0.5, "role_hint": "role description", "depends_on": []}},
  {{"description": "another subtask", "complexity": 0.8, "role_hint": "role", "depends_on": [0]}}
]}}

The depends_on array contains indices of subtasks that must complete first.
Respond with ONLY valid JSON."""


class TaskDecomposer:
    """Decomposes complex tasks into subtask DAGs using an LLM."""

    def __init__(self, llm: LLMBackend) -> None:
        self._llm = llm

    async def decompose(self, task_description: str) -> TaskDAG:
        """Decompose a task into a DAG of subtasks."""
        response = await self._llm.generate(
            messages=[
                {
                    "role": "user",
                    "content": DECOMPOSITION_PROMPT.format(task_description=task_description),
                }
            ],
        )
        return self._parse_response(response.content, task_description)

    def _parse_response(self, content: str, original_description: str) -> TaskDAG:
        """Parse the LLM response into a TaskDAG."""
        dag = TaskDAG()
        try:
            data = json.loads(content)
        except json.JSONDecodeError:
            # If parsing fails, treat as a single task
            task = TaskNode(description=original_description)
            dag.add_task(task)
            return dag

        if not data.get("decompose", False):
            task = TaskNode(description=original_description)
            dag.add_task(task)
            return dag

        subtasks = data.get("subtasks", [])
        if not subtasks:
            task = TaskNode(description=original_description)
            dag.add_task(task)
            return dag

        # Create task nodes
        task_nodes: list[TaskNode] = []
        for st in subtasks:
            node = TaskNode(
                description=st.get("description", ""),
                complexity=st.get("complexity", 1.0),
                role_hint=st.get("role_hint", ""),
            )
            dag.add_task(node)
            task_nodes.append(node)

        # Add dependency edges
        for i, st in enumerate(subtasks):
            deps = st.get("depends_on", [])
            for dep_idx in deps:
                if 0 <= dep_idx < len(task_nodes) and dep_idx != i:
                    dag.add_dependency(task_nodes[dep_idx].id, task_nodes[i].id)

        return dag
