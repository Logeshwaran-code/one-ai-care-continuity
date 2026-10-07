"""SCAFFOLD (module 8, future work): Clinician Copilot. Interfaces only; no model is wired in.
Contract: every draft is created with status="draft" and can only be finalised by a clinician (see VisitSummary approve flow).
All generated text must pass app.guardrails.validate_output before it is stored."""
from dataclasses import dataclass
from typing import Protocol


@dataclass
class NoteDraft:
    patient_id: int
    text: str
    sources: list[str]  # ids of measurements/medications/summaries used (traceability)
    status: str = "draft"  # draft -> approved (by a doctor) | rejected


class ClinicianCopilot(Protocol):
    async def draft_visit_note(self, patient_id: int, clinician_id: int) -> NoteDraft: ...

    async def approve(self, draft: NoteDraft, clinician_id: int, edited_text: str | None = None) -> NoteDraft: ...
