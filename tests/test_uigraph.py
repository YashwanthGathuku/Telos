"""
TELOS Tests — UIGraph extraction and reader/writer agent tests.

Tests structured UI extraction, password masking, element search,
and the agent layer that sits on top of UIGraph.
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from services.orchestrator.models import UIElement, UISnapshot
from services.orchestrator.agents.reader import ReaderAgent
from services.orchestrator.agents.writer import WriterAgent
from services.orchestrator.agents.verifier import VerifierAgent


# ── UIElement / UISnapshot model tests ───────────────────────────────────

class TestUIGraphModels:
    def test_element_defaults(self):
        elem = UIElement(name="Button1", control_type="Button")
        assert elem.name == "Button1"
        assert elem.value == ""
        assert elem.is_password is False
        assert elem.children == []

    def test_password_element(self):
        elem = UIElement(name="Password", control_type="Edit", value="", is_password=True)
        assert elem.is_password is True

    def test_nested_tree(self):
        child = UIElement(name="ChildEdit", control_type="Edit", value="123")
        parent = UIElement(name="GroupBox", control_type="Group", children=[child])
        assert len(parent.children) == 1
        assert parent.children[0].value == "123"

    def test_snapshot_creation(self):
        snap = UISnapshot(
            window_title="Test App",
            process_name="test.exe",
            process_id=1234,
            elements=[
                UIElement(name="Label1", control_type="Text", value="Hello"),
            ],
        )
        assert snap.window_title == "Test App"
        assert len(snap.elements) == 1

    def test_snapshot_empty_elements(self):
        snap = UISnapshot(window_title="Empty", process_name="e.exe", process_id=0)
        assert snap.elements == []


# ── ReaderAgent extraction logic ─────────────────────────────────────────

class TestReaderExtraction:
    """Test the ReaderAgent's _extract_value and _flatten_elements methods."""

    def setup_method(self):
        self.reader = ReaderAgent()
        self.snapshot = UISnapshot(
            window_title="Sales Report",
            process_name="quickbooks.exe",
            process_id=5678,
            elements=[
                UIElement(name="Q1 Sales Total", control_type="Text", value="$142,587.00"),
                UIElement(name="Q2 Sales Total", control_type="Text", value="$198,000.00"),
                UIElement(
                    name="Password Field",
                    control_type="Edit",
                    value="secret123",
                    is_password=True,
                ),
                UIElement(
                    name="Details Group",
                    control_type="Group",
                    children=[
                        UIElement(name="Revenue Line", control_type="Text", value="$50,000"),
                    ],
                ),
            ],
        )

    def test_extract_matching_value(self):
        value = self.reader._extract_value(self.snapshot, "Q1 sales total")
        assert value == "$142,587.00"

    def test_extract_partial_match(self):
        value = self.reader._extract_value(self.snapshot, "sales total Q1")
        assert value == "$142,587.00"

    def test_extract_no_match(self):
        value = self.reader._extract_value(self.snapshot, "nonexistent field")
        assert value is None

    def test_extract_skips_password_fields(self):
        """Password fields must never be exposed even if keyword matches."""
        value = self.reader._extract_value(self.snapshot, "password field")
        assert value is None

    def test_extract_nested_element(self):
        value = self.reader._extract_value(self.snapshot, "revenue line")
        assert value == "$50,000"

    def test_flatten_elements(self):
        flat = self.reader._flatten_elements(self.snapshot.elements)
        # 4 top-level + 1 nested = 5
        assert len(flat) == 5

    def test_count_elements(self):
        assert self.reader._count_elements(self.snapshot) == 5


# ── ReaderAgent HTTP integration (mocked) ────────────────────────────────

