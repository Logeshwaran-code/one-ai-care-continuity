"""Patient-independent tools: MedGuard resolve/OCR, health literacy, assistant Q&A, antibiotic education, cost help, wellbeing items."""
import asyncio
import logging
import re

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from pydantic import BaseModel, Field

from app import cost
from app.antibiotic import EDUCATION
from app.config import settings
from app.deps import CurrentUser
from app.guardrails import CRISIS_RESOURCES, ensure_safe, guarded_generate, lang_or_en
from app.llm import gateway
from app.medguard import ocr
from app.medguard.engine import get_kb
from app.wellbeing import INSTRUMENTS, OPTIONS

router = APIRouter(tags=["tools"])
log = logging.getLogger("tools")


def _apply_plain_glossary(text: str) -> str:
    replacements = {
        "hypertension": "high blood pressure",
        "hyperglycemia": "high blood sugar",
        "hypoglycemia": "low blood sugar",
        "hba1c": "HbA1c (average blood sugar over about 3 months)",
    }
    for term, plain in replacements.items():
        text = re.sub(rf"\b{re.escape(term)}\b", plain, text, flags=re.IGNORECASE)
    return text


def _document_review_fallback(text: str) -> str:
    """Provide a deterministic document map when an optional LLM is unavailable."""
    plain = _apply_plain_glossary(text)
    sentences = [s.strip() for s in re.split(r"[\n.]+", plain) if s.strip()]
    findings = "\n".join(f"- {sentence}" for sentence in sentences[:8])
    return (
        "Document overview\n"
        "- The following points were read from the uploaded document.\n\n"
        "Prescription and medicine details\n"
        f"{findings or '- No prescription details were readable.'}\n\n"
        "Reported body findings and measurements\n"
        f"{findings or '- No body findings or measurements were readable.'}\n\n"
        "Questions for your care team\n"
        "- Which findings are important for me?\n"
        "- Can you confirm every medicine name, strength, schedule, route, and duration?\n"
        "- Which results need follow-up, and when?\n"
        "- Please explain any value or instruction that is unclear."
    )


class NamesIn(BaseModel):
    names: list[str] = Field(min_length=1, max_length=30)


def _document_facts(text: str) -> list[str]:
    """Keep clinically relevant source lines available for exact user verification."""
    lines = [re.sub(r"\s+", " ", line).strip() for line in text.splitlines() if line.strip()]
    terms = ("prescription", "medicine", "tablet", "capsule", "dose", "mg", "ml", "daily",
             "blood", "glucose", "hba1c", "pressure", "assessment", "finding", "result", "follow-up")
    facts = [line for line in lines if any(term in line.casefold() for term in terms)]
    return facts[:12]


@router.post("/medguard/resolve")
async def resolve(body: NamesIn, user: CurrentUser) -> dict[str, object]:
    kb = get_kb()
    rs = [kb.resolve(n) for n in body.names]
    return {"results": [r.__dict__ for r in rs], "alerts": [a.to_dict() for a in kb.analyze(rs)], "note": "Confirm each medicine yourself before saving."}


class OcrTextIn(BaseModel):
    text: str = Field(max_length=5000)


@router.post("/medguard/ocr-text")
async def ocr_text(body: OcrTextIn, user: CurrentUser) -> dict[str, object]:
    """Same pipeline as image OCR but for already-extracted/pasted text. Candidates still need user confirmation."""
    return {"candidates": [c.__dict__ for c in ocr.extract_candidates(body.text)], "requires_confirmation": True}


@router.post("/medguard/ocr")
async def ocr_image(file: UploadFile, user: CurrentUser) -> dict[str, object]:
    data = await file.read()
    if len(data) > 8_000_000:
        raise HTTPException(413, "Image too large")
    try:
        r = ocr.get_provider().read(data)
    except RuntimeError as exc:
        raise HTTPException(501, str(exc)) from exc
    return {"ocr_confidence": r.confidence, "raw_text": r.text, "candidates": [c.__dict__ for c in ocr.extract_candidates(r.text, r.confidence)], "requires_confirmation": True}


