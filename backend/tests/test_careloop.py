from datetime import date, datetime, timedelta

from app.careloop.engine import (
    MedSchedule,
    Reading,
    adherence,
    baseline,
    evaluate_bp,
    evaluate_glucose,
    longest_run,
    median_mad,
    slope_per_day,
    suggested_questions,
)
from app.guardrails import validate_output

NOW = datetime(2026, 10, 7, 22, 0)


def bp_series(values, end=NOW):
    return [Reading(end - timedelta(days=len(values) - 1 - i, hours=1), v, 80) for i, v in enumerate(values)]


def test_median_mad_and_slope():
    assert median_mad([1, 2, 3, 4, 100]) == (3, 1)
    pts = [(datetime(2026, 1, 1) + timedelta(days=i), 100 + 2 * i) for i in range(10)]
    assert abs(slope_per_day(pts) - 2) < 1e-9
    assert slope_per_day(pts[:1]) == 0.0


def test_baseline_needs_enough_data():
    assert baseline(bp_series([130] * 5), NOW) is None
    b = baseline(bp_series([130] * 20), NOW)
    assert b and b["median_v1"] == 130


def test_bp_urgent_and_high_and_low():
    assert evaluate_bp([Reading(NOW, 185, 100)], NOW)[0].rule_id == "BP-URGENT"
    assert evaluate_bp([Reading(NOW, 165, 90)], NOW)[0].rule_id == "BP-HIGH"
    assert evaluate_bp([Reading(NOW, 85, 55)], NOW)[0].rule_id == "BP-LOW"
    assert evaluate_bp([Reading(NOW, 125, 80)], NOW) == []


def test_baseline_shift_flag_is_explainable():
    vals = [128, 130, 129, 131, 130, 128, 132, 130, 129, 131, 130, 129] + [150, 152, 151]
    flags = {f.rule_id: f for f in evaluate_bp(bp_series(vals), NOW)}
    f = flags["BP-BASELINE-SHIFT"]
    assert f.data["delta"] > 15 and f.data["baseline_n"] >= 7 and "usual" in f.explanation


def test_trend_up_flag():
    vals = [120 + i * 2 for i in range(14)]
    assert "BP-TREND-UP" in {f.rule_id for f in evaluate_bp(bp_series(vals), NOW)}


def test_stable_no_flags():
    assert evaluate_bp(bp_series([130, 131, 129, 130, 132, 130, 129, 131, 130, 130, 131, 129, 130, 131]), NOW) == []


def test_glucose_rules():
    ids = [evaluate_glucose([Reading(NOW, g)], NOW)[0].rule_id for g in (50, 65, 260, 320)]
    assert ids == ["GLU-URGENT-LOW", "GLU-LOW", "GLU-HIGH", "GLU-URGENT-HIGH"]
    assert evaluate_glucose([Reading(NOW, 110)], NOW) == []


def test_all_flag_text_is_guardrail_safe():
    fl = evaluate_bp([Reading(NOW, 190, 125)], NOW) + evaluate_glucose([Reading(NOW, 40)], NOW)
    for f in fl:
        assert validate_output(f.explanation) == [], f.explanation


def meds():
    return [MedSchedule(1, "Metformin", ["morning", "night"], date(2026, 9, 1))]


def test_adherence_full_and_low():
    taken = {(1, date(2026, 10, 7) - timedelta(days=d), s) for d in range(7) for s in ("morning", "night")}
    s, fl = adherence(meds(), taken, NOW)
    assert s["rate"] == 1.0 and fl == []
    s2, fl2 = adherence(meds(), set(), NOW)
    assert s2["rate"] == 0 and {f.rule_id for f in fl2} == {"ADH-LOW", "ADH-STREAK"}


def test_today_slot_not_counted_before_cutoff():
    early = datetime(2026, 10, 7, 8, 0)
    s, _ = adherence(meds(), set(), early, days=1)
    assert s["expected"] == 0


def test_longest_run():
    miss = [(date(2026, 10, 5), "night"), (date(2026, 10, 6), "morning"), (date(2026, 10, 6), "night")]
    assert longest_run(miss, ["morning", "night"]) == 3
    assert longest_run([(date(2026, 10, 5), "morning"), (date(2026, 10, 6), "morning")], ["morning", "night"]) == 1


def test_suggested_questions_have_no_directives():
    f = evaluate_bp([Reading(NOW, 170, 95)], NOW)
    for q in suggested_questions(f, 1, True):
        assert validate_output(q) == []
