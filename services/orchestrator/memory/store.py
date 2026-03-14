"""
TELOS Memory Layer — lightweight SQLite-backed local memory.

Stores task history, context snippets, and application state.
All data stays local by default (./telos_memory_db/).
"""

from __future__ import annotations

import sqlite3
import logging
from threading import RLock
from datetime import datetime, timezone
from pathlib import Path

from services.orchestrator.config import get_settings

logger = logging.getLogger("telos.memory")


class MemoryStore:
    """Local SQLite memory store for task history and context."""

    def __init__(self) -> None:
        db_path = Path(get_settings().telos_db_path)
        db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(db_path), check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._lock = RLock()
        self._configure_connection()
        self._init_tables()

    def _configure_connection(self) -> None:
        self._conn.execute("PRAGMA journal_mode=WAL;")
        self._conn.execute("PRAGMA synchronous=NORMAL;")
        self._conn.execute("PRAGMA foreign_keys=ON;")
        self._conn.execute("PRAGMA busy_timeout=5000;")

    def _init_tables(self) -> None:
        with self._lock:
            self._conn.executescript("""
                CREATE TABLE IF NOT EXISTS task_history (
                    id TEXT PRIMARY KEY,
                    task TEXT NOT NULL,
                    status TEXT NOT NULL,
                    result TEXT,
                    error TEXT,
                    created_at TEXT NOT NULL,
                    completed_at TEXT
                );
                CREATE TABLE IF NOT EXISTS context_store (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
            """)
            self._conn.commit()

    def save_task(self, task_id: str, task: str, status: str, result: str | None = None, error: str | None = None) -> None:
        now = datetime.now(timezone.utc).isoformat()
        completed_at = now if status in ("completed", "failed") else None
        with self._lock:
            self._conn.execute(
                """
                INSERT INTO task_history (id, task, status, result, error, created_at, completed_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    task = excluded.task,
                    status = excluded.status,
                    result = excluded.result,
                    error = excluded.error,
                    completed_at = excluded.completed_at
                """,
                (task_id, task, status, result, error, now, completed_at),
            )
            self._conn.commit()

    def get_task(self, task_id: str) -> dict | None:
        with self._lock:
            row = self._conn.execute("SELECT * FROM task_history WHERE id = ?", (task_id,)).fetchone()
            return dict(row) if row else None

    def recent_tasks(self, limit: int = 20) -> list[dict]:
        with self._lock:
            rows = self._conn.execute(
                "SELECT * FROM task_history ORDER BY created_at DESC LIMIT ?", (limit,)
            ).fetchall()
            return [dict(r) for r in rows]

    def set_context(self, key: str, value: str) -> None:
        now = datetime.now(timezone.utc).isoformat()
        with self._lock:
            self._conn.execute(
                "INSERT OR REPLACE INTO context_store (key, value, updated_at) VALUES (?, ?, ?)",
                (key, value, now),
            )
            self._conn.commit()

    def get_context(self, key: str) -> str | None:
        with self._lock:
            row = self._conn.execute("SELECT value FROM context_store WHERE key = ?", (key,)).fetchone()
            return row["value"] if row else None

    def close(self) -> None:
        with self._lock:
            self._conn.close()


_store = None


def get_memory():
    global _store
    if _store is None:
        from services.orchestrator.config import get_settings
        backend = get_settings().telos_memory_backend
        if backend.lower() == "firestore":
            from services.orchestrator.memory.firestore_store import FirestoreStore
            _store = FirestoreStore()
        else:
            _store = MemoryStore()
    return _store
