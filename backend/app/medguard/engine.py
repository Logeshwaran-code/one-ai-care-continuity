"""MedGuard: brand -> generic -> ingredient normalisation, duplicate therapy, drug-drug interaction and
allergy checks. Pure functions over the knowledge base so every output is testable and every alert carries a
source and confidence. The engine never tells anyone to stop or change a medicine."""
import difflib
import json
import re
from dataclasses import asdict, dataclass, field
from itertools import combinations
from pathlib import Path
from typing import Any

from app.guardrails import ESCALATE, ensure_safe

KB_PATH = Path(__file__).resolve().parent.parent / "knowledge" / "seed_drugs.json"
SEVERITY_RANK = {"info": 0, "moderate": 1, "major": 2}
_DOSE = re.compile(r"\b\d+(\.\d+)?\s*(mg|mcg|g|ml|iu|%)\b", re.IGNORECASE)
_FORM = re.compile(r"\b(tab|tabs|tablet|tablets|cap|caps|capsule|capsules|syrup|inj|injection|sr|xr|er|ip|bp)\b", re.IGNORECASE)
_NUM = re.compile(r"\b\d+(\.\d+)?\b")


@dataclass
class Resolution:
    query: str
    product_key: str | None
    ingredients: list[str]
    generic_name: str | None
    confidence: float
    method: str  # exact | token | fuzzy | none
    needs_confirmation: bool = True  # always true: a human must confirm every resolved medicine
    candidates: list[str] = field(default_factory=list)


@dataclass
class Alert:
    kind: str  # duplicate | interaction | allergy
    severity: str
    title: str
    explanation: str
    involved: list[str]
    source: str
    confidence: str
    reviewed: bool
    escalation: str
    rule_id: str

    @property
    def key(self) -> str:
        return f"{self.kind}|{'+'.join(sorted(self.involved))}"

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["key"] = self.key
        return d


