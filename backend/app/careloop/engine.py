"""CareLoop: personal baselines, trend detection, adherence and explainable risk flags.
Every flag is rule-based or simple statistics (median/MAD, least-squares slope) and carries its numbers
and rule id, so a clinician can see exactly why it fired. Thresholds are CONFIGURABLE defaults that a
clinician must confirm per patient; flags are prompts to contact the care team, never diagnoses."""
import statistics
from dataclasses import asdict, dataclass, field
from datetime import date, datetime, timedelta
from typing import Any

SLOT_CUTOFF_HOUR = {"morning": 12, "afternoon": 17, "evening": 21, "night": 23}


@dataclass(frozen=True)
class Thresholds:
    bp_urgent_sys: float = 180
    bp_urgent_dia: float = 120
    bp_high_sys: float = 160
    bp_high_dia: float = 100
    bp_low_sys: float = 90
    glucose_urgent_low: float = 54
    glucose_low: float = 70
    glucose_high: float = 250
    glucose_urgent_high: float = 300
    adherence_min: float = 0.8
    consecutive_missed: int = 2
    baseline_days: int = 30
    baseline_min_n: int = 7
    recent_days: int = 3
    trend_days: int = 14
    trend_min_n: int = 6
    bp_trend_delta: float = 10.0  # mmHg change over trend window


DEFAULT = Thresholds()
THRESHOLD_NOTE = "Default review thresholds are common general-purpose cut-offs and must be confirmed or changed by the patient's clinician."
EMERGENCY_NOTE = " If you also have chest pain, trouble breathing, confusion, weakness on one side, or a severe headache, call 112 now."


@dataclass
class Reading:
    at: datetime
    v1: float
    v2: float | None = None


@dataclass
class Flag:
    rule_id: str
    severity: str  # info | watch | urgent_review
    title: str
    explanation: str
    data: dict[str, Any] = field(default_factory=dict)
    clinician_review: bool = True

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def median_mad(xs: list[float]) -> tuple[float, float]:
    m = statistics.median(xs)
    return m, statistics.median([abs(x - m) for x in xs])


def slope_per_day(points: list[tuple[datetime, float]]) -> float:
    """Ordinary least-squares slope in units per day."""
    if len(points) < 2:
        return 0.0
    t0 = points[0][0]
    xs = [(t - t0).total_seconds() / 86400 for t, _ in points]
    ys = [v for _, v in points]
    mx, my = statistics.fmean(xs), statistics.fmean(ys)
    den = sum((x - mx) ** 2 for x in xs)
    return 0.0 if den == 0 else sum((x - mx) * (y - my) for x, y in zip(xs, ys, strict=True)) / den


def baseline(readings: list[Reading], now: datetime, th: Thresholds = DEFAULT) -> dict[str, float] | None:
    """Personal baseline = median/MAD of the window BEFORE the recent days (so recent change is not in its own baseline)."""
    lo, hi = now - timedelta(days=th.baseline_days), now - timedelta(days=th.recent_days)
    win = [r for r in readings if lo <= r.at < hi]
    if len(win) < th.baseline_min_n:
        return None
    m1, d1 = median_mad([r.v1 for r in win])
    out = {"n": float(len(win)), "median_v1": m1, "mad_v1": d1}
    v2 = [r.v2 for r in win if r.v2 is not None]
    if v2:
        out["median_v2"] = statistics.median(v2)
    return out


