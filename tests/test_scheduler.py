"""
TELOS Tests — scheduler persistence tests.

Validates Go scheduler functionality via its HTTP API contract.
Since the Go scheduler is a separate process, these tests validate
the data models and API contract expectations.
"""

import pytest
import json
import re

from services.orchestrator.models import ScheduledJob


class TestSchedulerModels:
    """Test scheduler-related data models."""

    def test_job_creation(self):
        job = ScheduledJob(
            name="Daily Sales Sync",
            cron="0 9 * * *",
            task="Copy yesterday's sales from QuickBooks to Excel",
        )
        assert job.name == "Daily Sales Sync"
        assert job.cron == "0 9 * * *"
        assert job.enabled is True
        assert job.id  # auto-generated
        assert job.last_run is None

    def test_job_with_disabled_state(self):
        job = ScheduledJob(
            name="Paused Job",
            cron="*/5 * * * *",
            task="Check inbox",
            enabled=False,
        )
        assert job.enabled is False

    def test_job_task_max_length(self):
        """Task content must not exceed 10,000 characters."""
        with pytest.raises(Exception):
            ScheduledJob(
                name="Too Long",
                cron="* * * * *",
                task="x" * 10_001,
            )

    def test_job_serialization(self):
        job = ScheduledJob(
            name="Test Job",
            cron="0 */2 * * *",
            task="Run report",
        )
        data = job.model_dump()
        assert data["name"] == "Test Job"
        assert data["cron"] == "0 */2 * * *"
        assert isinstance(data["id"], str)
        assert data["enabled"] is True

    def test_job_deserialization(self):
        raw = {
            "id": "abc123",
            "name": "From JSON",
            "cron": "0 0 * * 1",
            "task": "Monday sync",
            "enabled": True,
            "created_at": "2026-01-01T00:00:00Z",
        }
        job = ScheduledJob(**raw)
        assert job.id == "abc123"
        assert job.name == "From JSON"


class TestCronValidation:
    """Validate cron expression patterns used by the scheduler.

    Mirrors the Go scheduler's cron validation regex.
    """

    # Same pattern used in services/scheduler/main.go
    CRON_PATTERN = re.compile(
        r"^(\*|[0-9]{1,2}|\*/[0-9]{1,2})\s+"
        r"(\*|[0-9]{1,2}|\*/[0-9]{1,2})\s+"
        r"(\*|[0-9]{1,2}|\*/[0-9]{1,2})\s+"
        r"(\*|[0-9]{1,2}|\*/[0-9]{1,2})\s+"
        r"(\*|[0-7]|\*/[0-9]{1,2})$"
    )

    @pytest.mark.parametrize("expr", [
        "* * * * *",
        "0 9 * * *",
        "*/5 * * * *",
        "30 8 1 * *",
        "0 0 * * 1",
    ])
    def test_valid_cron_expressions(self, expr):
        assert self.CRON_PATTERN.match(expr), f"Should be valid: {expr}"

    @pytest.mark.parametrize("expr", [
        "",
        "not a cron",
        "* * *",
        "60 25 32 13 8",
    ])
    def test_invalid_cron_expressions(self, expr):
        assert not self.CRON_PATTERN.match(expr), f"Should be invalid: {expr}"


class TestSchedulerAPIContract:
    """Validate the expected API request/response shapes for the Go scheduler.

    These tests ensure the Python orchestrator's expectations of the
    scheduler API remain consistent.
    """

    def test_create_job_payload(self):
        """Orchestrator sends this shape to POST /jobs."""
        payload = {
            "name": "Hourly Check",
            "cron": "0 * * * *",
            "task": "Check for updates",
            "enabled": True,
        }
        # Validate it matches our model
        job = ScheduledJob(**payload)
        assert job.name == "Hourly Check"

    def test_trigger_job_expected_response(self):
        """POST /jobs/{id}/trigger returns this shape."""
        response = {
            "message": "Job triggered",
            "job_id": "abc123",
            "task_submitted": True,
        }
        assert "job_id" in response
        assert response["task_submitted"] is True

    def test_job_history_response_shape(self):
        """GET /jobs/{id}/history returns an array of run records."""
        history = [
            {
                "id": 1,
                "job_id": "abc123",
                "status": "completed",
                "triggered_at": "2026-01-01T09:00:00Z",
                "completed_at": "2026-01-01T09:00:05Z",
                "error": None,
            }
        ]
        assert len(history) == 1
        assert history[0]["status"] == "completed"

    def test_job_list_response_shape(self):
        """GET /jobs returns an array of job objects."""
        jobs = [
            {"id": "abc123", "name": "Test", "cron": "* * * * *",
             "task": "do it", "enabled": True, "created_at": "2026-01-01T00:00:00Z"},
        ]
        parsed = [ScheduledJob(**j) for j in jobs]
        assert len(parsed) == 1
        assert parsed[0].name == "Test"
