"""Guardrail layer: input classifier, output validator, refusal templates, disclaimers.

Principle: AI assists, humans decide. These checks run in code on every AI call and on all
generated safety text; they are not just UI copy.
"""
import re
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field

from prometheus_client import Counter

GUARDRAIL_EVENTS = Counter("guardrail_events_total", "Guardrail decisions", ["stage", "outcome"])

LANGS = ("en", "ta", "hi")

# ----------------------------------------------------------------------------- input classifier
_SELF_HARM = [
    r"\bsuicid", r"\bkill myself\b", r"\bend my life\b", r"\bwant to die\b", r"\bhurt myself\b",
    r"\bself[- ]?harm\b", r"\bno reason to live\b", r"\bbetter off dead\b",
    "आत्महत्या", "मरना चाहता", "मरना चाहती", "खुद को नुकसान",
    "தற்கொலை", "சாக வேண்டும்", "உயிரை மாய்",
]
_EMERGENCY = [
    r"\bchest pain\b", r"\bcan'?t breathe\b", r"\bcannot breathe\b", r"\bdifficulty breathing\b",
    r"\bunconscious\b", r"\bstroke\b", r"\bface (is )?droop", r"\bslurred speech\b", r"\bseizure\b",
    r"\boverdos", r"\bsevere bleeding\b", r"\bvomiting blood\b", r"\bfainted\b", r"\bpassed out\b",
    "सीने में दर्द", "सांस नहीं", "बेहोश",
    "நெஞ்சு வலி", "மூச்சு விட முடிய", "மயக்கம்",
]
_PRESCRIPTION = [
    r"\bwhich (antibiotic|medicine|medication|tablet|drug)\b", r"\bwhat (antibiotic|medicine|medication|tablet|drug) (should|can|do)\b",
    r"\bprescribe\b", r"\brecommend (me )?(a |an |some )?(antibiotic|medicine|medication|tablet|drug)\b",
    r"\bwhat (dose|dosage)\b", r"\bhow (many|much) (mg|tablets?|pills?|units?) (should|can|do) i\b",
    r"\b(should|can|could|may) i (stop|skip|increase|decrease|double|halve|reduce|change|switch|quit)\b",
    r"\b(stop|quit) taking (my|the)\b", r"\bgive me an antibiotic\b",
]
_DIAGNOSIS = [r"\bdo i have\b", r"\bdiagnose\b", r"\bwhat (disease|illness|condition) do i have\b", r"\bam i (depressed|diabetic)\b"]


def _any(patterns: list[str], text: str) -> bool:
    return any(re.search(p, text, flags=re.IGNORECASE) for p in patterns)


def classify_input(text: str) -> str:
    """Return one of: self_harm, emergency, prescription_request, diagnosis_request, ok."""
    if _any(_SELF_HARM, text):
        return "self_harm"
    if _any(_EMERGENCY, text):
        return "emergency"
    if _any(_PRESCRIPTION, text):
        return "prescription_request"
    if _any(_DIAGNOSIS, text):
        return "diagnosis_request"
    return "ok"


# ----------------------------------------------------------------------------- output validator
_NEG = r"(?<!not )(?<!never )(?<!n't )(?<!no need to )"
_OUTPUT_RULES: list[tuple[str, str]] = [
    ("dosing_instruction", r"\b(take|use|consume|inject|swallow)\s+\d+(\.\d+)?\s*(mg|mcg|g|ml|units?|tablets?|pills?|capsules?)\b"),
    ("stop_instruction", _NEG + r"\b(stop|discontinue|quit|skip|halve|double)\s+(taking|using|your|the|this|that|it)\b"),
    ("dose_change", _NEG + r"\b(increase|decrease|reduce|change|switch|adjust|lower|raise)\s+(your |the |this |that )?(dose|dosage|medicine|medication|tablet|pills?)\b"),
    ("drug_selection", r"\byou should (take|try|use|start|begin|switch to)\b"),
    ("drug_selection", r"\b(i|we) (recommend|suggest|advise|prescribe)\b"),
    ("drug_selection", _NEG + r"\bstart (taking|on|with)\b"),
    ("diagnosis", r"\byou (have|likely have|probably have|may have|might have|are suffering from|suffer from|are diagnosed with)\b.{0,40}\b(diabetes|hypertension|depress\w*|anxiety|cancer|infection|disorder|disease|pneumonia|asthma|tuberculosis|kidney failure|bipolar)"),
    ("diagnosis", r"\byou are (clinically )?(depressed|bipolar|suicidal|diabetic|hypertensive)\b"),
    ("diagnosis", r"\b(my|the) diagnosis (is|would be)\b|\bi diagnose\b"),
    ("emergency_handling", r"\bno need (to|for) (see|call|visit) (a |your )?(doctor|hospital|emergency)\b"),
]
_COMPILED = [(name, re.compile(p, re.IGNORECASE | re.DOTALL)) for name, p in _OUTPUT_RULES]


