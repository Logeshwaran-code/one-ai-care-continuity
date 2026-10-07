"""Patient-scoped endpoints: consent, medications (MedGuard), measurements/doses (CareLoop), family dashboard,
tasks, visit summaries, FHIR export, voice logging, antibiotic courses, screenings."""
import json
from datetime import date, datetime, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel, Field
from sqlalchemy import delete, func, select

from app.careloop import engine as cl
from app.careloop import summary as sm
from app.deps import ALL_SCOPES, CurrentUser, Session, authorize, profile_lists, require_roles
from app.guardrails import ESCALATE, guarded_generate
from app.llm import gateway
from app.medguard.engine import Alert, Resolution, get_kb
from app.models import (
    Appointment,
    AuditLog,
    Consent,
    DoseLog,
    Measurement,
    Medication,
    PatientProfile,
    RefreshToken,
    Screening,
    Task,
    User,
    VisitSummary,
    utcnow,
)
from app.wellbeing import score_screening

router = APIRouter(tags=["patient"])
SLOTS = ("morning", "afternoon", "evening", "night")
STAFF = ("doctor", "health_worker")
Doctor = Annotated[User, Depends(require_roles("doctor"))]
Staff = Annotated[User, Depends(require_roles(*STAFF))]


# ------------------------------------------------------------------------------------ consent
class ConsentIn(BaseModel):
    grantee_email: str
    scopes: list[str]


@router.post("/consents", status_code=201)
async def grant(body: ConsentIn, user: CurrentUser, session: Session) -> dict[str, object]:
    if user.role != "patient":
        raise HTTPException(403, "Only patients grant consent")
    if not set(body.scopes) <= set(ALL_SCOPES) or not body.scopes:
        raise HTTPException(422, f"scopes must be a non-empty subset of {ALL_SCOPES}")
    g = await session.scalar(select(User).where(User.email == body.grantee_email.lower()))
    if g is None or g.role == "admin" or g.id == user.id:
        raise HTTPException(404, "Grantee not found")
    old = await session.scalars(select(Consent).where(Consent.patient_id == user.id, Consent.grantee_id == g.id, Consent.revoked_at.is_(None)))
    for c in old:
        c.revoked_at = utcnow()
    c = Consent(patient_id=user.id, grantee_id=g.id, scopes=body.scopes)
    session.add(c)
    session.add(AuditLog(actor_id=user.id, actor_role=user.role, patient_id=user.id, action="consent_grant", scope=",".join(body.scopes)))
    await session.commit()
    return {"id": c.id, "grantee": g.email, "scopes": c.scopes}


@router.get("/consents")
async def list_consents(user: CurrentUser, session: Session) -> list[dict[str, object]]:
    rows = (await session.execute(select(Consent, User).join(User, User.id == Consent.grantee_id)
                                  .where(Consent.patient_id == user.id, Consent.revoked_at.is_(None)))).all()
    return [{"id": c.id, "grantee": u.email, "name": u.name, "role": u.role, "scopes": c.scopes} for c, u in rows]


@router.delete("/consents/{cid}", status_code=204)
async def revoke(cid: int, user: CurrentUser, session: Session) -> Response:
    c = await session.get(Consent, cid)
    if c is None or c.patient_id != user.id:
        raise HTTPException(404, "Not found")
    c.revoked_at = utcnow()
    session.add(AuditLog(actor_id=user.id, actor_role=user.role, patient_id=user.id, action="consent_revoke"))
    await session.commit()
    return Response(status_code=204)


@router.get("/patients")
async def my_patients(user: CurrentUser, session: Session) -> list[dict[str, object]]:
    """Patients who have shared data with me (or myself, for a patient)."""
    if user.role == "patient":
        return [{"id": user.id, "name": user.name, "scopes": ALL_SCOPES}]
    rows = (await session.execute(select(Consent, User).join(User, User.id == Consent.patient_id)
                                  .where(Consent.grantee_id == user.id, Consent.revoked_at.is_(None)))).all()
    return [{"id": u.id, "name": u.name, "scopes": c.scopes} for c, u in rows]


