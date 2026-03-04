"""MessageBus for inter-agent synchronization signals."""

from __future__ import annotations

import asyncio
from collections import defaultdict
from collections.abc import Awaitable, Callable

from sageagent.communication.protocols import Message, MessageType

Subscriber = Callable[[Message], Awaitable[None]]


class MessageBus:
    """Lightweight message bus for agent coordination signals."""

    def __init__(self) -> None:
        self._subscribers: dict[MessageType, list[Subscriber]] = defaultdict(list)
        self._all_subscribers: list[Subscriber] = []
        self._history: list[Message] = []

    def subscribe(self, message_type: MessageType, handler: Subscriber) -> None:
        """Subscribe to a specific message type."""
        self._subscribers[message_type].append(handler)

    def subscribe_all(self, handler: Subscriber) -> None:
        """Subscribe to all message types."""
        self._all_subscribers.append(handler)

    async def publish(self, message: Message) -> None:
        """Publish a message to all matching subscribers."""
        self._history.append(message)
        handlers = list(self._subscribers.get(message.type, []))
        handlers.extend(self._all_subscribers)
        if handlers:
            await asyncio.gather(*(h(message) for h in handlers))

    def get_history(self, message_type: MessageType | None = None) -> list[Message]:
        """Get message history, optionally filtered by type."""
        if message_type is None:
            return list(self._history)
        return [m for m in self._history if m.type == message_type]

    def clear_history(self) -> None:
        """Clear all message history."""
        self._history.clear()

    @property
    def subscriber_count(self) -> int:
        """Total number of type-specific subscriptions."""
        return sum(len(subs) for subs in self._subscribers.values())
