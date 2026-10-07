import json

import pytest
from pydantic import BaseModel

from app import cost
from app.antibiotic import course_status
from app.guardrails import validate_output
from app.llm import LLMGateway, LLMRequest


class Flaky:
    name = "flaky"

    def __init__(self, fail: int, out: str):
        self.fail, self.out, self.calls = fail, out, 0

    async def complete(self, req: LLMRequest) -> str:
        self.calls += 1
        if self.calls <= self.fail:
            raise RuntimeError("boom")
        return self.out


async def test_gateway_retries_then_succeeds_and_caches():
    p = Flaky(1, "Your report says: ok")
    g = LLMGateway(p)
    assert await g.generate("simplify", {"text": "x", "level": "simple", "target": "en"}) == "Your report says: ok"
    n = p.calls
    await g.generate("simplify", {"text": "x", "level": "simple", "target": "en"})
    assert p.calls == n  # served from cache


async def test_gateway_gives_up_after_retries():
    with pytest.raises(RuntimeError):
        await LLMGateway(Flaky(99, "")).generate("simplify", {"text": "x", "level": "simple", "target": "en"})


class Out(BaseModel):
    ok: bool


async def test_structured_output_validation():
    assert (await LLMGateway(Flaky(0, json.dumps({"ok": True}))).generate("translate", {"text": "a", "target": "en"}, Out)).ok is True
    with pytest.raises(ValueError):
        await LLMGateway(Flaky(0, "not json")).generate("translate", {"text": "b", "target": "en"}, Out)


async def test_mock_simplify_levels_and_translate():
    g = LLMGateway()
    s = await g.generate("simplify", {"text": "Hypertension noted. BID dosing of antihypertensive.", "level": "simple", "target": "en"})
    assert "high blood pressure" in str(s) and "twice a day" in str(s)
    v = await g.generate("simplify", {"text": " ".join(["word"] * 40) + ".", "level": "very_simple", "target": "en"})
    assert "..." in str(v)
    t = await g.generate("translate", {"text": "Please talk to your doctor.", "target": "ta"})
    assert "மருத்துவரிடம்" in str(t)
    assert await g.generate("translate", {"text": "unknown phrase", "target": "hi"}) == "unknown phrase"
    assert await g.generate("translate", {"text": "same", "target": "en"}) == "same"


def test_cost_compare_and_csv(tmp_path):
    r = cost.compare("Glycomet 500")
    assert r["found"] and r["possible_saving_inr"] > 0 and r["data"]["as_of"] and "pharmacist" in r["confirm"]
    assert cost.compare("Augmentin")["found"] is False  # no price data -> says so, no invention
    f = tmp_path / "p.csv"
    f.write_text("generic,brand,brand_price_inr,generic_price_inr,pack,source,as_of\nmetformin,glycomet,40,10,10 tabs,PMBI list,2026-09-01\n")
    data = cost.load_prices_csv(f)
    assert cost.compare("glycomet", data)["generic_price_inr"] == 10 and data["_meta"]["source"] == "PMBI list"


def test_antibiotic_course_and_education_are_safe():
    from datetime import date

    s = course_status("Azithral 500", date(2026, 10, 5), 5, date(2026, 10, 7))
    assert s["day_number"] == 3 and s["days_left"] == 2 and not s["complete"]
    assert validate_output(s["note"]) == []
    assert course_status("x", date(2026, 10, 1), 5, date(2026, 10, 9))["complete"] is True
    from app.antibiotic import EDUCATION

    assert all(validate_output(line) == [] for line in EDUCATION["en"])
