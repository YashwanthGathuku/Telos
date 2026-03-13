"""
TELOS Tests — Egress logger tests.
"""

import pytest
from unittest.mock import patch
from services.orchestrator.privacy.egress import EgressLogger


@pytest.fixture
def egress_logger(tmp_path):
    log_path = str(tmp_path / "egress.jsonl")
    with patch("services.orchestrator.privacy.egress.get_settings") as mock_settings:
        mock_settings.return_value.telos_egress_log = log_path
        logger = EgressLogger()
        yield logger


class TestEgressLogger:
    def test_record_event(self, egress_logger):
        rec = egress_logger.record(
            destination="llm/azure",
            bytes_sent=1024,
            bytes_received=2048,
            provider="azure",
            task_id="t1",
        )
        assert rec.destination == "llm/azure"
        assert rec.bytes_sent == 1024

    def test_summary(self, egress_logger):
        egress_logger.record("dest1", 100, 200, "azure")
        egress_logger.record("dest2", 300, 400, "gemini")

        summary = egress_logger.summary()
        assert summary["total_calls"] == 2
        assert summary["total_bytes_sent"] == 400
        assert summary["total_bytes_received"] == 600

    def test_recent(self, egress_logger):
        for i in range(30):
            egress_logger.record(f"dest{i}", 100, 200, "azure")

        recent = egress_logger.recent(10)
        assert len(recent) == 10

    def test_persistent_log(self, egress_logger, tmp_path):
        egress_logger.record("test", 50, 100, "azure")
        log_file = tmp_path / "egress.jsonl"
        assert log_file.exists()
        content = log_file.read_text()
        assert "test" in content
        assert "50" in content
