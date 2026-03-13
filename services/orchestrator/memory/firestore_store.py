"""
TELOS Firestore Memory Store — cloud-backed task/context persistence.

Uses Google Cloud Firestore as a GCP service for hackathon compliance.
Implements the same interface as the local SQLite MemoryStore so the
orchestrator can switch backends via TELOS_MEMORY_BACKEND=firestore|sqlite.
"""

from __future__ import annotations

import logging
from typing import Any

from services.orchestrator.config import get_settings

logger = logging.getLogger("telos.memory.firestore")


class FirestoreStore:
    """Cloud Firestore memory backend.

    Mirrors MemoryStore interface: save_task, get_task, recent_tasks,
    set_context, get_context, close.
    """

    def __init__(self) -> None:
        from google.cloud import firestore

        s = get_settings()
        project = s.google_cloud_project or None
        self._db = firestore.Client(project=project)
        self._collection = s.firestore_collection
        logger.info("Firestore store initialized (project=%s, collection=%s)", project, self._collection)

    @property
    def _tasks_ref(self):
        return self._db.collection(self._collection)

    @property
    def _context_ref(self):
        return self._db.collection(f"{self._collection}_context")

    def save_task(self, task_id: str, task: str, status: str, result: str | None = None) -> None:
        """Create or update a task document."""
        self._tasks_ref.document(task_id).set(
            {
                "task_id": task_id,
                "task": task,
                "status": status,
                "result": result or "",
                "updated_at": _now_iso(),
            },
            merge=True,
        )

    def get_task(self, task_id: str) -> dict[str, Any] | None:
        """Retrieve a task by ID."""
        doc = self._tasks_ref.document(task_id).get()
        if doc.exists:
            return doc.to_dict()
        return None

    def recent_tasks(self, limit: int = 20) -> list[dict[str, Any]]:
        """Get most recent tasks ordered by update time."""
        docs = (
            self._tasks_ref
            .order_by("updated_at", direction="DESCENDING")
            .limit(limit)
            .stream()
        )
        return [doc.to_dict() for doc in docs]

    def set_context(self, key: str, value: str) -> None:
        """Store a context key-value pair."""
        self._context_ref.document(key).set({"key": key, "value": value})

    def get_context(self, key: str) -> str | None:
        """Retrieve a context value by key."""
        doc = self._context_ref.document(key).get()
        if doc.exists:
            data = doc.to_dict()
            return data.get("value")
        return None

    def close(self) -> None:
        """No-op for Firestore (stateless client)."""
        pass


def _now_iso() -> str:
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat()
