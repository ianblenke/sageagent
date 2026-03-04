"""Tests for task decomposition."""

import json

import pytest

from sageagent.llm.base import LLMResponse
from sageagent.topology.decomposer import TaskDecomposer
from tests.conftest import MockLLMBackend


@pytest.mark.asyncio
async def test_decompose_simple_task():
    llm = MockLLMBackend(
        responses=[
            LLMResponse(content=json.dumps({"decompose": False})),
        ]
    )
    decomposer = TaskDecomposer(llm)
    dag = await decomposer.decompose("Print hello world")
    assert dag.task_count == 1
    tasks = dag.all_tasks()
    assert tasks[0].description == "Print hello world"


@pytest.mark.asyncio
async def test_decompose_complex_task():
    response = json.dumps(
        {
            "decompose": True,
            "subtasks": [
                {
                    "description": "Read file",
                    "complexity": 0.3,
                    "role_hint": "reader",
                    "depends_on": [],
                },
                {
                    "description": "Analyze code",
                    "complexity": 0.7,
                    "role_hint": "analyzer",
                    "depends_on": [0],
                },
                {
                    "description": "Write report",
                    "complexity": 0.5,
                    "role_hint": "writer",
                    "depends_on": [1],
                },
            ],
        }
    )
    llm = MockLLMBackend(responses=[LLMResponse(content=response)])
    decomposer = TaskDecomposer(llm)
    dag = await decomposer.decompose("Analyze a codebase and write a report")
    assert dag.task_count == 3
    tasks = dag.all_tasks()
    descs = [t.description for t in tasks]
    assert "Read file" in descs
    assert "Analyze code" in descs
    assert "Write report" in descs


@pytest.mark.asyncio
async def test_decompose_with_dependencies():
    response = json.dumps(
        {
            "decompose": True,
            "subtasks": [
                {"description": "A", "depends_on": []},
                {"description": "B", "depends_on": [0]},
            ],
        }
    )
    llm = MockLLMBackend(responses=[LLMResponse(content=response)])
    decomposer = TaskDecomposer(llm)
    dag = await decomposer.decompose("Task with deps")
    ready = dag.get_ready_tasks()
    assert len(ready) == 1
    assert ready[0].description == "A"


@pytest.mark.asyncio
async def test_decompose_invalid_json():
    llm = MockLLMBackend(responses=[LLMResponse(content="not json at all")])
    decomposer = TaskDecomposer(llm)
    dag = await decomposer.decompose("Some task")
    # Falls back to single task
    assert dag.task_count == 1
    assert dag.all_tasks()[0].description == "Some task"


@pytest.mark.asyncio
async def test_decompose_empty_subtasks():
    response = json.dumps({"decompose": True, "subtasks": []})
    llm = MockLLMBackend(responses=[LLMResponse(content=response)])
    decomposer = TaskDecomposer(llm)
    dag = await decomposer.decompose("Task")
    assert dag.task_count == 1


@pytest.mark.asyncio
async def test_decompose_invalid_dep_index():
    response = json.dumps(
        {
            "decompose": True,
            "subtasks": [
                {"description": "A", "depends_on": [99]},
                {"description": "B", "depends_on": [0]},
            ],
        }
    )
    llm = MockLLMBackend(responses=[LLMResponse(content=response)])
    decomposer = TaskDecomposer(llm)
    dag = await decomposer.decompose("Task")
    assert dag.task_count == 2


@pytest.mark.asyncio
async def test_decompose_self_dependency():
    response = json.dumps(
        {
            "decompose": True,
            "subtasks": [
                {"description": "A", "depends_on": [0]},
            ],
        }
    )
    llm = MockLLMBackend(responses=[LLMResponse(content=response)])
    decomposer = TaskDecomposer(llm)
    dag = await decomposer.decompose("Task")
    assert dag.task_count == 1
    # Self-dep is filtered out, task should be ready
    ready = dag.get_ready_tasks()
    assert len(ready) == 1