class KnowledgeBase:
    def __init__(self, data: dict[str, Any]) -> None:
        self.meta = data["_meta"]
        self.ingredients: dict[str, dict[str, Any]] = data["ingredients"]
        self.products: dict[str, list[str]] = data["products"]
        self.duplicate_classes: dict[str, str] = data["duplicate_classes"]
        self.interactions: list[dict[str, Any]] = data["interactions"]

    @classmethod
    def load(cls, path: Path = KB_PATH) -> "KnowledgeBase":
        return cls(json.loads(path.read_text(encoding="utf-8")))

    def classes_of(self, ingredient: str) -> set[str]:
        return set(self.ingredients.get(ingredient, {}).get("classes", []))

    def tags_of(self, ingredient: str) -> set[str]:
        return {ingredient} | self.classes_of(ingredient)

    def is_antibiotic(self, ingredients: list[str]) -> bool:
        return any("antibiotic" in self.classes_of(i) for i in ingredients)

    @staticmethod
    def normalise(text: str) -> str:
        t = _DOSE.sub(" ", text.lower())
        t = _FORM.sub(" ", t)
        t = _NUM.sub(" ", t)
        t = re.sub(r"[^a-z\s]", " ", t)
        return re.sub(r"\s+", " ", t).strip()

    def resolve(self, text: str) -> Resolution:
        q = self.normalise(text)
        if not q:
            return Resolution(text, None, [], None, 0.0, "none")
        if q in self.products:
            return self._res(text, q, 1.0, "exact")
        tokens = q.split()
        for n in (2, 1):  # try multi-word keys first
            for i in range(len(tokens) - n + 1):
                key = " ".join(tokens[i : i + n])
                if key in self.products:
                    return self._res(text, key, 0.9, "token")
        close = difflib.get_close_matches(q, list(self.products), n=3, cutoff=0.75)
        if close:
            ratio = difflib.SequenceMatcher(None, q, close[0]).ratio()
            res = self._res(text, close[0], round(min(ratio, 0.85), 2), "fuzzy")
            res.candidates = close
            return res
        return Resolution(text, None, [], None, 0.0, "none")

    def _res(self, text: str, key: str, conf: float, method: str) -> Resolution:
        ings = self.products[key]
        return Resolution(text, key, list(ings), " + ".join(ings), conf, method)

    # ------------------------------------------------------------------------------ analysis
    def analyze(self, products: list[Resolution], allergies: list[str] | None = None) -> list[Alert]:
        alerts: dict[str, Alert] = {}
        known = [p for p in products if p.ingredients]
        for p1, p2 in combinations(known, 2):
            for a in self._duplicates(p1, p2) + self._interactions(p1, p2):
                alerts.setdefault(a.key + a.rule_id, a)
        for p in known:
            for a in self._allergies(p, allergies or []):
                alerts.setdefault(a.key + a.rule_id, a)
        return sorted(alerts.values(), key=lambda a: (-SEVERITY_RANK[a.severity], a.kind, a.key))

    def _mk(self, kind: str, sev: str, title: str, expl: str, involved: list[str], source: str, conf: str,
            reviewed: bool, rule_id: str, lang: str = "en") -> Alert:
        expl = ensure_safe(expl, lang)  # runtime safety check on every explanation
        return Alert(kind, sev, title, expl, involved, source, conf, reviewed, ESCALATE[lang], rule_id)

    def _duplicates(self, p1: Resolution, p2: Resolution) -> list[Alert]:
        out: list[Alert] = []
        names = [p1.generic_name or "", p2.generic_name or ""]
        shared = set(p1.ingredients) & set(p2.ingredients)
        for ing in sorted(shared):
            out.append(self._mk(
                "duplicate", "major", f"Same ingredient twice: {ing}",
                f"Both '{p1.query}' and '{p2.query}' contain {ing}. Taking the same ingredient from two products can lead to too much of it.",
                names, "Ingredient match against seed knowledge base", "high", False, f"DUP-ING-{ing}"))
        c1 = {c for i in p1.ingredients for c in self.classes_of(i)}
        c2 = {c for i in p2.ingredients for c in self.classes_of(i)}
        for cls in sorted((c1 & c2) & set(self.duplicate_classes)):
            if all(cls in self.classes_of(i) and i in shared for i in p1.ingredients if cls in self.classes_of(i)):
                continue  # already reported as same-ingredient duplicate
            out.append(self._mk(
                "duplicate", self.duplicate_classes[cls], f"Possible duplicate therapy: two '{cls.replace('_', ' ')}' medicines",
                f"'{p1.query}' ({names[0]}) and '{p2.query}' ({names[1]}) belong to the same medicine family ({cls.replace('_', ' ')}). Medicines from the same family are not usually combined unless a doctor has planned it.",
                names, "Therapeutic-class match (ATC/class) against seed knowledge base", "moderate", False, f"DUP-CLS-{cls}"))
        return out

    def _interactions(self, p1: Resolution, p2: Resolution) -> list[Alert]:
        out: list[Alert] = []
        t1 = {t for i in p1.ingredients for t in self.tags_of(i)}
        t2 = {t for i in p2.ingredients for t in self.tags_of(i)}
        for rule in self.interactions:
            a, b = rule["a"], rule["b"]
            if (a in t1 and b in t2) or (a in t2 and b in t1):
                names = [p1.generic_name or "", p2.generic_name or ""]
                out.append(self._mk(
                    "interaction", rule["severity"], f"Possible interaction: {names[0]} and {names[1]}", rule["plain"], names,
                    rule["source"], rule["confidence"], False, rule["id"]))
        return out

    def _allergies(self, p: Resolution, allergies: list[str]) -> list[Alert]:
        out: list[Alert] = []
        tags = {t for i in p.ingredients for t in self.tags_of(i)} | {p.product_key or ""}
        for raw in allergies:
            al = self.normalise(raw)
            if al and al in tags:
                out.append(self._mk(
                    "allergy", "major", f"Allergy alert: {raw}",
                    f"'{p.query}' ({p.generic_name}) matches the allergy you recorded ({raw}). Please tell your doctor or pharmacist about this allergy before using it.",
                    [p.generic_name or "", f"allergy:{al}"], "Allergy record vs ingredient/class match in seed knowledge base", "high", False, f"ALG-{al}"))
        return out


_kb: KnowledgeBase | None = None


def get_kb() -> KnowledgeBase:
    global _kb
    if _kb is None:
        _kb = KnowledgeBase.load()
    return _kb
