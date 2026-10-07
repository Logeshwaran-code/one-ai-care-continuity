import json
from pathlib import Path

import pytest

from app.guardrails import validate_output
from app.medguard.engine import KnowledgeBase, get_kb
from app.medguard.ocr import extract_candidates

kb = get_kb()
GOLDEN = json.loads((Path(__file__).parent.parent / "eval" / "golden_interactions.json").read_text(encoding="utf-8"))


def run(meds: list[str], allergies: list[str] | None = None):
    return kb.analyze([kb.resolve(m) for m in meds], allergies)


@pytest.mark.parametrize("text,key", [("Glycomet 500 tablet", "glycomet"), ("TELMA 40mg", "telma"), ("Dolo 650", "dolo"),
                                      ("telmisartan", "telmisartan"), ("Glycomit", "glycomet")])
def test_resolution(text, key):
    assert kb.resolve(text).product_key == key


def test_unknown_drug_not_guessed():
    r = kb.resolve("zzzxqv")
    assert r.product_key is None and r.confidence == 0


def test_brand_to_ingredient():
    assert kb.resolve("Augmentin 625").ingredients == ["amoxicillin", "clavulanic acid"]


def test_always_needs_confirmation():
    assert all(kb.resolve(n).needs_confirmation for n in ["telma", "metformin"])


@pytest.mark.parametrize("case", GOLDEN["cases"], ids=lambda c: c["name"])
def test_golden(case):
    got = {a.key for a in run(case["meds"], case.get("allergies"))}
    assert got == set(case["expect"])


def test_alerts_have_source_and_escalation_and_are_safe():
    alerts = run(["Telma", "Losar", "Voveran", "Warf", "Ecosprin", "Augmentin"], ["penicillin"])
    assert alerts
    for a in alerts:
        assert a.source and a.confidence and a.escalation and a.reviewed is False
        assert validate_output(a.explanation) == []
        assert "stop" not in a.explanation.lower()


def test_severity_sorted_desc():
    alerts = run(["Telma", "Losar", "Voveran"])
    ranks = [{"major": 2, "moderate": 1, "info": 0}[a.severity] for a in alerts]
    assert ranks == sorted(ranks, reverse=True)


def test_no_self_pairs_in_combination_product():
    assert run(["Combiflam"]) == []


def test_ocr_candidates_confidence_scaled():
    cands = extract_candidates("Glycomet 500\nTelma 40\nrandom words", ocr_confidence=0.8)
    assert [c.product_key for c in cands] == ["glycomet", "telma"]
    assert all(c.confidence <= 0.8 and c.needs_confirmation for c in cands)


def test_kb_is_labelled_seed():
    assert "SEED" in KnowledgeBase.load().meta["label"]
