"""
TELOS Tests — end-to-end hero flow integration test.

Validates the complete task pipeline: submit → plan → read → write → verify.
Uses mocked UIGraph/provider backends but exercises the real router,
agents, event bus, privacy filter, egress logger, and memory store.
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from services.orchestrator.router import TaskRouter
from services.orchestrator.bus.a2a import A2ABus
from services.orchestrator.models import (
    TaskStatus, EventType, TelosEvent, LLMResponse, ProviderName,
)


@pytest.fixture
def fresh_bus():
    """Each test gets a private bus to avoid cross-contamination."""
    return A2ABus()


@pytest.fixture
def captured_events(fresh_bus):
    """Capture all events emitted during a test."""
    events: list[TelosEvent] = []

    async def capture(event: TelosEvent) -> None:
        events.append(event)

    fresh_bus.subscribe(None, capture)
    return events


class TestHeroFlowE2E:
    """End-to-end tests for the hero demo path:
    Submit task → Planner decomposes → Reader extracts → Writer inserts → Verifier confirms
    """

    @pytest.mark.asyncio
    async def test_full_hero_flow(self, fresh_bus, captured_events):
        """The complete hero demo: copy value from one app to another."""
        planner_response = LLMResponse(
            content='[{"agent":"reader","action":"read_field","app":"Notepad","detail":"Q1 sales total"},{"agent":"writer","action":"write_cell","app":"Excel","detail":"cell B4"},{"agent":"verifier","action":"verify_write","app":"Excel","detail":"cell B4"}]',
            provider=ProviderName.AZURE,
            model="gpt-4o",
            bytes_sent=200,
            bytes_received=400,
        )

        reader_snapshot = {
            "snapshot": {
                "window_title": "Notepad",
                "process_name": "notepad.exe",
                "process_id": 100,
                "elements": [
                    {"name": "Q1 Sales Total", "control_type": "Text",
                     "value": "$142,587.00", "automation_id": "",
                     "bounding_rect": {}, "children": [], "is_password": False},
                ],
            }
        }
        verifier_snapshot = {
            "snapshot": {
                "window_title": "Excel",
                "process_name": "excel.exe",
                "process_id": 200,
                "elements": [
                    {"name": "cell B4", "control_type": "Text",
                     "value": "$142,587.00", "automation_id": "B4",
                     "bounding_rect": {}, "children": [], "is_password": False},
                ],
            }
        }

        with patch("services.orchestrator.router.get_bus", return_value=fresh_bus), \
             patch("services.orchestrator.router.get_provider") as mock_get_provider, \
             patch("services.orchestrator.agents.reader.AsyncClient") as MockReaderClient, \
             patch("services.orchestrator.agents.writer.AsyncClient") as MockWriterClient:

            # Mock provider (provider_name is sync, so use MagicMock for it)
            mock_provider = AsyncMock()
            mock_provider.complete = AsyncMock(return_value=planner_response)
            mock_provider.provider_name = MagicMock(return_value="azure")
            mock_provider.health_check = AsyncMock(return_value=True)
            mock_get_provider.return_value = mock_provider

            # Mock reader HTTP calls
            reader_client = AsyncMock()
            first_read = MagicMock()
            first_read.json.return_value = reader_snapshot
            first_read.raise_for_status = MagicMock()
            verify_read = MagicMock()
            verify_read.json.return_value = verifier_snapshot
            verify_read.raise_for_status = MagicMock()
            reader_client.post = AsyncMock(side_effect=[first_read, verify_read])
            reader_client.__aenter__ = AsyncMock(return_value=reader_client)
            reader_client.__aexit__ = AsyncMock(return_value=False)
            MockReaderClient.return_value = reader_client

            # Mock writer HTTP calls (focus + action)
            writer_client = AsyncMock()
            writer_resp = MagicMock()
            writer_resp.json.return_value = {"success": True}
            writer_resp.raise_for_status = MagicMock()
            writer_client.post = AsyncMock(return_value=writer_resp)
            writer_client.__aenter__ = AsyncMock(return_value=writer_client)
            writer_client.__aexit__ = AsyncMock(return_value=False)
            MockWriterClient.return_value = writer_client

            router = TaskRouter()
            record = await router.submit(
                "Copy the Q1 sales total from Notepad into Excel cell B4",
                _await=True,
            )

            # Assertions
            assert record.status == TaskStatus.COMPLETED
            assert len(record.steps) == 3
            assert record.steps[0].agent.value == "reader"
            assert record.steps[1].agent.value == "writer"
            assert record.steps[2].agent.value == "verifier"
            assert all(s.status == TaskStatus.COMPLETED for s in record.steps)
            assert record.result["extracted_value"] == "$142,587.00"

            # Privacy was tracked
            assert record.privacy_summary is not None
            assert record.privacy_summary.cloud_calls >= 1
            assert record.privacy_summary.local_operations >= 2

            # Events were emitted
            event_types = [e.event_type for e in captured_events]
            assert EventType.TASK_CREATED in event_types
            assert EventType.TASK_STATUS in event_types
            assert EventType.STEP_UPDATE in event_types
            assert EventType.PRIVACY_UPDATE in event_types

    @pytest.mark.asyncio
    async def test_hero_flow_with_pii_masking(self, fresh_bus):
        """Verify PII is masked before reaching the LLM provider."""
        captured_prompts: list[str] = []

        async def capture_prompt(request):
            captured_prompts.append(request.user_prompt)
            return LLMResponse(
                content='[{"agent":"reader","action":"read_field","app":"Notepad","detail":"total"}]',
                provider=ProviderName.AZURE,
                model="gpt-4o",
                bytes_sent=100,
                bytes_received=200,
            )

        with patch("services.orchestrator.router.get_bus", return_value=fresh_bus), \
             patch("services.orchestrator.router.get_provider") as mock_prov, \
             patch("services.orchestrator.agents.reader.AsyncClient") as MockRC:

            mock_provider = AsyncMock()
            mock_provider.complete = capture_prompt
            mock_provider.provider_name = MagicMock(return_value="azure")
            mock_get_prov = mock_prov
            mock_get_prov.return_value = mock_provider

            # Reader returns empty to keep it simple
            rc = AsyncMock()
            resp = MagicMock()
            resp.json.return_value = {"snapshot": {"window_title": "N", "process_name": "n.exe", "process_id": 1, "elements": []}}
            resp.raise_for_status = MagicMock()
            rc.post = AsyncMock(return_value=resp)
            rc.__aenter__ = AsyncMock(return_value=rc)
            rc.__aexit__ = AsyncMock(return_value=False)
            MockRC.return_value = rc

            router = TaskRouter()
            # Task text contains PII (email)
            await router.submit(
                "Send the report to user@example.com in Excel",
                _await=True,
            )

            # The prompt sent to LLM should have PII masked
            assert len(captured_prompts) >= 1
            assert "user@example.com" not in captured_prompts[0]
            assert "[REDACTED]" in captured_prompts[0]

    @pytest.mark.asyncio
    async def test_hero_flow_planner_fallback(self, fresh_bus):
        """When planner returns non-JSON, it falls back to a single reader step."""
        with patch("services.orchestrator.router.get_bus", return_value=fresh_bus), \
             patch("services.orchestrator.router.get_provider") as mock_prov, \
             patch("services.orchestrator.agents.reader.AsyncClient") as MockRC:

            mock_provider = AsyncMock()
            mock_provider.complete = AsyncMock(return_value=LLMResponse(
                content='invalid json',
                provider=ProviderName.AZURE,
                model="gpt-4o",
                bytes_sent=50,
                bytes_received=30,
            ))
            mock_provider.provider_name = MagicMock(return_value="azure")
            mock_prov.return_value = mock_provider

            # Reader returns empty (UIGraph offline)
            rc = AsyncMock()
            resp = MagicMock()
            resp.json.return_value = {"snapshot": {"window_title": "N", "process_name": "n.exe", "process_id": 1, "elements": []}}
            resp.raise_for_status = MagicMock()
            rc.post = AsyncMock(return_value=resp)
            rc.__aenter__ = AsyncMock(return_value=rc)
            rc.__aexit__ = AsyncMock(return_value=False)
            MockRC.return_value = rc

            router = TaskRouter()
            record = await router.submit("Do something", _await=True)
            # Planner falls back to a single reader step on JSONDecodeError.
            # With no extractable value, the task should now fail truthfully.
            assert record.status == TaskStatus.FAILED
            assert len(record.steps) == 1
            assert record.steps[0].agent.value == "reader"

    @pytest.mark.asyncio
    async def test_hero_flow_provider_error(self, fresh_bus):
        """Task should fail gracefully when provider raises an exception."""
        with patch("services.orchestrator.router.get_bus", return_value=fresh_bus), \
             patch("services.orchestrator.router.get_provider") as mock_prov:

            mock_provider = AsyncMock()
            mock_provider.complete = AsyncMock(side_effect=Exception("Provider timeout"))
            mock_provider.provider_name = MagicMock(return_value="azure")
            mock_prov.return_value = mock_provider

            router = TaskRouter()
            record = await router.submit("Test task", _await=True)
            assert record.status == TaskStatus.FAILED
            assert "Provider timeout" in (record.error or "")

    @pytest.mark.asyncio
    async def test_hero_flow_reader_error_fails_task(self, fresh_bus):
        """Agent-layer errors must fail the task instead of being marked completed."""
        planner_response = LLMResponse(
            content='[{"agent":"reader","action":"read_field","app":"Notepad","detail":"Q1 sales total"}]',
            provider=ProviderName.AZURE,
            model="gpt-4o",
            bytes_sent=100,
            bytes_received=200,
        )

        with patch("services.orchestrator.router.get_bus", return_value=fresh_bus), \
             patch("services.orchestrator.router.get_provider") as mock_get_provider:
            mock_provider = AsyncMock()
            mock_provider.complete = AsyncMock(return_value=planner_response)
            mock_provider.provider_name = MagicMock(return_value="azure")
            mock_provider.health_check = AsyncMock(return_value=True)
            mock_get_provider.return_value = mock_provider

            router = TaskRouter()
            router._reader.execute = AsyncMock(return_value={
                "error": "UIGraph service unavailable",
                "source": "unavailable",
                "value": None,
            })

            record = await router.submit("Copy the Q1 sales total from Notepad into Excel cell B4", _await=True)

            assert record.status == TaskStatus.FAILED
            assert "UIGraph service unavailable" in (record.error or "")
            assert record.steps[0].status == TaskStatus.FAILED


class TestCrossAppDataTransfer:
    """Integration tests for cross-app read → write → verify pipeline."""

    @pytest.mark.asyncio
    async def test_read_write_verify_sequence(self, fresh_bus):
        """Simulates reading from Notepad and writing to Excel."""
        planner_response = LLMResponse(
            content='[{"agent":"reader","action":"read_field","app":"Notepad","detail":"sales figure"},{"agent":"writer","action":"write_cell","app":"Excel","detail":"B4"}]',
            provider=ProviderName.GEMINI,
            model="gemini-pro",
            bytes_sent=150,
            bytes_received=300,
        )

        with patch("services.orchestrator.router.get_bus", return_value=fresh_bus), \
             patch("services.orchestrator.router.get_provider") as mock_prov, \
             patch("services.orchestrator.agents.reader.AsyncClient") as MockRC, \
             patch("services.orchestrator.agents.writer.AsyncClient") as MockWC:

            mock_provider = AsyncMock()
            mock_provider.complete = AsyncMock(return_value=planner_response)
            mock_provider.provider_name = MagicMock(return_value="gemini")
            mock_prov.return_value = mock_provider

            # Reader returns a value
            rc = AsyncMock()
            rr = MagicMock()
            rr.json.return_value = {"snapshot": {
                "window_title": "Notepad", "process_name": "notepad.exe", "process_id": 1,
                "elements": [{"name": "Sales Figure", "control_type": "Text",
                              "value": "$99,000", "automation_id": "", "bounding_rect": {},
                              "children": [], "is_password": False}],
            }}
            rr.raise_for_status = MagicMock()
            rc.post = AsyncMock(return_value=rr)
            rc.__aenter__ = AsyncMock(return_value=rc)
            rc.__aexit__ = AsyncMock(return_value=False)
            MockRC.return_value = rc

            # Writer succeeds
            wc = AsyncMock()
            wr = MagicMock()
            wr.json.return_value = {"success": True}
            wr.raise_for_status = MagicMock()
            wc.post = AsyncMock(return_value=wr)
            wc.__aenter__ = AsyncMock(return_value=wc)
            wc.__aexit__ = AsyncMock(return_value=False)
            MockWC.return_value = wc

            router = TaskRouter()
            record = await router.submit("Copy the sales figure from Notepad into Excel B4", _await=True)

            assert record.status == TaskStatus.COMPLETED
            assert record.result["extracted_value"] == "$99,000"
            assert len(record.steps) == 2

    @pytest.mark.asyncio
    async def test_write_failure_is_surfaced(self, fresh_bus):
        """When writer fails, the task returns a failed status."""
        import httpx

        planner_response = LLMResponse(
            content='[{"agent":"reader","action":"read_field","app":"Notepad","detail":"value"},{"agent":"writer","action":"write_cell","app":"Excel","detail":"A1"}]',
            provider=ProviderName.AZURE,
            model="gpt-4o",
            bytes_sent=100,
            bytes_received=200,
        )

        with patch("services.orchestrator.router.get_bus", return_value=fresh_bus), \
             patch("services.orchestrator.router.get_provider") as mock_prov, \
             patch("services.orchestrator.agents.reader.AsyncClient") as MockRC, \
             patch("services.orchestrator.agents.writer.AsyncClient") as MockWC:

            mock_provider = AsyncMock()
            mock_provider.complete = AsyncMock(return_value=planner_response)
            mock_provider.provider_name = MagicMock(return_value="azure")
            mock_prov.return_value = mock_provider

            # Reader works
            rc = AsyncMock()
            rr = MagicMock()
            rr.json.return_value = {"snapshot": {
                "window_title": "N", "process_name": "n.exe", "process_id": 1,
                "elements": [{"name": "Value", "control_type": "Text", "value": "42",
                              "automation_id": "", "bounding_rect": {}, "children": [],
                              "is_password": False}],
            }}
            rr.raise_for_status = MagicMock()
            rc.post = AsyncMock(return_value=rr)
            rc.__aenter__ = AsyncMock(return_value=rc)
            rc.__aexit__ = AsyncMock(return_value=False)
            MockRC.return_value = rc

            # Writer is down
            wc = AsyncMock()
            wc.post = AsyncMock(side_effect=httpx.ConnectError("Connection refused"))
            wc.__aenter__ = AsyncMock(return_value=wc)
            wc.__aexit__ = AsyncMock(return_value=False)
            MockWC.return_value = wc

            router = TaskRouter()
            record = await router.submit("Copy value from Notepad to Excel A1", _await=True)

            assert record.status == TaskStatus.FAILED
            assert "unavailable" in (record.error or "").lower()


class TestSSEPIIMasking:
    """Verify PII is masked in step details that flow to SSE/frontend."""

    @pytest.mark.asyncio
    async def test_extracted_pii_masked_in_step_detail(self, fresh_bus, captured_events):
        """When the reader extracts a value containing PII (e.g. an email),
        the step.detail visible via SSE must have PII redacted."""
        planner_response = LLMResponse(
            content='[{"agent":"reader","action":"read_field","app":"App","detail":"contact info"}]',
            provider=ProviderName.AZURE,
            model="gpt-4o",
            bytes_sent=100,
            bytes_received=200,
        )

        with patch("services.orchestrator.router.get_bus", return_value=fresh_bus), \
             patch("services.orchestrator.router.get_provider") as mock_prov, \
             patch("services.orchestrator.agents.reader.AsyncClient") as MockRC:

            mock_provider = AsyncMock()
            mock_provider.complete = AsyncMock(return_value=planner_response)
            mock_provider.provider_name = MagicMock(return_value="azure")
            mock_prov.return_value = mock_provider

            rc = AsyncMock()
            resp = MagicMock()
            resp.json.return_value = {"snapshot": {
                "window_title": "App", "process_name": "app.exe", "process_id": 1,
                "elements": [
                    {"name": "contact info", "control_type": "Text",
                     "value": "secret@example.com", "automation_id": "",
                     "bounding_rect": {}, "children": [], "is_password": False},
                ],
            }}
            resp.raise_for_status = MagicMock()
            rc.post = AsyncMock(return_value=resp)
            rc.__aenter__ = AsyncMock(return_value=rc)
            rc.__aexit__ = AsyncMock(return_value=False)
            MockRC.return_value = rc

            router = TaskRouter()
            record = await router.submit("Get the contact info from App", _await=True)

            # The raw email should NOT appear in step details
            for step in record.steps:
                assert "secret@example.com" not in (step.detail or "")
            # It should be redacted
            assert "[REDACTED]" in record.steps[0].detail

            # Also check SSE event payloads
            for event in captured_events:
                payload_str = str(event.payload)
                assert "secret@example.com" not in payload_str