def validate_output(text: str) -> list[str]:
    """Return the list of violated rule names (empty list == safe)."""
    return sorted({name for name, rx in _COMPILED if rx.search(text)})


# ----------------------------------------------------------------------------- templates
DISCLAIMER = {
    "en": "This is general information to help you prepare for a conversation with your care team. It is not medical advice. Do not start, stop or change any medicine without asking your doctor or pharmacist.",
    "ta": "இது தகவலுக்காக மட்டுமே; மருத்துவ ஆலோசனை அல்ல. எந்த மருந்தையும் தொடங்குவதற்கு, நிறுத்துவதற்கு அல்லது மாற்றுவதற்கு முன் உங்கள் மருத்துவர் அல்லது மருந்தாளரிடம் கேளுங்கள்.",
    "hi": "यह केवल सामान्य जानकारी है, चिकित्सकीय सलाह नहीं। कोई भी दवा शुरू करने, बंद करने या बदलने से पहले अपने डॉक्टर या फ़ार्मासिस्ट से पूछें।",
}
ESCALATE = {
    "en": "Please confirm this with your doctor or pharmacist before acting on it. Do not stop or change any medicine on your own.",
    "ta": "இதன்படி செயல்படுவதற்கு முன் உங்கள் மருத்துவர் அல்லது மருந்தாளரிடம் உறுதிசெய்யுங்கள். நீங்களாக எந்த மருந்தையும் நிறுத்தவோ மாற்றவோ வேண்டாம்.",
    "hi": "इस पर अमल करने से पहले अपने डॉक्टर या फ़ार्मासिस्ट से पुष्टि करें। अपने आप कोई दवा बंद या न बदलें।",
}
REFUSALS = {
    "emergency": {
        "en": "This could be an emergency. Please call 112 now or go to the nearest hospital. If someone is with you, ask them to help. I cannot handle emergencies.",
        "ta": "இது அவசர நிலையாக இருக்கலாம். உடனடியாக 112 ஐ அழைக்கவும் அல்லது அருகிலுள்ள மருத்துவமனைக்குச் செல்லவும்.",
        "hi": "यह आपातकाल हो सकता है। कृपया तुरंत 112 पर कॉल करें या नज़दीकी अस्पताल जाएँ।",
    },
    "self_harm": {
        "en": "I'm really sorry you're going through this. You are not alone. Please talk to someone right now: call Tele-MANAS at 14416 (free, 24x7, many Indian languages), or call 112 if you are in immediate danger. If you can, tell a person you trust where you are.",
        "ta": "நீங்கள் தனியாக இல்லை. இப்போதே Tele-MANAS 14416 ஐ அழைக்கவும் (இலவசம், 24x7). உடனடி ஆபத்தில் இருந்தால் 112 ஐ அழைக்கவும். நம்பிக்கையான ஒருவரிடம் சொல்லுங்கள்.",
        "hi": "आप अकेले नहीं हैं। अभी Tele-MANAS 14416 पर कॉल करें (निःशुल्क, 24x7)। तुरंत खतरे में हों तो 112 पर कॉल करें। किसी भरोसेमंद व्यक्ति को बताएँ।",
    },
    "prescription_request": {
        "en": "I can't choose, recommend, start, stop or change a medicine or dose. That decision belongs to your doctor or pharmacist. I can help you write down your questions and your current medicines so the visit is more useful.",
        "ta": "மருந்து அல்லது அளவைத் தேர்வு செய்யவோ மாற்றவோ என்னால் முடியாது. அது உங்கள் மருத்துவர் அல்லது மருந்தாளரின் முடிவு. உங்கள் கேள்விகளை எழுதிக்கொள்ள உதவ முடியும்.",
        "hi": "मैं दवा या खुराक चुन, सुझा, शुरू, बंद या बदल नहीं सकता। यह फ़ैसला आपके डॉक्टर या फ़ार्मासिस्ट का है। मैं आपके सवाल लिखने में मदद कर सकता हूँ।",
    },
    "diagnosis_request": {
        "en": "I can't diagnose conditions. A doctor needs to examine you and review tests. I can help you note your symptoms and questions to bring to your appointment.",
        "ta": "என்னால் நோயைக் கண்டறிய முடியாது. மருத்துவர் பரிசோதிக்க வேண்டும். உங்கள் அறிகுறிகளையும் கேள்விகளையும் குறித்துக்கொள்ள உதவ முடியும்.",
        "hi": "मैं बीमारी का निदान नहीं कर सकता। डॉक्टर को जाँच करनी होगी। मैं आपके लक्षण और सवाल लिखने में मदद कर सकता हूँ।",
    },
    "unsafe_output": {
        "en": "I can't give a safe answer to that here. Please ask your doctor or pharmacist.",
        "ta": "இதற்கு பாதுகாப்பான பதிலை என்னால் தர முடியாது. உங்கள் மருத்துவர் அல்லது மருந்தாளரிடம் கேளுங்கள்.",
        "hi": "मैं इसका सुरक्षित उत्तर यहाँ नहीं दे सकता। कृपया अपने डॉक्टर या फ़ार्मासिस्ट से पूछें।",
    },
}
CRISIS_RESOURCES = [
    {"name": "Tele-MANAS (Govt. of India, 24x7 mental health)", "phone": "14416", "alt": "1-800-891-4416"},
    {"name": "National emergency number", "phone": "112"},
]


