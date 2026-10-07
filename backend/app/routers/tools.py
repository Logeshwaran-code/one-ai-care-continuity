"""Patient-independent tools: MedGuard resolve/OCR, health literacy, assistant Q&A, antibiotic education, cost help, wellbeing items."""
import re

from fastapi import APIRouter, HTTPException, UploadFile
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


class NamesIn(BaseModel):
    names: list[str] = Field(min_length=1, max_length=30)


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
