"""Visit-summary assembly (deterministic facts -> optional LLM narrative -> guardrail check) and PDF export."""
import io
from typing import Any

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from app.guardrails import DISCLAIMER, ensure_safe


def facts_text(c: dict[str, Any]) -> str:
    parts = [f"Patient {c['patient_name']}."]
    bp = c.get("bp")
    if bp:
        parts.append(f"{bp['n']} blood pressure readings in 30 days, average {bp['avg']}/{bp.get('avg_v2', '-')} mmHg (range systolic {bp['min']:.0f}-{bp['max']:.0f}).")
    g = c.get("glucose")
    if g:
        parts.append(f"{g['n']} glucose readings, average {g['avg']} mg/dL (range {g['min']:.0f}-{g['max']:.0f}).")
    a = c["adherence"]
    if a["rate"] is not None:
        parts.append(f"Dose adherence over the last {a['days']} days: {a['taken']} of {a['expected']} doses logged ({a['rate']:.0%}).")
    if c["flags"]:
        parts.append("Flags: " + "; ".join(f["title"] for f in c["flags"]) + ".")
    if c["medication_alerts"]:
        parts.append(f"{len(c['medication_alerts'])} medicine-list alert(s) need clinician review.")
    return " ".join(parts)


def render_pdf(c: dict[str, Any]) -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, title="Show your doctor - visit summary", leftMargin=40, rightMargin=40, topMargin=40, bottomMargin=40)
    st = getSampleStyleSheet()
    els: list[Any] = [Paragraph("Show your doctor: visit summary", st["Title"]),
                      Paragraph(f"Patient: {c['patient_name']} &nbsp;&nbsp; Status: <b>{c['status'].upper()}</b> "
                                f"({'reviewed and approved by a clinician' if c['status'] == 'approved' else 'AI-assisted DRAFT - clinician review required'})", st["Normal"]),
                      Spacer(1, 10), Paragraph("Overview", st["Heading2"]), Paragraph(c["narrative"], st["Normal"])]
    rows: list[list[str]] = [["Measure", "Readings", "Average", "Range"]]
    if c.get("bp"):
        b = c["bp"]
        rows.append(["Blood pressure (mmHg)", str(b["n"]), f"{b['avg']}/{b.get('avg_v2', '-')}", f"sys {b['min']:.0f}-{b['max']:.0f}"])
    if c.get("glucose"):
        g = c["glucose"]
        rows.append(["Glucose (mg/dL)", str(g["n"]), str(g["avg"]), f"{g['min']:.0f}-{g['max']:.0f}"])
    if c.get("weight"):
        w = c["weight"]
        rows.append(["Weight (kg)", str(w["n"]), str(w["avg"]), f"{w['min']:.0f}-{w['max']:.0f}"])
    if len(rows) > 1:
        t = Table(rows, hAlign="LEFT")
        t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey), ("GRID", (0, 0), (-1, -1), 0.5, colors.grey)]))
        els += [Spacer(1, 8), Paragraph("Trends (last 30 days)", st["Heading2"]), t]
    a = c["adherence"]
    els += [Paragraph("Medicine adherence", st["Heading2"]),
            Paragraph(f"{a['taken']} of {a['expected']} scheduled doses logged in the last {a['days']} days.", st["Normal"])]
    for m in a["per_medication"]:
        els.append(Paragraph(f"- {m['name']}: {m['taken']}/{m['expected']}", st["Normal"]))
    if c["flags"]:
        els.append(Paragraph("Flags (rule-based, with reasons)", st["Heading2"]))
        els += [Paragraph(f"<b>{f['title']}</b> [{f['rule_id']}]: {f['explanation']}", st["Normal"]) for f in c["flags"]]
    if c["medication_alerts"]:
        els.append(Paragraph("Medicine-list alerts (seed knowledge base, needs clinician review)", st["Heading2"]))
        els += [Paragraph(f"<b>{x['title']}</b> ({x['severity']}): {x['explanation']}", st["Normal"]) for x in c["medication_alerts"]]
    els.append(Paragraph("Suggested questions for the visit", st["Heading2"]))
    els += [Paragraph(f"{i}. {q}", st["Normal"]) for i, q in enumerate(c["questions"], 1)]
    els += [Spacer(1, 14), Paragraph(f"<i>{DISCLAIMER['en']}</i>", st["Normal"])]
    doc.build(els)
    return buf.getvalue()


def safe_narrative(text: str) -> str:
    return ensure_safe(text, "en")
