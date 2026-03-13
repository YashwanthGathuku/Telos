"""
TELOS Task Router — central orchestration engine.

Receives tasks, runs them through the planner, then executes each step
through the appropriate specialist agent, emitting events throughout.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from services.orchestrator.models import (
    TaskRecord, TaskStatus, TaskStep, AgentRole, PrivacySummary, EventType, TelosEvent,
)
from services.orchestrator.bus.a2a import get_bus
from services.orchestrator.providers.registry import get_provider
from services.orchestrator.providers.provider_base import ProviderBase
from services.orchestrator.agents.planner import PlannerAgent
from services.orchestrator.agents.reader import ReaderAgent
from services.orchestrator.agents.writer import WriterAgent
from services.orchestrator.agents.verifier import VerifierAgent
from services.orchestrator.agents.vision import VisionAgent
from services.orchestrator.privacy.egress import get_egress_logger
from services.orchestrator.memory.store import get_memory

logger = logging.getLogger("telos.router")


class TaskRouter:
    """Orchestrates task decomposition and step execution."""

    def __init__(self) -> None:
        self._provider: ProviderBase = get_provider()
        self._planner = PlannerAgent(self._provider)
        self._reader = ReaderAgent()
        self._writer = WriterAgent()
        self._verifier = VerifierAgent()
        self._vision = VisionAgent()
        self._bus = get_bus()
        self._egress = get_egress_logger()
        self._memory = get_memory()
        self._tasks: dict[str, TaskRecord] = {}

    async def submit(self, task_text: str) -> TaskRecord:
        """Accept a new task and begin asynchronous execution."""
        record = TaskRecord(task=task_text, status=TaskStatus.ROUTING)
        self._tasks[record.id] = record

        # Save to memory
        self._memory.save_task(record.id, task_text, record.status.value)

        # Emit creation event
        await self._bus.publish(TelosEvent(
            event_type=EventType.TASK_CREATED,
            task_id=record.id,
            payload={"task": task_text, "status": record.status.value},
        ))

        # Execute the task
        try:
            await self._execute(record)
        except Exception as exc:
            record.status = TaskStatus.FAILED
            record.error = str(exc)
            logger.exception("Task %s failed", record.id)
            await self._emit_status(record)

        return record

    async def _execute(self, record: TaskRecord) -> None:
        """Run planner → reader → writer → verifier pipeline."""
        # Step 1: Plan
        record.status = TaskStatus.ROUTING
        await self._emit_status(record)

        plan_result = await self._planner.execute({"task": record.task})

        # Track egress from planning
        if "provider_usage" in plan_result:
            pu = plan_result["provider_usage"]
            self._egress.record(
                destination=f"llm/{self._provider.provider_name()}",
                bytes_sent=pu.get("bytes_sent", 0),
                bytes_received=pu.get("bytes_received", 0),
                provider=self._provider.provider_name(),
                task_id=record.id,
            )

        steps = plan_result.get("steps", [])
        if not steps:
            record.status = TaskStatus.FAILED
            record.error = plan_result.get("error", "Planner returned no steps")
            await self._emit_status(record)
            return

        # Build task steps
        privacy = PrivacySummary(
            cloud_calls=1,
            bytes_sent=plan_result.get("provider_usage", {}).get("bytes_sent", 0),
            bytes_received=plan_result.get("provider_usage", {}).get("bytes_received", 0),
            fields_masked=plan_result.get("privacy", {}).get("fields_masked", 0),
            pii_blocked=plan_result.get("privacy", {}).get("pii_blocked", 0),
        )

        for step_data in steps:
            agent_name = step_data.get("agent", "reader")
            try:
                agent_role = AgentRole(agent_name)
            except ValueError:
                agent_role = AgentRole.READER

            record.steps.append(TaskStep(
                agent=agent_role,
                action=step_data.get("action", ""),
                detail=step_data.get("detail", ""),
            ))

        # Step 2: Execute each step
        record.status = TaskStatus.EXECUTING
        await self._emit_status(record)
        extracted_value: str | None = None

        for i, step in enumerate(record.steps):
            step.status = TaskStatus.EXECUTING
            step.started_at = datetime.now(timezone.utc).isoformat()

            await self._bus.publish(TelosEvent(
                event_type=EventType.STEP_UPDATE,
                task_id=record.id,
                payload={"step_index": i, "agent": step.agent.value, "status": "executing"},
            ))

            step_context: dict[str, Any] = {
                "app": steps[i].get("app", ""),
                "detail": step.detail,
                "action": step.action,
            }

            if step.agent == AgentRole.READER:
                result = await self._reader.execute(step_context)
                extracted_value = result.get("value")
                privacy.local_operations += 1
                step.detail = f"Read: {extracted_value}"

            elif step.agent == AgentRole.WRITER:
                step_context["value"] = extracted_value or ""
                result = await self._writer.execute(step_context)
                privacy.local_operations += 1

            elif step.agent == AgentRole.VERIFIER:
                step_context["expected_value"] = extracted_value or ""
                result = await self._verifier.execute(step_context)
                privacy.local_operations += 1

            elif step.agent == AgentRole.VISION:
                result = await self._vision.execute(step_context)
                extracted_value = result.get("value")
                privacy.cloud_calls += 1
                step.detail = f"Vision extracted: {extracted_value}"

            else:
                result = {"skipped": True}

            step.status = TaskStatus.COMPLETED
            step.completed_at = datetime.now(timezone.utc).isoformat()

            await self._bus.publish(TelosEvent(
                event_type=EventType.STEP_UPDATE,
                task_id=record.id,
                payload={"step_index": i, "agent": step.agent.value, "status": "completed", "result": result},
            ))

        # Finalize
        record.status = TaskStatus.COMPLETED
        record.result = {"extracted_value": extracted_value, "steps_completed": len(record.steps)}
        record.privacy_summary = privacy
        record.updated_at = datetime.now(timezone.utc).isoformat()

        self._memory.save_task(record.id, record.task, record.status.value, str(record.result))

        await self._bus.publish(TelosEvent(
            event_type=EventType.PRIVACY_UPDATE,
            task_id=record.id,
            payload=privacy.model_dump(),
        ))
        await self._emit_status(record)

    async def _emit_status(self, record: TaskRecord) -> None:
        await self._bus.publish(TelosEvent(
            event_type=EventType.TASK_STATUS,
            task_id=record.id,
            payload={
                "status": record.status.value,
                "error": record.error,
                "updated_at": record.updated_at,
            },
        ))

    def get_task(self, task_id: str) -> TaskRecord | None:
        return self._tasks.get(task_id)

    def active_tasks(self) -> list[TaskRecord]:
        return list(self._tasks.values())
