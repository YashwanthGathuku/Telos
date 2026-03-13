"""
TELOS Tests — Memory store tests.
"""

import os
import tempfile
import pytest
from unittest.mock import patch
from services.orchestrator.memory.store import MemoryStore


@pytest.fixture
def memory_store(tmp_path):
    db_path = str(tmp_path / "test.db")
    with patch("services.orchestrator.memory.store.get_settings") as mock_settings:
        mock_settings.return_value.telos_db_path = db_path
        store = MemoryStore()
        yield store
        store.close()


class TestMemoryStore:
    def test_save_and_get_task(self, memory_store):
        memory_store.save_task("t1", "Test task", "completed", "success")
        task = memory_store.get_task("t1")
        assert task is not None
        assert task["task"] == "Test task"
        assert task["status"] == "completed"

    def test_get_nonexistent_task(self, memory_store):
        assert memory_store.get_task("nonexistent") is None

    def test_recent_tasks(self, memory_store):
        for i in range(5):
            memory_store.save_task(f"t{i}", f"Task {i}", "completed")
        recent = memory_store.recent_tasks(3)
        assert len(recent) == 3

    def test_context_store(self, memory_store):
        memory_store.set_context("last_app", "Excel")
        assert memory_store.get_context("last_app") == "Excel"

    def test_context_overwrite(self, memory_store):
        memory_store.set_context("key", "value1")
        memory_store.set_context("key", "value2")
        assert memory_store.get_context("key") == "value2"

    def test_context_nonexistent(self, memory_store):
        assert memory_store.get_context("missing") is None

    def test_update_task(self, memory_store):
        memory_store.save_task("t1", "Task 1", "pending")
        memory_store.save_task("t1", "Task 1", "completed", "done")
        task = memory_store.get_task("t1")
        assert task["status"] == "completed"
        assert task["result"] == "done"