def evaluate_bp(readings: list[Reading], now: datetime, th: Thresholds = DEFAULT) -> list[Flag]:
    flags: list[Flag] = []
    rs = sorted(readings, key=lambda r: r.at)
    if not rs:
        return flags
    last = rs[-1]
    sys_, dia = last.v1, last.v2 or 0
    if sys_ >= th.bp_urgent_sys or dia >= th.bp_urgent_dia:
        flags.append(Flag("BP-URGENT", "urgent_review", "Blood pressure reading is very high",
                          f"Your latest reading was {sys_:.0f}/{dia:.0f} mmHg, at or above {th.bp_urgent_sys:.0f}/{th.bp_urgent_dia:.0f}. Please recheck after resting for 5 minutes and contact your doctor today." + EMERGENCY_NOTE,
                          {"sys": sys_, "dia": dia}))
    elif sys_ >= th.bp_high_sys or dia >= th.bp_high_dia:
        flags.append(Flag("BP-HIGH", "watch", "Blood pressure reading is above the review level",
                          f"Your latest reading was {sys_:.0f}/{dia:.0f} mmHg, at or above {th.bp_high_sys:.0f}/{th.bp_high_dia:.0f}. Consider contacting your care team and sharing this at your next visit.",
                          {"sys": sys_, "dia": dia}))
    elif sys_ < th.bp_low_sys:
        flags.append(Flag("BP-LOW", "watch", "Blood pressure reading is low",
                          f"Your latest reading was {sys_:.0f}/{dia:.0f} mmHg (systolic below {th.bp_low_sys:.0f}). If you feel dizzy or faint, sit or lie down and contact your care team.",
                          {"sys": sys_, "dia": dia}))
    base = baseline(rs, now, th)
    recent = [r for r in rs if r.at >= now - timedelta(days=th.recent_days)]
    if base and recent:
        rec_med = statistics.median([r.v1 for r in recent])
        delta = rec_med - base["median_v1"]
        band = max(10.0, 3 * 1.4826 * base["mad_v1"])
        if abs(delta) > band:
            direction = "higher" if delta > 0 else "lower"
            flags.append(Flag("BP-BASELINE-SHIFT", "watch", f"Recent blood pressure is {direction} than your usual",
                              f"Your last {th.recent_days} days have a median systolic of {rec_med:.0f}, compared with your usual {base['median_v1']:.0f} (change {delta:+.0f} mmHg; flag level is more than {band:.0f}). Worth mentioning to your care team.",
                              {"recent_median": rec_med, "baseline_median": base["median_v1"], "delta": delta, "band": band, "baseline_n": base["n"]}))
    trend_pts = [(r.at, r.v1) for r in rs if r.at >= now - timedelta(days=th.trend_days)]
    if len(trend_pts) >= th.trend_min_n:
        change = slope_per_day(trend_pts) * th.trend_days
        if change >= th.bp_trend_delta:
            flags.append(Flag("BP-TREND-UP", "info", "Blood pressure has been drifting upward",
                              f"Over the last {th.trend_days} days, systolic readings have trended up by about {change:.0f} mmHg (from {len(trend_pts)} readings).",
                              {"change": change, "n": len(trend_pts)}))
    return flags


def evaluate_glucose(readings: list[Reading], now: datetime, th: Thresholds = DEFAULT) -> list[Flag]:
    rs = sorted(readings, key=lambda r: r.at)
    if not rs:
        return []
    g = rs[-1].v1
    if g < th.glucose_urgent_low:
        return [Flag("GLU-URGENT-LOW", "urgent_review", "Blood sugar reading is very low",
                     f"Your latest reading was {g:.0f} mg/dL (below {th.glucose_urgent_low:.0f}). Follow the low-sugar plan your doctor gave you and get help now." + EMERGENCY_NOTE, {"glucose": g})]
    if g < th.glucose_low:
        return [Flag("GLU-LOW", "watch", "Blood sugar reading is low",
                     f"Your latest reading was {g:.0f} mg/dL (below {th.glucose_low:.0f}). Follow the plan your doctor gave you for low sugar and let your care team know.", {"glucose": g})]
    if g >= th.glucose_urgent_high:
        return [Flag("GLU-URGENT-HIGH", "urgent_review", "Blood sugar reading is very high",
                     f"Your latest reading was {g:.0f} mg/dL (at or above {th.glucose_urgent_high:.0f}). Please contact your doctor today." + EMERGENCY_NOTE, {"glucose": g})]
    if g >= th.glucose_high:
        return [Flag("GLU-HIGH", "watch", "Blood sugar reading is high",
                     f"Your latest reading was {g:.0f} mg/dL (at or above {th.glucose_high:.0f}). Consider sharing this with your care team.", {"glucose": g})]
    return []


# ----------------------------------------------------------------------------- adherence
@dataclass
class MedSchedule:
    id: int
    name: str
    timing: list[str]
    start: date
    end: date | None = None  # last course day (inclusive) or None


def expected_slots(meds: list[MedSchedule], since: date, now: datetime) -> list[tuple[int, date, str]]:
    out: list[tuple[int, date, str]] = []
    today = now.date()
    d = since
    while d <= today:
        for m in meds:
            if d < m.start or (m.end and d > m.end):
                continue
            for slot in m.timing:
                if d == today and now.hour < SLOT_CUTOFF_HOUR.get(slot, 23):
                    continue  # slot not yet due/overdue
                out.append((m.id, d, slot))
        d += timedelta(days=1)
    return out


