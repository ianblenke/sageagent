"""Tests for TaskDAG data structure."""

import pytest

from sageagent.core.types import TaskId, TaskStatus
from sageagent.topology.dag import TaskDAG, TaskNode


def test_add_task():
    dag = TaskDAG()
    task = TaskNode(description="Test task")
    dag.add_task(task)
    assert dag.task_count == 1
    assert dag.get_task(task.id).description == "Test task"


def test_get_task_not_found():
    dag = TaskDAG()
    with pytest.raises(KeyError):
        dag.get_task(TaskId("nonexistent"))


def test_add_dependency():
    dag = TaskDAG()
    t1 = TaskNode(id=TaskId("t1"), description="First")
    t2 = TaskNode(id=TaskId("t2"), description="Second")
    dag.add_task(t1)
    dag.add_task(t2)
    dag.add_dependency(TaskId("t1"), TaskId("t2"))
    # t2 should not be ready until t1 completes
    ready = dag.get_ready_tasks()
    assert len(ready) == 1
    assert ready[0].id == TaskId("t1")


def test_add_dependency_not_found():
    dag = TaskDAG()
    t1 = TaskNode(id=TaskId("t1"), description="First")
    dag.add_task(t1)
    with pytest.raises(KeyError):
        dag.add_dependency(TaskId("t1"), TaskId("missing"))
    with pytest.raises(KeyError):
        dag.add_dependency(TaskId("missing"), TaskId("t1"))


def test_add_dependency_cycle():
    dag = TaskDAG()
    t1 = TaskNode(id=TaskId("t1"), description="A")
    t2 = TaskNode(id=TaskId("t2"), description="B")
    dag.add_task(t1)
    dag.add_task(t2)
    dag.add_dependency(TaskId("t1"), TaskId("t2"))
    with pytest.raises(ValueError, match="cycle"):
        dag.add_dependency(TaskId("t2"), TaskId("t1"))


def test_mark_completed():
    dag = TaskDAG()
    task = TaskNode(id=TaskId("t1"), description="Test")
    dag.add_task(task)
    dag.mark_completed(TaskId("t1"), result="done")
    assert task.status == TaskStatus.COMPLETED
    assert task.result == "done"


def test_mark_failed():
    dag = TaskDAG()
    task = TaskNode(id=TaskId("t1"), description="Test")
    dag.add_task(task)
    dag.mark_failed(TaskId("t1"))
    assert task.status == TaskStatus.FAILED


def test_get_ready_tasks():
    dag = TaskDAG()
    t1 = TaskNode(id=TaskId("t1"), description="First")
    t2 = TaskNode(id=TaskId("t2"), description="Second")
    t3 = TaskNode(id=TaskId("t3"), description="Third")
    dag.add_task(t1)
    dag.add_task(t2)
    dag.add_task(t3)
    dag.add_dependency(TaskId("t1"), TaskId("t3"))
    dag.add_dependency(TaskId("t2"), TaskId("t3"))

    # t1 and t2 are ready (no deps)
    ready = dag.get_ready_tasks()
    ready_ids = {t.id for t in ready}
    assert ready_ids == {TaskId("t1"), TaskId("t2")}

    # Complete t1, t3 still not ready
    dag.mark_completed(TaskId("t1"))
    ready = dag.get_ready_tasks()
    assert len(ready) == 1
    assert ready[0].id == TaskId("t2")

    # Complete t2, now t3 is ready
    dag.mark_completed(TaskId("t2"))
    ready = dag.get_ready_tasks()
    assert len(ready) == 1
    assert ready[0].id == TaskId("t3")


def test_topological_order():
    dag = TaskDAG()
    t1 = TaskNode(id=TaskId("t1"), description="First")
    t2 = TaskNode(id=TaskId("t2"), description="Second")
    dag.add_task(t1)
    dag.add_task(t2)
    dag.add_dependency(TaskId("t1"), TaskId("t2"))
    order = dag.topological_order()
    assert order[0].id == TaskId("t1")
    assert order[1].id == TaskId("t2")


def test_all_completed():
    dag = TaskDAG()
    t1 = TaskNode(id=TaskId("t1"), description="A")
    dag.add_task(t1)
    assert dag.all_completed() is False
    dag.mark_completed(TaskId("t1"))
    assert dag.all_completed() is True


def test_has_failures():
    dag = TaskDAG()
    t1 = TaskNode(id=TaskId("t1"), description="A")
    dag.add_task(t1)
    assert dag.has_failures() is False
    dag.mark_failed(TaskId("t1"))
    assert dag.has_failures() is True


def test_all_tasks():
    dag = TaskDAG()
    t1 = TaskNode(description="A")
    t2 = TaskNode(description="B")
    dag.add_task(t1)
    dag.add_task(t2)
    assert len(dag.all_tasks()) == 2


def test_task_node_defaults():
    task = TaskNode(description="Test")
    assert task.status == TaskStatus.PENDING
    assert task.complexity == 1.0
    assert task.role_hint == ""
    assert task.result is None
    assert task.metadata == {}