def lang_or_en(lang: str) -> str:
    return lang if lang in LANGS else "en"


def ensure_safe(text: str, lang: str = "en") -> str:
    """Runtime guard for any generated text. Returns the text, or a safe fallback if it violates a rule."""
    violations = validate_output(text)
    if violations:
        GUARDRAIL_EVENTS.labels("output", "blocked").inc()
        return REFUSALS["unsafe_output"][lang_or_en(lang)]
    return text


@dataclass
class GuardedResult:
    text: str
    blocked: bool
    category: str = "ok"
    violations: list[str] = field(default_factory=list)
    show_crisis_resources: bool = False
    disclaimer: str = ""


async def guarded_generate(user_text: str, lang: str, generate: Callable[[], Awaitable[str]]) -> GuardedResult:
    """Wrap EVERY AI call: classify input -> (refuse | generate) -> validate output -> disclaimer."""
    lang = lang_or_en(lang)
    category = classify_input(user_text)
    if category in ("self_harm", "emergency", "prescription_request", "diagnosis_request"):
        GUARDRAIL_EVENTS.labels("input", category).inc()
        return GuardedResult(
            text=REFUSALS[category][lang], blocked=True, category=category,
            show_crisis_resources=category in ("self_harm", "emergency"), disclaimer=DISCLAIMER[lang],
        )
    out = await generate()
    violations = validate_output(out)
    if violations:
        GUARDRAIL_EVENTS.labels("output", "blocked").inc()
        return GuardedResult(text=REFUSALS["unsafe_output"][lang], blocked=True, category="unsafe_output",
                             violations=violations, disclaimer=DISCLAIMER[lang])
    GUARDRAIL_EVENTS.labels("output", "passed").inc()
    return GuardedResult(text=out, blocked=False, disclaimer=DISCLAIMER[lang])
