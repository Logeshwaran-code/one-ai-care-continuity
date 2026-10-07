"""Antibiotic safety: adherence/course tracking and education for antibiotics a clinician ALREADY prescribed.
This module never selects, starts, stops or changes an antibiotic."""
from datetime import date, timedelta
from typing import Any

EDUCATION = {
    "en": [
        "Antibiotics only work against bacterial infections, not colds or most coughs and sore throats caused by viruses.",
        "Only take an antibiotic that a doctor has prescribed for you. Never use leftover antibiotics or ones meant for someone else.",
        "Do not start, stop or change an antibiotic without medical advice. If you feel better early, or feel unwell on it, call your doctor or pharmacist and ask what to do.",
        "Using antibiotics when they are not needed, or not as prescribed, helps bacteria become resistant, which makes future infections harder to treat for everyone.",
        "If you miss a dose, do not double the next one. Ask your pharmacist or doctor what to do.",
        "Seek urgent medical help for swelling of the face or lips, trouble breathing, a widespread rash, or severe diarrhoea.",
    ],
}


def course_status(name: str, start: date, course_days: int | None, today: date) -> dict[str, Any]:
    out: dict[str, Any] = {"name": name, "start": start.isoformat(), "course_days": course_days}
    if course_days:
        end = start + timedelta(days=course_days - 1)
        out.update({"planned_last_day": end.isoformat(), "day_number": min((today - start).days + 1, course_days), "days_left": max((end - today).days, 0),
                    "complete": today > end})
    out["note"] = "Follow your prescription exactly. If you have questions or problems, ask your doctor or pharmacist - do not change the course on your own."
    return out
