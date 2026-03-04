"""Tests for the MessageBus."""

import pytest

from sageagent.communication.protocols import (
    Message,
    MessageType,
    ShutdownRequest,
    TaskCompleted,
    TaskFailed,
)
from sageagent.core.types import AgentId, TaskId


@pytest.mark.asyncio
async def test_publish_and_subscribe(message_bus):
    received = []

    async def handler(msg: Message):
        received.append(msg)

    message_bus.subscribe(MessageType.TASK_COMPLETED, handler)
    msg = TaskCompleted(sender=AgentId("a"), task_id=TaskId("t"))
    await message_bus.publish(msg)
    assert len(received) == 1
    assert received[0] is msg


@pytest.mark.asyncio
async def test_subscribe_filters_by_type(message_bus):
    received = []

    async def handler(msg: Message):
        received.append(msg)

    message_bus.subscribe(MessageType.TASK_COMPLETED, handler)
    await message_bus.publish(TaskFailed(sender=AgentId("a"), error="err"))
    assert len(received) == 0


@pytest.mark.asyncio
async def test_subscribe_all(message_bus):
    received = []

    async def handler(msg: Message):
        received.append(msg)

    message_bus.subscribe_all(handler)
    await message_bus.publish(TaskCompleted(sender=AgentId("a")))
    await message_bus.publish(TaskFailed(sender=AgentId("b")))
    assert len(received) == 2


@pytest.mark.asyncio
async def test_multiple_subscribers(message_bus):
    received_1 = []
    received_2 = []

    async def handler1(msg: Message):
        received_1.append(msg)

    async def handler2(msg: Message):
        received_2.append(msg)

    message_bus.subscribe(MessageType.TASK_COMPLETED, handler1)
    message_bus.subscribe(MessageType.TASK_COMPLETED, handler2)
    await message_bus.publish(TaskCompleted(sender=AgentId("a")))
    assert len(received_1) == 1
    assert len(received_2) == 1


@pytest.mark.asyncio
async def test_get_history(message_bus):
    msg1 = TaskCompleted(sender=AgentId("a"))
    msg2 = TaskFailed(sender=AgentId("b"))
    await message_bus.publish(msg1)
    await message_bus.publish(msg2)
    history = message_bus.get_history()
    assert len(history) == 2
    completed = message_bus.get_history(MessageType.TASK_COMPLETED)
    assert len(completed) == 1


@pytest.mark.asyncio
async def test_clear_history(message_bus):
    await message_bus.publish(TaskCompleted(sender=AgentId("a")))
    assert len(message_bus.get_history()) == 1
    message_bus.clear_history()
    assert len(message_bus.get_history()) == 0


def test_subscriber_count(message_bus):
    assert message_bus.subscriber_count == 0

    async def handler(msg: Message):
        pass

    message_bus.subscribe(MessageType.TASK_COMPLETED, handler)
    assert message_bus.subscriber_count == 1
    message_bus.subscribe(MessageType.TASK_FAILED, handler)
    assert message_bus.subscriber_count == 2


@pytest.mark.asyncio
async def test_publish_no_subscribers(message_bus):
    """Publish with no subscribers should not error."""
    await message_bus.publish(ShutdownRequest(sender=AgentId("engine")))
    assert len(message_bus.get_history()) == 1


@pytest.mark.asyncio
async def test_shutdown_coordination(message_bus):
    shutdown_received = []

    async def handler(msg: Message):
        shutdown_received.append(msg)

    message_bus.subscribe(MessageType.SHUTDOWN_REQUEST, handler)
    await message_bus.publish(ShutdownRequest(sender=AgentId("engine")))
    assert len(shutdown_received) == 1
    assert shutdown_received[0].type == MessageType.SHUTDOWN_REQUEST
