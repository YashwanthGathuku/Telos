"""
TELOS Tests — Firestore memory backend tests.

Verifies the cloud backend implements the same interface as local SQLite
and handles dict conversion correctly.
"""

from typing import Any
import pytest
from services.orchestrator.memory.firestore_store import FirestoreStore


class MockDocumentSnapshot:
    def __init__(self, exists: bool, data: dict[str, Any] | None = None):
        self.exists = exists
        self._data = data

    def to_dict(self):
        return self._data


class MockDocumentReference:
    def __init__(self, data_store: dict, key: str):
        self._store = data_store
        self._key = key

    def get(self):
        if self._key in self._store:
            return MockDocumentSnapshot(True, self._store[self._key])
        return MockDocumentSnapshot(False)

    def set(self, data: dict[str, Any], merge: bool = False):
        if merge and self._key in self._store:
            self._store[self._key].update(data)
        else:
            self._store[self._key] = data


class MockCollectionReference:
    def __init__(self, data_store: dict):
        self._store = data_store

    def document(self, doc_id: str):
        return MockDocumentReference(self._store, doc_id)

    def order_by(self, *args, **kwargs):
        return self

    def limit(self, *args, **kwargs):
        return self

    def stream(self):
        # Return all as snapshots (simulated)
        return [MockDocumentSnapshot(True, v) for v in self._store.values()]


class MockFirestoreClient:
    def __init__(self, *args, **kwargs):
        self._collections: dict[str, dict] = {}

    def collection(self, name: str):
        if name not in self._collections:
            self._collections[name] = {}
        return MockCollectionReference(self._collections[name])


@pytest.fixture
def firestore_store(monkeypatch):
    import google.cloud.firestore
    monkeypatch.setattr(google.cloud.firestore, "Client", MockFirestoreClient)
    
    monkeypatch.setenv("GOOGLE_CLOUD_PROJECT", "test-project")
    monkeypatch.setenv("FIRESTORE_COLLECTION", "test_tasks")
    
    from services.orchestrator.config import get_settings
    get_settings.cache_clear()
    
    store = FirestoreStore()
    return store


def test_save_and_get_task(firestore_store):
    firestore_store.save_task("task-123", "Do something", "pending", "none")
    task = firestore_store.get_task("task-123")
    
    assert task is not None
    assert task["task_id"] == "task-123"
    assert task["task"] == "Do something"
    assert task["status"] == "pending"


def test_recent_tasks(firestore_store):
    firestore_store.save_task("t1", "Task 1", "completed")
    firestore_store.save_task("t2", "Task 2", "pending")
    
    tasks = firestore_store.recent_tasks(limit=10)
    assert len(tasks) == 2


def test_get_nonexistent_task(firestore_store):
    assert firestore_store.get_task("missing") is None


def test_save_and_get_context(firestore_store):
    firestore_store.set_context("auth_token", "secret123")
    assert firestore_store.get_context("auth_token") == "secret123"


def test_get_nonexistent_context(firestore_store):
    assert firestore_store.get_context("missing") is None