class TestReaderAgentHTTP:
    @pytest.mark.asyncio
    async def test_reader_returns_value_from_uigraph(self):
        """Reader agent calls UIGraph service and extracts a value."""
        reader = ReaderAgent()
        mock_response = {
            "snapshot": {
                "window_title": "Notepad",
                "process_name": "notepad.exe",
                "process_id": 100,
                "elements": [
                    {"name": "Text Area", "control_type": "Edit", "value": "$142,587.00",
                     "automation_id": "", "bounding_rect": {}, "children": [], "is_password": False},
                ],
            }
        }

        with patch("services.orchestrator.agents.reader.AsyncClient") as MockClient:
            mock_client = AsyncMock()
            mock_resp = MagicMock()
            mock_resp.json.return_value = mock_response
            mock_resp.raise_for_status = MagicMock()
            mock_client.post = AsyncMock(return_value=mock_resp)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value = mock_client

            result = await reader.execute({"app": "Notepad", "detail": "text area"})
            assert result["value"] == "$142,587.00"
            assert result["source"] == "uia"

    @pytest.mark.asyncio
    async def test_reader_handles_unavailable_service(self):
        """Reader degrades gracefully when UIGraph is down."""
        import httpx
        reader = ReaderAgent()

        with patch("services.orchestrator.agents.reader.AsyncClient") as MockClient:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(side_effect=httpx.ConnectError("Connection refused"))
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value = mock_client

            result = await reader.execute({"app": "Notepad", "detail": "some field"})
            assert result["source"] == "unavailable"
            assert "error" in result

    @pytest.mark.asyncio
    async def test_reader_requires_app_name(self):
        reader = ReaderAgent()
        result = await reader.execute({"detail": "something"})
        assert "error" in result


# ── WriterAgent HTTP tests (mocked) ─────────────────────────────────────

class TestWriterAgentHTTP:
    @pytest.mark.asyncio
    async def test_writer_sends_value(self):
        writer = WriterAgent()
        with patch("services.orchestrator.agents.writer.AsyncClient") as MockClient:
            mock_client = AsyncMock()
            mock_resp = MagicMock()
            mock_resp.json.return_value = {"success": True}
            mock_resp.raise_for_status = MagicMock()
            mock_client.post = AsyncMock(return_value=mock_resp)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value = mock_client

            result = await writer.execute({
                "app": "Excel",
                "detail": "cell B4",
                "value": "$142,587.00",
            })
            assert result["success"] is True
            assert result["source"] == "uia"

    @pytest.mark.asyncio
    async def test_writer_requires_app_and_value(self):
        writer = WriterAgent()
        result = await writer.execute({"app": "Excel", "detail": "B4"})
        assert "error" in result

    @pytest.mark.asyncio
    async def test_writer_handles_unavailable_service(self):
        import httpx
        writer = WriterAgent()
        with patch("services.orchestrator.agents.writer.AsyncClient") as MockClient:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(side_effect=httpx.ConnectError("Connection refused"))
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value = mock_client

            result = await writer.execute({
                "app": "Excel", "detail": "B4", "value": "100",
            })
            assert result["success"] is False


# ── VerifierAgent tests ──────────────────────────────────────────────────

class TestVerifierAgent:
    @pytest.mark.asyncio
    async def test_verifier_confirms_match(self):
        verifier = VerifierAgent()
        with patch.object(verifier._reader, "execute", new_callable=AsyncMock) as mock_read:
            mock_read.return_value = {"value": "$142,587.00"}
            result = await verifier.execute({
                "app": "Excel",
                "detail": "B4",
                "expected_value": "$142,587.00",
            })
            assert result["verified"] is True

    @pytest.mark.asyncio
    async def test_verifier_detects_mismatch(self):
        verifier = VerifierAgent()
        with patch.object(verifier._reader, "execute", new_callable=AsyncMock) as mock_read:
            mock_read.return_value = {"value": "WRONG"}
            result = await verifier.execute({
                "app": "Excel",
                "detail": "B4",
                "expected_value": "$142,587.00",
            })
            assert result["verified"] is False

    @pytest.mark.asyncio
    async def test_verifier_handles_missing_value(self):
        verifier = VerifierAgent()
        with patch.object(verifier._reader, "execute", new_callable=AsyncMock) as mock_read:
            mock_read.return_value = {"value": None}
            result = await verifier.execute({
                "app": "Excel",
                "detail": "B4",
                "expected_value": "$142,587.00",
            })
            assert result["verified"] is False

    @pytest.mark.asyncio
    async def test_verifier_requires_expected_value(self):
        verifier = VerifierAgent()
        result = await verifier.execute({"app": "Excel", "detail": "B4"})
        assert result["verified"] is False
        assert "error" in result
