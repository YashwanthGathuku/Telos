"""
TELOS Tests — Orchestrator routing and model validation tests.
"""

import pytest
from services.orchestrator.models import (
    TaskRequest,
    TaskRecord,
    TaskStatus,
    TaskStep,
    AgentRole,
    PrivacySummary,
    TelosEvent,
    EventType,
    UIElement,
    UISnapshot,
    ScheduledJob,
)


class TestTaskRequest:
    def test_valid_task(self):
        req = TaskRequest(task="Copy Q1 sales total to Excel")
        assert req.task == "Copy Q1 sales total to Excel"

    def test_strips_html_tags(self):
        req = TaskRequest(task="<b>Bold</b> task <script>alert('x')</script>")
        assert "<script>" not in req.task
        assert "<b>" not in req.task
        assert "Bold" in req.task

    def test_max_length(self):
        with pytest.raises(Exception):
            TaskRequest(task="x" * 10_001)

    def test_empty_context(self):
        req = TaskRequest(task="Test")
        assert req.context == {}


class TestTaskRecord:
    def test_default_values(self):
        record = TaskRecord(task="Test task")
        assert record.status == TaskStatus.PENDING
        assert record.id  # auto-generated
        assert record.created_at
        assert record.steps == []
        assert record.result is None

    def test_with_steps(self):
        step = TaskStep(agent=AgentRole.READER, action="read_field", detail="Q1 sales")
        record = TaskRecord(task="Test", steps=[step])
        assert len(record.steps) == 1
        assert record.steps[0].agent == AgentRole.READER


class TestPrivacySummary:
    def test_default_zeroes(self):
        ps = PrivacySummary()
        assert ps.local_operations == 0
        assert ps.cloud_calls == 0
        assert ps.bytes_sent == 0
        assert ps.fields_masked == 0
        assert ps.pii_blocked == 0


class TestTelosEvent:
    def test_event_creation(self):
        event = TelosEvent(
            event_type=EventType.TASK_CREATED,
            task_id="abc123",
            payload={"task": "Test"},
        )
        assert event.event_type == EventType.TASK_CREATED
        assert event.task_id == "abc123"
        assert event.timestamp


class TestUIElement:
    def test_password_field(self):
        elem = UIElement(
            name="Password",
            control_type="Edit",
            is_password=True,
            value="***MASKED***",
        )
        assert elem.is_password is True
        assert elem.value == "***MASKED***"

    def test_nested_children(self):
        child = UIElement(name="Child", control_type="Text")
        parent = UIElement(name="Parent", control_type="Group", children=[child])
        assert len(parent.children) == 1


class TestUISnapshot:
    def test_snapshot_creation(self):
        snap = UISnapshot(
            window_title="Excel - Q1 Report",
            process_name="EXCEL.EXE",
            process_id=1234,
        )
        assert snap.window_title == "Excel - Q1 Report"
        assert snap.elements == []


class TestScheduledJob:
    def test_job_creation(self):
        job = ScheduledJob(name="Daily sync", cron="0 9 * * *", task="Sync data")
        assert job.name == "Daily sync"
        assert job.enabled is True
