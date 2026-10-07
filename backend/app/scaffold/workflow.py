"""SCAFFOLD (module 9, future work): health-worker workflow engine. Today tasks are created by MedGuard/CareLoop/wellbeing
rules (see routers/patient.py). This interface describes the intended rule-driven engine: declarative triggers, SLAs, escalation."""
from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class WorkflowRule:
    id: str
    trigger: str  # e.g. "careloop.flag:ADH-STREAK" | "medguard.alert:major"
    task_title: str
    assignee_role: str  # health_worker | doctor
    due_hours: int
    escalate_to_role: str | None = None


class WorkflowEngine(Protocol):
    async def on_event(self, event: str, patient_id: int, payload: dict[str, object]) -> list[int]:
        """Return ids of tasks created."""
        ...

    async def escalate_overdue(self) -> int: ...
