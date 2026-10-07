"""PHQ-9 and GAD-7 scoring (standard published scoring; both instruments are in the public domain).
Output is a screening result, never a diagnosis. Validated Tamil/Hindi item wording must come from the
official translations; only English items are bundled here (see LIMITATIONS.md)."""
from dataclasses import dataclass

from app.guardrails import CRISIS_RESOURCES

OPTIONS = ["Not at all", "Several days", "More than half the days", "Nearly every day"]
PHQ9_ITEMS = [
    "Little interest or pleasure in doing things",
    "Feeling down, depressed, or hopeless",
    "Trouble falling or staying asleep, or sleeping too much",
    "Feeling tired or having little energy",
    "Poor appetite or overeating",
    "Feeling bad about yourself, or that you are a failure or have let yourself or your family down",
    "Trouble concentrating on things, such as reading or watching television",
    "Moving or speaking so slowly that other people could have noticed, or being so fidgety or restless that you have been moving around a lot more than usual",
    "Thoughts that you would be better off dead, or of hurting yourself in some way",
]
GAD7_ITEMS = [
    "Feeling nervous, anxious, or on edge",
    "Not being able to stop or control worrying",
    "Worrying too much about different things",
    "Trouble relaxing",
    "Being so restless that it is hard to sit still",
    "Becoming easily annoyed or irritable",
    "Feeling afraid, as if something awful might happen",
]
INSTRUMENTS = {"phq9": PHQ9_ITEMS, "gad7": GAD7_ITEMS}
_PHQ_BANDS = [(4, "minimal"), (9, "mild"), (14, "moderate"), (19, "moderately severe"), (27, "severe")]
_GAD_BANDS = [(4, "minimal"), (9, "mild"), (14, "moderate"), (21, "severe")]


@dataclass
class ScreeningResult:
    instrument: str
    score: int
    band: str
    escalate: bool
    message: str
    crisis_resources: list[dict[str, str]]


def score_screening(instrument: str, answers: list[int]) -> ScreeningResult:
    items = INSTRUMENTS.get(instrument)
    if items is None:
        raise ValueError("unknown instrument")
    if len(answers) != len(items) or any(a not in (0, 1, 2, 3) for a in answers):
        raise ValueError(f"{instrument} needs {len(items)} answers, each 0-3")
    total = sum(answers)
    bands = _PHQ_BANDS if instrument == "phq9" else _GAD_BANDS
    band = next(label for limit, label in bands if total <= limit)
    item9 = instrument == "phq9" and answers[8] > 0
    escalate = item9 or (instrument == "phq9" and total >= 15) or (instrument == "gad7" and total >= 15)
    msg = (
        f"Your answers add up to {total}, which falls in the '{band}' range on this screening questionnaire. "
        "This is a screening result to start a conversation, not a diagnosis. "
    )
    if band in ("minimal",):
        msg += "Many people find it helpful to keep talking with family or friends and to stay active. You can repeat this check-in in a few weeks."
    else:
        msg += "It would be a good idea to share this with your doctor or a trained counsellor, who can talk with you about how you have been feeling."
    if escalate:
        msg += " Because of your answers, please speak to a health professional soon. You can call Tele-MANAS on 14416 (free, 24x7) at any time."
    if item9:
        msg += " You said you have had thoughts of being better off dead or of hurting yourself. You matter, and support is available right now: call 14416, or 112 if you are in immediate danger. Please tell someone you trust."
    return ScreeningResult(instrument, total, band, escalate, msg, CRISIS_RESOURCES if escalate else [])
