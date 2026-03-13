"""
TELOS Orchestrator — shared data models.

All Pydantic models used across the orchestrator for request validation,
event emission, and inter-service contracts.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, field_validator


# ── Enums ────────────────────────────────────────────────────────────────

class TaskStatus(str, Enum):
    PENDING = "pending"
    ROUTING = "routing"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class AgentRole(str, Enum):
    PLANNER = "planner"
    READER = "reader"
    WRITER = "writer"
    VERIFIER = "verifier"
    PRIVACY = "privacy"
    VISION = "vision"


class ProviderName(str, Enum):
    AZURE = "azure"
    GEMINI = "gemini"
    AZURE_SK = "azure_sk"


# ── Core Models ──────────────────────────────────────────────────────────

class TaskRequest(BaseModel):
    """Inbound task from the frontend command bar."""
    task: str = Field(..., max_length=10_000, description="Natural-language task instruction")
    context: dict[str, Any] = Field(default_factory=dict, description="Optional additional context")

    @field_validator("task")
    @classmethod
    def strip_dangerous_content(cls, v: str) -> str:
        import re
        v = re.sub(r"<script[^>]*>.*?</script>", "", v, flags=re.IGNORECASE | re.DOTALL)
        v = re.sub(r"<[^>]+>", "", v)
        return v.strip()


class TaskRecord(BaseModel):
    """Internal representation of a task throughout its lifecycle."""
    id: str = Field(default_factory=lambda: uuid.uuid4().hex[:12])
    task: str
    status: TaskStatus = TaskStatus.PENDING
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    result: Any | None = None
    error: str | None = None
    steps: list[TaskStep] = Field(default_factory=list)
    privacy_summary: PrivacySummary | None = None


class TaskStep(BaseModel):
    """A single step within a task execution."""
    agent: AgentRole
    action: str
    status: TaskStatus = TaskStatus.PENDING
    started_at: str | None = None
    completed_at: str | None = None
    detail: str = ""


class PrivacySummary(BaseModel):
    """Per-task privacy metrics visible on the dashboard."""
    local_operations: int = 0
    cloud_calls: int = 0
    bytes_sent: int = 0
    bytes_received: int = 0
    fields_masked: int = 0
    pii_blocked: int = 0


# ── Provider Models ──────────────────────────────────────────────────────

class LLMRequest(BaseModel):
    """Normalized request to any LLM provider."""
    system_prompt: str = ""
    user_prompt: str
    temperature: float = 0.2
    max_tokens: int = 2048
    image_data: bytes | None = None
    image_mime: str | None = None


class LLMResponse(BaseModel):
    """Normalized response from any LLM provider."""
    content: str
    provider: ProviderName
    model: str
    usage_prompt_tokens: int = 0
    usage_completion_tokens: int = 0
    bytes_sent: int = 0
    bytes_received: int = 0


# ── Event Models ─────────────────────────────────────────────────────────

class EventType(str, Enum):
    TASK_CREATED = "task_created"
    TASK_STATUS = "task_status"
    STEP_UPDATE = "step_update"
    PRIVACY_UPDATE = "privacy_update"
    AGENT_STATUS = "agent_status"
    SYSTEM_STATE = "system_state"
    UIGRAPH_UPDATE = "uigraph_update"
    ERROR = "error"


class TelosEvent(BaseModel):
    """SSE event pushed to the frontend."""
    event_type: EventType
    task_id: str | None = None
    payload: dict[str, Any] = Field(default_factory=dict)
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


# ── UIGraph Models ───────────────────────────────────────────────────────

class UIElement(BaseModel):
    """A single UI Automation element."""
    automation_id: str = ""
    name: str = ""
    control_type: str = ""
    value: str = ""
    bounding_rect: dict[str, int] = Field(default_factory=dict)
    children: list[UIElement] = Field(default_factory=list)
    is_password: bool = False


class UISnapshot(BaseModel):
    """Snapshot of a window's accessible UI tree."""
    window_title: str
    process_name: str
    process_id: int
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    elements: list[UIElement] = Field(default_factory=list)


# ── Scheduler Models ─────────────────────────────────────────────────────

class ScheduledJob(BaseModel):
    """A repeatable scheduled task."""
    id: str = Field(default_factory=lambda: uuid.uuid4().hex[:12])
    name: str
    cron: str
    task: str = Field(..., max_length=10_000)
    enabled: bool = True
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    last_run: str | None = None
    next_run: str | None = None


# Resolve forward references
TaskRecord.model_rebuild()
UIElement.model_rebuild()