@router.post("/assistant/document")
async def explain_document(user: CurrentUser, file: UploadFile = File(...), lang: str = Form("en")) -> dict[str, object]:
    """Read a medical document transiently and return a safe plain-language explanation."""
    data = await file.read()
    if len(data) > 8_000_000:
        raise HTTPException(413, "Document is too large. Please upload a file under 8 MB.")
    name = (file.filename or "").lower()
    content_type = (file.content_type or "").lower()
    text = ""
    if content_type == "application/pdf" or name.endswith(".pdf"):
        try:
            from pypdf import PdfReader
            from pypdf.errors import PdfReadError
            import io
            text = "\n".join(page.extract_text() or "" for page in PdfReader(io.BytesIO(data)).pages)
        except (PdfReadError, OSError, ValueError) as exc:
            raise HTTPException(422, "This PDF could not be read. Try a clearer PDF or paste its text into CareSync AI.") from exc
    elif content_type.startswith("text/") or name.endswith((".txt", ".md", ".csv", ".json")):
        text = data.decode("utf-8", errors="replace")
    elif content_type.startswith("image/") or name.endswith((".png", ".jpg", ".jpeg", ".webp")):
        try:
            text = ocr.get_provider().read(data).text
        except RuntimeError as exc:
            raise HTTPException(501, str(exc)) from exc
    else:
        raise HTTPException(415, "Upload a PDF, text file, or medical image.")
    text = text.strip()
    if not text:
        raise HTTPException(422, "No readable text was found in this image. Try a sharper, well-lit image with the full report visible.")
    if len(text) > 6000:
        text = text[:6000]
    target = lang_or_en(lang)

    async def gen() -> str:
        out = str(await gateway.generate("document_review", {"text": text, "target": target}))
        if target != "en":
            out = str(await gateway.generate("translate", {"text": out, "target": target}))
        return ensure_safe(out, target)

    # A document may contain the words "prescription" or a diagnosis term as data.
    # Classify the user's action, not the document's quoted clinical content.
    async def bounded_gen() -> str:
        return await asyncio.wait_for(gen(), timeout=25)

    try:
        result = await guarded_generate("Explain this uploaded document without changing treatment.", target, bounded_gen)
    except (RuntimeError, asyncio.TimeoutError):
        log.warning("document_ai_unavailable_using_local_review")
        async def local_review() -> str:
            return _document_review_fallback(text)

        result = await guarded_generate(
            "Explain this uploaded document without changing treatment.",
            target,
            local_review,
        )
    if result.blocked and result.category == "unsafe_output":
        log.warning("document_ai_output_blocked_using_local_review")

        async def safe_local_review() -> str:
            return _document_review_fallback(text)

        result = await guarded_generate(
            "Explain this uploaded document without changing treatment.",
            target,
            safe_local_review,
        )
    return {"text": result.text, "document_facts": _document_facts(text), "blocked": result.blocked, "category": result.category, "language": target,
            "filename": file.filename or "document", "disclaimer": result.disclaimer,
            "crisis_resources": CRISIS_RESOURCES if result.show_crisis_resources else [],
            "stored": False}


class SimplifyIn(BaseModel):
    text: str = Field(min_length=1, max_length=6000)
    level: str = Field(default="simple", pattern="^(standard|simple|very_simple)$")
    target: str = "en"