def adherence(meds: list[MedSchedule], taken: set[tuple[int, date, str]], now: datetime, days: int = 7,
              th: Thresholds = DEFAULT) -> tuple[dict[str, Any], list[Flag]]:
    since = now.date() - timedelta(days=days - 1)
    slots = expected_slots(meds, since, now)
    per: dict[int, dict[str, Any]] = {m.id: {"name": m.name, "expected": 0, "taken": 0, "missed": []} for m in meds}
    for mid, d, slot in sorted(slots, key=lambda s: (s[0], s[1], s[2])):
        per[mid]["expected"] += 1
        if (mid, d, slot) in taken:
            per[mid]["taken"] += 1
        else:
            per[mid]["missed"].append((d, slot))
    exp = sum(p["expected"] for p in per.values())
    tk = sum(p["taken"] for p in per.values())
    rate = (tk / exp) if exp else None
    flags: list[Flag] = []
    if rate is not None and rate < th.adherence_min:
        flags.append(Flag("ADH-LOW", "watch", "Many doses were missed this week",
                          f"{tk} of {exp} scheduled doses were logged in the last {days} days ({rate:.0%}). If doses are being missed because of side effects, cost or forgetting, tell your care team - do not change medicines on your own.",
                          {"taken": tk, "expected": exp, "rate": rate}))
    for mid, p in per.items():
        run = longest_run(p["missed"], next(m.timing for m in meds if m.id == mid))
        if run >= th.consecutive_missed:
            flags.append(Flag("ADH-STREAK", "watch", f"Several missed doses in a row: {p['name']}",
                              f"{run} scheduled doses of {p['name']} in a row have not been logged. Please let your pharmacist or doctor know - do not double up on doses to catch up.",
                              {"medication_id": mid, "run": run}))
    summary = {"days": days, "expected": exp, "taken": tk, "rate": rate,
               "per_medication": [{"medication_id": mid, "name": p["name"], "expected": p["expected"], "taken": p["taken"],
                                   "missed": [f"{d.isoformat()} {s}" for d, s in p["missed"]]} for mid, p in per.items()]}
    return summary, flags


_ORDER = ["morning", "afternoon", "evening", "night"]


def longest_run(missed: list[tuple[date, str]], timing: list[str]) -> int:
    """Longest run of consecutive scheduled slots (in time order) that were missed."""
    if not missed:
        return 0
    slots = sorted(timing, key=_ORDER.index)
    idx = {(d, s): d.toordinal() * 10 + slots.index(s) for d, s in missed}
    # convert to consecutive positions: day * len(slots) + slot position
    pos = sorted(d.toordinal() * len(slots) + slots.index(s) for d, s in idx)
    best = cur = 1
    for a, b in zip(pos, pos[1:], strict=False):
        cur = cur + 1 if b == a + 1 else 1
        best = max(best, cur)
    return best


# ----------------------------------------------------------------------------- summary helpers
def series_stats(readings: list[Reading], since: datetime) -> dict[str, Any] | None:
    rs = [r for r in readings if r.at >= since]
    if not rs:
        return None
    v1 = [r.v1 for r in rs]
    out: dict[str, Any] = {"n": len(rs), "avg": round(statistics.fmean(v1), 1), "min": min(v1), "max": max(v1)}
    v2 = [r.v2 for r in rs if r.v2 is not None]
    if v2:
        out["avg_v2"] = round(statistics.fmean(v2), 1)
    return out


def suggested_questions(flags: list[Flag], med_alert_count: int, has_antibiotic: bool) -> list[str]:
    qs: list[str] = []
    ids = {f.rule_id for f in flags}
    if ids & {"BP-HIGH", "BP-URGENT", "BP-BASELINE-SHIFT", "BP-TREND-UP"}:
        qs.append("My blood pressure readings have changed recently. Should we review my treatment plan?")
    if ids & {"GLU-HIGH", "GLU-URGENT-HIGH", "GLU-LOW", "GLU-URGENT-LOW"}:
        qs.append("My blood sugar readings have been outside the usual range. What should I watch for and what is my plan?")
    if ids & {"ADH-LOW", "ADH-STREAK"}:
        qs.append("I have been missing some doses. Is there a simpler schedule or a reason this is happening that we can talk about?")
    if med_alert_count:
        qs.append("My medicine list was flagged for possible duplicates or interactions. Can you or the pharmacist review the list with me?")
    if has_antibiotic:
        qs.append("What should I do if I miss a dose of my antibiotic course?")
    qs.append("Are there any tests or check-ups that are due?")
    return qs
