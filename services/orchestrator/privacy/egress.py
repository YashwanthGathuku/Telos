"""
TELOS Egress Logger — tracks all outbound API traffic.

Logs destination, byte counts, and timestamps for every external request.
Provides data for the privacy dashboard's egress monitor.
"""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path

from pydantic import BaseModel

from services.orchestrator.config import get_settings

logger = logging.getLogger("telos.privacy.egress")


class EgressRecord(BaseModel):
    """Single egress event record."""
    destination: str
    bytes_sent: int
    bytes_received: int
    timestamp: str
    provider: str
    task_id: str = ""


class EgressLogger:
    """Append-only JSONL egress log and in-memory aggregator."""

    def __init__(self) -> None:
        self._log_path = Path(get_settings().telos_egress_log)
        self._log_path.parent.mkdir(parents=True, exist_ok=True)
        self._records: list[EgressRecord] = []
        self._total_bytes_sent: int = 0
        self._total_bytes_received: int = 0
        self._total_calls: int = 0

    def record(
        self,
        destination: str,
        bytes_sent: int,
        bytes_received: int,
        provider: str,
        task_id: str = "",
    ) -> EgressRecord:
        """Log an egress event."""
        rec = EgressRecord(
            destination=destination,
            bytes_sent=bytes_sent,
            bytes_received=bytes_received,
            timestamp=datetime.now(timezone.utc).isoformat(),
            provider=provider,
            task_id=task_id,
        )
        self._records.append(rec)
        self._total_bytes_sent += bytes_sent
        self._total_bytes_received += bytes_received
        self._total_calls += 1

        # Append to JSONL file
        try:
            with open(self._log_path, "a", encoding="utf-8") as f:
                f.write(rec.model_dump_json() + "\n")
        except OSError:
            logger.warning("Failed to write egress log to %s", self._log_path)

        logger.info(
            "Egress: %s | sent=%d recv=%d | provider=%s",
            destination, bytes_sent, bytes_received, provider,
        )
        return rec

    def summary(self) -> dict[str, int]:
        """Aggregate egress metrics for the dashboard."""
        return {
            "total_calls": self._total_calls,
            "total_bytes_sent": self._total_bytes_sent,
            "total_bytes_received": self._total_bytes_received,
        }

    def recent(self, n: int = 20) -> list[EgressRecord]:
        """Return the most recent N egress records."""
        return list(self._records[-n:])


# Module-level singleton
_egress: EgressLogger | None = None


def get_egress_logger() -> EgressLogger:
    global _egress
    if _egress is None:
        _egress = EgressLogger()
    return _egress