@router.post("/literacy/simplify")
async def simplify(body: SimplifyIn, user: CurrentUser) -> dict[str, object]:
    lang = lang_or_en(body.target)

    async def gen() -> str:
        out = str(await gateway.generate("simplify", {"text": body.text, "level": body.level, "target": lang}))
        if lang != "en":
            out = str(await gateway.generate("translate", {"text": out, "target": lang}))
        return _apply_plain_glossary(out)

    r = await guarded_generate(body.text, lang, gen)
    return {"text": r.text, "blocked": r.blocked, "category": r.category, "disclaimer": r.disclaimer, "crisis_resources": CRISIS_RESOURCES if r.show_crisis_resources else [],
            "translation_note": "Offline demo mode only translates a few fixed phrases; connect an LLM provider for full translation." if lang != "en" else None}


class AskIn(BaseModel):
    text: str = Field(min_length=1, max_length=2000)
    lang: str = "en"


def _simple_answer(text: str, lang: str) -> str:
    """Return a short, safe health-literacy answer for common everyday questions."""
    lowered = text.casefold()
    answers = (
        (("blood pressure", "pressure"), "Blood pressure is the force of blood moving through your blood vessels. A reading has a top number and a bottom number. Sit quietly, keep your arm supported, and record the reading so your care team can review it."),
        (("blood sugar", "glucose", "sugar level"), "Blood sugar is the amount of glucose in your blood. Your reading can change with food, activity, stress, and medicines. Record it with the time and context, then discuss patterns with your care team."),
        (("medicine reminder", "remember my medicine", "missed a dose"), "Use the schedule in this app and mark a dose only after you take it. If you miss a dose, check the instructions from your doctor or pharmacist rather than taking extra medicine."),
        (("side effect", "adverse effect"), "A side effect is an unwanted change that can happen after using a medicine. Write down what happened, when it started, and the medicine involved, then contact your pharmacist or doctor."),
        (("appointment", "prepare for doctor"), "Bring your medicine list, recent readings, symptoms or questions, allergies, and any changes since your last visit. This helps your care team make a safer decision."),
        (("healthy food", "healthy eating", "diet"), "A simple starting point is regular meals with vegetables, pulses or other protein, whole grains, and water. Your doctor or dietitian can adapt this to your conditions and medicines."),
    )
    for keywords, answer in answers:
        if any(keyword in lowered for keyword in keywords):
            return answer
    return "I can explain health words, readings, medicine schedules, and how to prepare for a care-team visit. Please ask one specific question, or share the term you want explained."


@router.post("/assistant/ask")
async def ask(body: AskIn, user: CurrentUser) -> dict[str, object]:
    """Answer safe health-literacy questions simply; guardrails handle clinical-risk requests."""
    async def gen() -> str:
        if settings.llm_provider == "openai_compat":
            answer = str(await gateway.generate("question_answer", {"question": body.text, "language": lang_or_en(body.lang)}))
        else:
            answer = _simple_answer(body.text, body.lang)
        return ensure_safe(answer, body.lang)

    r = await guarded_generate(body.text, body.lang, gen)
    return {"text": r.text, "blocked": r.blocked, "category": r.category, "language": lang_or_en(body.lang),
            "model": settings.llm_model if settings.llm_provider == "openai_compat" else "offline",
            "disclaimer": r.disclaimer, "crisis_resources": CRISIS_RESOURCES if r.show_crisis_resources else []}


@router.get("/antibiotic/education")
async def edu(user: CurrentUser) -> dict[str, list[str]]:
    return EDUCATION


@router.get("/cost/compare")
async def cost_compare(name: str, user: CurrentUser) -> dict[str, object]:
    return cost.compare(name)


@router.get("/wellbeing/instruments/{name}")
async def instrument(name: str, user: CurrentUser) -> dict[str, object]:
    items = INSTRUMENTS.get(name)
    if items is None:
        raise HTTPException(404, "Unknown instrument")
    return {"name": name, "items": items, "options": OPTIONS, "values": [0, 1, 2, 3], "intro": "Over the last 2 weeks, how often have you been bothered by the following? This is a screening questionnaire, not a diagnosis.",
            "language_note": "Only English item wording is bundled; use officially validated translations before offering other languages."}
