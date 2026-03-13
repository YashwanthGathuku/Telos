"""
TELOS A2A Event Bus — lightweight pub/sub for inter-agent communication.

Agents publish TelosEvents; the frontend SSE stream and internal agents
subscribe to them. This is the single internal communication backbone.
"""

from __future__ import annotations

import asyncio
import logging
from collections import defaultdict
from typing import Callable, Awaitable

from services.orchestrator.models import TelosEvent, EventType

logger = logging.getLogger("telos.bus")

Subscriber = Callable[[TelosEvent], Awaitable[None]]


class A2ABus:
    """Async publish/subscribe event bus."""

    def __init__(self) -> None:
        self._subscribers: dict[EventType | None, list[Subscriber]] = defaultdict(list)
        self._history: list[TelosEvent] = []
        self._max_history = 500
        self._lock = asyncio.Lock()

    def subscribe(self, event_type: EventType | None, handler: Subscriber) -> None:
        """Subscribe to a specific event type, or None for all events."""
        self._subscribers[event_type].append(handler)

    def unsubscribe(self, event_type: EventType | None, handler: Subscriber) -> None:
        """Remove a subscriber."""
        subs = self._subscribers.get(event_type, [])
        if handler in subs:
            subs.remove(handler)

    async def publish(self, event: TelosEvent) -> None:
        """Publish an event to all matching subscribers."""
        async with self._lock:
            self._history.append(event)
            if len(self._history) > self._max_history:
                self._history = self._history[-self._max_history:]

        # Notify type-specific subscribers
        for handler in self._subscribers.get(event.event_type, []):
            try:
                await handler(event)
            except Exception:
                logger.exception("Subscriber error for %s", event.event_type)

        # Notify wildcard subscribers
        for handler in self._subscribers.get(None, []):
            try:
                await handler(event)
            except Exception:
                logger.exception("Wildcard subscriber error")

    def recent(self, n: int = 50) -> list[TelosEvent]:
        """Return the most recent N events."""
        return list(self._history[-n:])


# Module-level singleton
_bus: A2ABus | None = None


def get_bus() -> A2ABus:
    """Return the global A2A bus singleton."""
    global _bus
    if _bus is None:
        _bus = A2ABus()
    return _bus
