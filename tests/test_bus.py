"""
TELOS Tests — A2A Event Bus tests.
"""

import asyncio
import pytest
from services.orchestrator.bus.a2a import A2ABus
from services.orchestrator.models import TelosEvent, EventType


@pytest.fixture
def bus():
    return A2ABus()


class TestA2ABus:
    @pytest.mark.asyncio
    async def test_subscribe_and_publish(self, bus):
        received = []

        async def handler(event: TelosEvent):
            received.append(event)

        bus.subscribe(EventType.TASK_CREATED, handler)

        event = TelosEvent(
            event_type=EventType.TASK_CREATED,
            task_id="test-1",
            payload={"task": "Test task"},
        )
        await bus.publish(event)

        assert len(received) == 1
        assert received[0].task_id == "test-1"

    @pytest.mark.asyncio
    async def test_wildcard_subscriber(self, bus):
        received = []

        async def handler(event: TelosEvent):
            received.append(event)

        bus.subscribe(None, handler)

        await bus.publish(TelosEvent(event_type=EventType.TASK_CREATED, payload={}))
        await bus.publish(TelosEvent(event_type=EventType.STEP_UPDATE, payload={}))

        assert len(received) == 2

    @pytest.mark.asyncio
    async def test_unsubscribe(self, bus):
        received = []

        async def handler(event: TelosEvent):
            received.append(event)

        bus.subscribe(EventType.TASK_CREATED, handler)
        bus.unsubscribe(EventType.TASK_CREATED, handler)

        await bus.publish(TelosEvent(event_type=EventType.TASK_CREATED, payload={}))
        assert len(received) == 0

    @pytest.mark.asyncio
    async def test_recent_events(self, bus):
        for i in range(10):
            await bus.publish(TelosEvent(
                event_type=EventType.TASK_STATUS,
                payload={"index": i},
            ))

        recent = bus.recent(5)
        assert len(recent) == 5

    @pytest.mark.asyncio
    async def test_history_limit(self, bus):
        for i in range(600):
            await bus.publish(TelosEvent(
                event_type=EventType.TASK_STATUS,
                payload={"i": i},
            ))

        # Should be capped at max_history (500)
        assert len(bus.recent(1000)) <= 500

    @pytest.mark.asyncio
    async def test_subscriber_error_handled(self, bus):
        """A failing subscriber should not crash the bus."""
        calls = []

        async def bad_handler(event: TelosEvent):
            raise RuntimeError("intentional error")

        async def good_handler(event: TelosEvent):
            calls.append(event)

        bus.subscribe(EventType.TASK_CREATED, bad_handler)
        bus.subscribe(EventType.TASK_CREATED, good_handler)

        await bus.publish(TelosEvent(event_type=EventType.TASK_CREATED, payload={}))

        # Good handler should still receive the event
        assert len(calls) == 1