# ------------------------------------------------------------------------------------ medications
class MedIn(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    dose_text: str | None = Field(default=None, max_length=100)
    timing: list[str] = Field(default_factory=lambda: ["morning"])
    course_days: int | None = Field(default=None, ge=1, le=365)
    start_date: date | None = None
    confirmed: bool = False  # the person must confirm the extracted/typed medicine
    acknowledge_alerts: bool = False


def _med_out(m: Medication) -> dict[str, object]:
    return {"id": m.id, "name": m.raw_name, "generic": m.generic_name, "dose": m.dose_text, "timing": m.timing,
            "start_date": m.start_date.isoformat(), "course_days": m.course_days, "is_antibiotic": m.is_antibiotic, "active": m.active}


async def _active_meds(session: Session, pid: int) -> list[Medication]:
    return list((await session.scalars(select(Medication).where(Medication.patient_id == pid, Medication.active.is_(True)).order_by(Medication.id))).all())


def _resolutions(meds: list[Medication]) -> list[Resolution]:
    kb = get_kb()
    return [kb.resolve(m.raw_name) for m in meds]


async def _add_med(session: Session, pid: int, body: MedIn, prescriber: User | None) -> tuple[Medication, list[Alert]]:
    if not body.confirmed:
        raise HTTPException(422, "Please confirm the medicine name before saving (confirmed=true).")
    if not set(body.timing) <= set(SLOTS) or not body.timing:
        raise HTTPException(422, f"timing must be a non-empty subset of {SLOTS}")
    kb = get_kb()
    res = kb.resolve(body.name)
    existing = await _active_meds(session, pid)
    allergies, _ = await profile_lists(session, pid)
    alerts = kb.analyze(_resolutions(existing) + [res], allergies)
    new_alerts = [a for a in alerts if res.generic_name and res.generic_name in a.involved or a.kind == "allergy"]
    if any(a.severity == "major" for a in new_alerts) and not body.acknowledge_alerts:
        raise HTTPException(409, {"message": "Major medicine-safety alerts. A clinician or pharmacist should review; resubmit with acknowledge_alerts=true if intended.",
                                  "alerts": [a.to_dict() for a in new_alerts]})
    med = Medication(patient_id=pid, prescriber_id=prescriber.id if prescriber else None, raw_name=body.name, product_key=res.product_key,
                     generic_name=res.generic_name, dose_text=body.dose_text, timing=body.timing, start_date=body.start_date or date.today(),
                     course_days=body.course_days, is_antibiotic=kb.is_antibiotic(res.ingredients), confirmed=True)
    session.add(med)
    if any(a.severity == "major" for a in new_alerts):
        session.add(Task(patient_id=pid, kind="medication_alert", title=f"Follow up: medicine alert for {body.name}",
                         detail="; ".join(f"{a.title} ({a.severity})" for a in new_alerts)[:1000]))
    await session.commit()
    return med, new_alerts


@router.post("/patients/{pid}/medications", status_code=201)
async def add_medication(pid: int, body: MedIn, user: CurrentUser, session: Session) -> dict[str, object]:
    await authorize(session, user, pid, "medications", "medication_add")
    if user.role not in ("patient", "doctor", "health_worker"):
        raise HTTPException(403, "Role cannot add medicines")
    med, alerts = await _add_med(session, pid, body, user if user.role != "patient" else None)
    return {"medication": _med_out(med), "alerts": [a.to_dict() for a in alerts]}


@router.post("/patients/{pid}/prescriptions", status_code=201)
async def prescribe(pid: int, body: MedIn, user: Doctor, session: Session) -> dict[str, object]:
    """A doctor records a prescription they decided on. MedGuard only shows alerts; the doctor decides."""
    await authorize(session, user, pid, "medications", "prescription_add")
    med, alerts = await _add_med(session, pid, body, user)
    return {"medication": _med_out(med), "alerts": [a.to_dict() for a in alerts], "note": ESCALATE["en"]}


@router.get("/patients/{pid}/medications")
async def list_meds(pid: int, user: CurrentUser, session: Session) -> list[dict[str, object]]:
    await authorize(session, user, pid, "medications", "medication_list")
    return [_med_out(m) for m in await _active_meds(session, pid)]


@router.get("/patients/{pid}/medguard/report")
async def medguard_report(pid: int, user: CurrentUser, session: Session) -> dict[str, object]:
    await authorize(session, user, pid, "medications", "medguard_report")
    meds = await _active_meds(session, pid)
    allergies, _ = await profile_lists(session, pid)
    alerts = get_kb().analyze(_resolutions(meds), allergies)
    return {"alerts": [a.to_dict() for a in alerts], "kb": get_kb().meta, "escalation": ESCALATE["en"]}


# ------------------------------------------------------------------------------------ measurements / doses
class MeasIn(BaseModel):
    kind: str = Field(pattern="^(bp|glucose|weight)$")
    v1: float = Field(gt=0, lt=1000)
    v2: float | None = Field(default=None, gt=0, lt=500)
    measured_at: datetime | None = None
    source: str = "manual"


@router.post("/patients/{pid}/measurements", status_code=201)
async def add_measurement(pid: int, body: MeasIn, user: CurrentUser, session: Session) -> dict[str, object]:
    await authorize(session, user, pid, "measurements", "measurement_add")
    if body.kind == "bp" and (body.v2 is None or body.v2 >= body.v1):
        raise HTTPException(422, "Blood pressure needs systolic (v1) greater than diastolic (v2)")
    m = Measurement(patient_id=pid, kind=body.kind, v1=body.v1, v2=body.v2, measured_at=body.measured_at or utcnow(), source=body.source)
    session.add(m)
    await session.commit()
    return {"id": m.id}


@router.get("/patients/{pid}/measurements")
async def list_measurements(pid: int, user: CurrentUser, session: Session, kind: str | None = None, limit: int = 50, offset: int = 0) -> list[dict[str, object]]:
    await authorize(session, user, pid, "measurements", "measurement_list")
    q = select(Measurement).where(Measurement.patient_id == pid)
    if kind:
        q = q.where(Measurement.kind == kind)
    rows = (await session.scalars(q.order_by(Measurement.measured_at.desc()).limit(min(limit, 200)).offset(offset))).all()
    return [{"id": r.id, "kind": r.kind, "v1": r.v1, "v2": r.v2, "at": r.measured_at.isoformat(), "source": r.source} for r in rows]


class DoseIn(BaseModel):
    medication_id: int
    slot: str
    day: date | None = None


@router.post("/patients/{pid}/doses", status_code=201)
async def log_dose(pid: int, body: DoseIn, user: CurrentUser, session: Session) -> dict[str, bool]:
    await authorize(session, user, pid, "adherence", "dose_log")
    med = await session.get(Medication, body.medication_id)
    if med is None or med.patient_id != pid or body.slot not in med.timing:
        raise HTTPException(404, "Medication/slot not found")
    day = body.day or date.today()
    exists = await session.scalar(select(DoseLog.id).where(DoseLog.medication_id == med.id, DoseLog.day == day, DoseLog.slot == body.slot))
    if not exists:
        session.add(DoseLog(patient_id=pid, medication_id=med.id, day=day, slot=body.slot))
        await session.commit()
    return {"logged": True}


async def _careloop_state(session: Session, pid: int, now: datetime) -> dict[str, object]:
    since = now - timedelta(days=60)
    rows = (await session.scalars(select(Measurement).where(Measurement.patient_id == pid, Measurement.measured_at >= since).order_by(Measurement.measured_at))).all()
    by = {k: [cl.Reading(r.measured_at, r.v1, r.v2) for r in rows if r.kind == k] for k in ("bp", "glucose", "weight")}
    meds = await _active_meds(session, pid)
    sched = [cl.MedSchedule(m.id, m.raw_name, m.timing, m.start_date, m.start_date + timedelta(days=m.course_days - 1) if m.course_days else None) for m in meds]
    doses = (await session.scalars(select(DoseLog).where(DoseLog.patient_id == pid, DoseLog.day >= now.date() - timedelta(days=14)))).all()
    adh, adh_flags = cl.adherence(sched, {(d.medication_id, d.day, d.slot) for d in doses}, now)
    flags = cl.evaluate_bp(by["bp"], now) + cl.evaluate_glucose(by["glucose"], now) + adh_flags
    return {"by": by, "meds": meds, "adherence": adh, "flags": flags, "doses": doses}


@router.get("/patients/{pid}/careloop/insights")
async def insights(pid: int, user: CurrentUser, session: Session) -> dict[str, object]:
    await authorize(session, user, pid, "measurements", "careloop_insights")
    now = utcnow()
    st = await _careloop_state(session, pid, now)
    by = st["by"]  # type: ignore[assignment]
    base = cl.baseline(by["bp"], now)  # type: ignore[index]
    return {"flags": [f.to_dict() for f in st["flags"]], "adherence": st["adherence"], "bp_baseline": base,  # type: ignore[attr-defined]
            "threshold_note": cl.THRESHOLD_NOTE, "explainable": True}


@router.get("/patients/{pid}/today")
async def today(pid: int, user: CurrentUser, session: Session) -> dict[str, object]:
    await authorize(session, user, pid, "adherence", "today_view")
    d = date.today()
    meds = await _active_meds(session, pid)
    taken = {(x.medication_id, x.slot) for x in (await session.scalars(select(DoseLog).where(DoseLog.patient_id == pid, DoseLog.day == d))).all()}
    return {"date": d.isoformat(), "doses": [{"medication_id": m.id, "name": m.raw_name, "dose": m.dose_text, "slot": s, "taken": (m.id, s) in taken}
                                             for m in meds for s in sorted(m.timing, key=SLOTS.index)]}


# ------------------------------------------------------------------------------------ elder voice logging
class VoiceIn(BaseModel):
    text: str = Field(max_length=300)


_SLOT_WORDS = {"morning": ("morning", "सुबह", "காலை"), "afternoon": ("afternoon", "दोपहर", "மதியம்"), "evening": ("evening", "शाम", "மாலை"), "night": ("night", "रात", "இரவு")}
_TAKEN_WORDS = ("took", "taken", "had my", "ले ली", "लिया", "ली", "எடுத்தேன்", "சாப்பிட்டேன்")


@router.post("/patients/{pid}/voice-log")
async def voice_log(pid: int, body: VoiceIn, user: CurrentUser, session: Session) -> dict[str, object]:
    """'I took my morning medicine' -> marks that slot's doses taken. Needs a clear 'taken' + slot; otherwise asks."""
    await authorize(session, user, pid, "adherence", "voice_log")
    t = body.text.lower()
    slot = next((s for s, ws in _SLOT_WORDS.items() if any(w in t for w in ws)), None)
    if not slot or not any(w in t for w in _TAKEN_WORDS):
        return {"logged": 0, "reply": "I did not catch that. Please say, for example: I took my morning medicine."}
    n = 0
    for m in await _active_meds(session, pid):
        if slot in m.timing and not await session.scalar(select(DoseLog.id).where(DoseLog.medication_id == m.id, DoseLog.day == date.today(), DoseLog.slot == slot)):
            session.add(DoseLog(patient_id=pid, medication_id=m.id, day=date.today(), slot=slot, source="voice"))
            n += 1
    await session.commit()
    return {"logged": n, "slot": slot, "reply": f"Noted: {n} {slot} medicine(s) marked as taken." if n else "Those medicines were already marked as taken."}


# ------------------------------------------------------------------------------------ family dashboard
@router.get("/patients/{pid}/family-dashboard")
async def family_dashboard(pid: int, user: CurrentUser, session: Session) -> dict[str, object]:
    """Data-minimised shared status. Each field appears only if the patient consented to the matching scope."""
    base = await session.get(User, pid)
    if base is None:
        raise HTTPException(404, "Not found")
    out: dict[str, object] = {"patient": base.name}
    now = utcnow()
    c = None if user.id == pid else await session.scalar(select(Consent).where(Consent.patient_id == pid, Consent.grantee_id == user.id, Consent.revoked_at.is_(None)))
    scopes = set(ALL_SCOPES) if user.id == pid else set(c.scopes if c else [])
    await authorize(session, user, pid, "adherence" if "adherence" in scopes else "measurements" if "measurements" in scopes else "appointments", "family_dashboard")
    if "adherence" in scopes:
        meds = await _active_meds(session, pid)
        exp = sum(len(m.timing) for m in meds)
        got = await session.scalar(select(func.count()).select_from(DoseLog).where(DoseLog.patient_id == pid, DoseLog.day == now.date()))
        out["medicine_taken_today"] = {"taken": got or 0, "scheduled": exp}
    if "measurements" in scopes:
        last = await session.scalar(select(func.max(Measurement.measured_at)).where(Measurement.patient_id == pid, Measurement.kind == "bp"))
        out["bp_recorded_today"] = bool(last and last.date() == now.date())
        out["last_bp_at"] = last.isoformat() if last else None
    if "appointments" in scopes:
        ap = await session.scalar(select(Appointment).where(Appointment.patient_id == pid, Appointment.when >= now).order_by(Appointment.when))
        out["next_appointment"] = {"when": ap.when.isoformat(), "with": ap.with_name} if ap else None
    return out


# ------------------------------------------------------------------------------------ tasks
@router.get("/tasks")
async def tasks(user: Staff, session: Session) -> list[dict[str, object]]:
    """Open tasks, only for patients who consented to this staff member."""
    ids = list((await session.scalars(select(Consent.patient_id).where(Consent.grantee_id == user.id, Consent.revoked_at.is_(None)))).all())
    rows = (await session.execute(select(Task, User).join(User, User.id == Task.patient_id).where(Task.patient_id.in_(ids), Task.status == "open").order_by(Task.id.desc()))).all()
    return [{"id": t.id, "patient_id": t.patient_id, "patient": u.name, "kind": t.kind, "title": t.title, "detail": t.detail} for t, u in rows]


@router.post("/tasks/{tid}/complete")
async def complete_task(tid: int, user: Staff, session: Session) -> dict[str, str]:
    t = await session.get(Task, tid)
    if t is None:
        raise HTTPException(404, "Not found")
    await authorize(session, user, t.patient_id, "medications", "task_complete")
    t.status = "done"
    await session.commit()
    return {"status": "done"}


# ------------------------------------------------------------------------------------ visit summary
async def _build_summary(session: Session, pid: int, now: datetime) -> dict[str, object]:
    patient = await session.get(User, pid)
    st = await _careloop_state(session, pid, now)
    by = st["by"]  # type: ignore[assignment]
    since = now - timedelta(days=30)
    meds = st["meds"]  # type: ignore[assignment]
    allergies, _ = await profile_lists(session, pid)
    alerts = get_kb().analyze(_resolutions(meds), allergies)  # type: ignore[arg-type]
    flags = st["flags"]  # type: ignore[assignment]
    content: dict[str, object] = {
        "patient_name": patient.name if patient else "", "generated_at": now.isoformat(), "status": "draft",
        "bp": cl.series_stats(by["bp"], since), "glucose": cl.series_stats(by["glucose"], since), "weight": cl.series_stats(by["weight"], since),  # type: ignore[index]
        "adherence": st["adherence"], "flags": [f.to_dict() for f in flags],  # type: ignore[attr-defined]
        "medication_alerts": [a.to_dict() for a in alerts],
        "medicines": [_med_out(m) for m in meds],  # type: ignore[attr-defined]
        "questions": cl.suggested_questions(flags, len(alerts), any(m.is_antibiotic for m in meds)),  # type: ignore[arg-type, attr-defined]
    }
    facts = sm.facts_text(content)  # type: ignore[arg-type]
    res = await guarded_generate("", "en", lambda: _narr(facts))
    content["narrative"] = res.text if not res.blocked else facts
    content["narrative"] = sm.safe_narrative(str(content["narrative"]))
    return content


async def _narr(facts: str) -> str:
    return str(await gateway.generate("visit_narrative", {"facts": facts}))


@router.post("/patients/{pid}/summary", status_code=201)
async def create_summary(pid: int, user: CurrentUser, session: Session) -> dict[str, object]:
    await authorize(session, user, pid, "summary", "summary_create")
    if user.role not in ("patient", "doctor", "health_worker"):
        raise HTTPException(403, "Role cannot create summaries")
    content = await _build_summary(session, pid, utcnow())
    row = VisitSummary(patient_id=pid, created_by=user.id, content_enc=json.dumps(content, default=str))
    session.add(row)
    await session.commit()
    return {"id": row.id, "status": row.status, "content": content}


async def _summary(session: Session, user: User, sid: int, action: str) -> tuple[VisitSummary, dict[str, object]]:
    row = await session.get(VisitSummary, sid)
    if row is None:
        raise HTTPException(404, "Not found")
    await authorize(session, user, row.patient_id, "summary", action)
    content = json.loads(row.content_enc)
    content["status"] = row.status
    return row, content


@router.get("/summaries/{sid}")
async def get_summary(sid: int, user: CurrentUser, session: Session) -> dict[str, object]:
    row, content = await _summary(session, user, sid, "summary_view")
    return {"id": row.id, "status": row.status, "content": content}


@router.get("/summaries/{sid}/pdf")
async def summary_pdf(sid: int, user: CurrentUser, session: Session) -> Response:
    _, content = await _summary(session, user, sid, "summary_pdf")
    return Response(sm.render_pdf(content), media_type="application/pdf", headers={"Content-Disposition": f'attachment; filename="summary-{sid}.pdf"'})


@router.post("/summaries/{sid}/approve")
async def approve(sid: int, user: Doctor, session: Session) -> dict[str, object]:
    """Human-in-the-loop: only a doctor can approve an AI-assisted draft."""
    row, _ = await _summary(session, user, sid, "summary_approve")
    row.status, row.approved_by, row.approved_at = "approved", user.id, utcnow()
    await session.commit()
    return {"id": row.id, "status": row.status}


# ------------------------------------------------------------------------------------ antibiotic safety
@router.get("/patients/{pid}/antibiotics")
async def antibiotic_courses(pid: int, user: CurrentUser, session: Session) -> dict[str, object]:
    """Tracks courses a clinician has already prescribed. Never chooses or changes an antibiotic."""
    await authorize(session, user, pid, "medications", "antibiotic_view")
    from app.antibiotic import EDUCATION, course_status
    meds = [m for m in await _active_meds(session, pid) if m.is_antibiotic]
    return {"courses": [course_status(m.raw_name, m.start_date, m.course_days, date.today()) for m in meds], "education": EDUCATION["en"]}


# ------------------------------------------------------------------------------------ screening
class ScreenIn(BaseModel):
    instrument: str = Field(pattern="^(phq9|gad7)$")
    answers: list[int]


@router.post("/patients/{pid}/screenings", status_code=201)
async def screening(pid: int, body: ScreenIn, user: CurrentUser, session: Session) -> dict[str, object]:
    await authorize(session, user, pid, "screening", "screening_submit")
    try:
        r = score_screening(body.instrument, body.answers)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    session.add(Screening(patient_id=pid, instrument=r.instrument, answers_enc=json.dumps(body.answers), score=r.score, band=r.band, escalated=r.escalate))
    if r.escalate:
        session.add(Task(patient_id=pid, kind="wellbeing_followup", title="Gentle check-in recommended", detail="Screening answers suggest a clinician conversation would help. Contact the patient kindly; see crisis resources."))
    await session.commit()
    return {"score": r.score, "band": r.band, "escalate": r.escalate, "message": r.message, "crisis_resources": r.crisis_resources, "is_diagnosis": False}


# ------------------------------------------------------------------------------------ FHIR / export / delete
def fhir_bundle(patient: User, profile: PatientProfile | None, meds: list[Medication], ms: list[Measurement]) -> dict[str, object]:
    pid = f"patient-{patient.id}"
    entries: list[dict[str, object]] = [{"resource": {"resourceType": "Patient", "id": pid, "name": [{"text": patient.name}],
                                                        **({"birthDate": str(profile.birth_year)} if profile and profile.birth_year else {})}}]
    for m in meds:
        entries.append({"resource": {"resourceType": "MedicationStatement", "id": f"med-{m.id}", "status": "active" if m.active else "stopped",
                                     "subject": {"reference": f"Patient/{pid}"}, "medicationCodeableConcept": {"text": m.generic_name or m.raw_name},
                                     "dosage": [{"text": m.dose_text or ""}]}})
    for x in ms:
        base: dict[str, object] = {"resourceType": "Observation", "id": f"obs-{x.id}", "status": "final", "subject": {"reference": f"Patient/{pid}"},
                "effectiveDateTime": x.measured_at.isoformat() + "Z"}
        if x.kind == "bp":
            base.update({"code": {"coding": [{"system": "http://loinc.org", "code": "85354-9", "display": "Blood pressure panel"}]},
                         "component": [{"code": {"coding": [{"system": "http://loinc.org", "code": "8480-6", "display": "Systolic blood pressure"}]}, "valueQuantity": {"value": x.v1, "unit": "mmHg", "system": "http://unitsofmeasure.org", "code": "mm[Hg]"}},
                                       {"code": {"coding": [{"system": "http://loinc.org", "code": "8462-4", "display": "Diastolic blood pressure"}]}, "valueQuantity": {"value": x.v2, "unit": "mmHg", "system": "http://unitsofmeasure.org", "code": "mm[Hg]"}}]})
        elif x.kind == "glucose":
            base.update({"code": {"coding": [{"system": "http://loinc.org", "code": "2339-0", "display": "Glucose [Mass/volume] in Blood"}]}, "valueQuantity": {"value": x.v1, "unit": "mg/dL", "system": "http://unitsofmeasure.org", "code": "mg/dL"}})
        else:
            base.update({"code": {"coding": [{"system": "http://loinc.org", "code": "29463-7", "display": "Body weight"}]}, "valueQuantity": {"value": x.v1, "unit": "kg", "system": "http://unitsofmeasure.org", "code": "kg"}})
        entries.append({"resource": base})
    return {"resourceType": "Bundle", "type": "collection", "entry": entries}


@router.get("/patients/{pid}/fhir")
async def fhir(pid: int, user: CurrentUser, session: Session) -> dict[str, object]:
    await authorize(session, user, pid, "medications", "fhir_export")
    await authorize(session, user, pid, "measurements", "fhir_export")
    p = await session.get(User, pid)
    if p is None:
        raise HTTPException(404, "Not found")
    ms = (await session.scalars(select(Measurement).where(Measurement.patient_id == pid).order_by(Measurement.measured_at))).all()
    return fhir_bundle(p, await session.get(PatientProfile, pid), await _active_meds(session, pid), list(ms))


@router.delete("/me", status_code=204)
async def delete_me(user: CurrentUser, session: Session) -> Response:
    """DPDP-style erasure: removes the user's health data and credentials; audit rows are kept without PHI."""
    for model in (DoseLog, Measurement, Medication, Appointment, Task, Screening, VisitSummary):
        await session.execute(delete(model).where(model.patient_id == user.id))  # type: ignore[attr-defined]
    await session.execute(delete(Consent).where((Consent.patient_id == user.id) | (Consent.grantee_id == user.id)))
    await session.execute(delete(RefreshToken).where(RefreshToken.user_id == user.id))
    await session.execute(delete(PatientProfile).where(PatientProfile.user_id == user.id))
    session.add(AuditLog(actor_id=user.id, actor_role=user.role, action="account_erased"))
    u = await session.get(User, user.id)
    if u:
        u.is_active, u.email, u.name = False, f"erased-{user.id}@erased.invalid", "Erased user"
    await session.commit()
    return Response(status_code=204)
