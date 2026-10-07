"""Scripted demo of the Ravi scenario against a running server:  python scripts/demo_walkthrough.py http://localhost:8000"""
import json
import sys

import httpx

BASE = (sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000").rstrip("/") + "/api/v1"
PW = "Demo@12345"


def login(c: httpx.Client, email: str) -> dict[str, str]:
    r = c.post(f"{BASE}/auth/login", json={"email": email, "password": PW})
    r.raise_for_status()
    return {"Authorization": "Bearer " + r.json()["access_token"]}


def step(n: int, title: str) -> None:
    print(f"\n=== Step {n}: {title}")


with httpx.Client(timeout=30) as c:
    ravi, doc, worker, priya = (login(c, f"{u}@demo.test") for u in ("ravi", "doctor", "worker", "priya"))
    rid = c.get(f"{BASE}/me", headers=ravi).json()["id"]

    step(1, "Doctor reviews Ravi's current medicines (MedGuard report - clean baseline)")
    print(json.dumps(c.get(f"{BASE}/patients/{rid}/medguard/report", headers=doc).json()["alerts"], indent=1))

    step(2, "Doctor tries to add Losar 50 -> MedGuard flags duplicate ARB therapy; doctor must acknowledge")
    body = {"name": "Losar 50", "dose_text": "50 mg", "timing": ["morning"], "confirmed": True}
    r = c.post(f"{BASE}/patients/{rid}/prescriptions", headers=doc, json=body)
    print(r.status_code, r.json()["detail"]["alerts"][0]["title"])
    print("-> The doctor decides (AI never changes medicines). Acknowledging after review:")
    r = c.post(f"{BASE}/patients/{rid}/prescriptions", headers=doc, json={**body, "acknowledge_alerts": True})
    print(r.status_code, r.json()["note"])

    step(3, "CareLoop: explainable flags from Ravi's BP/sugar/adherence")
    for f in c.get(f"{BASE}/patients/{rid}/careloop/insights", headers=doc).json()["flags"]:
        print(f"[{f['severity']}] {f['rule_id']}: {f['explanation']}")

    step(4, "Ravi logs by voice; daughter Priya's dashboard (consent-scoped, minimised)")
    print(c.post(f"{BASE}/patients/{rid}/voice-log", headers=ravi, json={"text": "I took my morning medicine"}).json())
    c.post(f"{BASE}/patients/{rid}/measurements", headers=ravi, json={"kind": "bp", "v1": 142, "v2": 90})
    print(c.get(f"{BASE}/patients/{rid}/family-dashboard", headers=priya).json())

    step(5, "Pharmacist/health worker has a follow-up task")
    for t in c.get(f"{BASE}/tasks", headers=worker).json():
        print("-", t["patient"], ":", t["title"])

    step(6, "Doctor receives an AI-assisted DRAFT summary and approves it (human decides)")
    s = c.post(f"{BASE}/patients/{rid}/summary", headers=doc).json()
    print(s["status"], "|", s["content"]["narrative"])
    print("Suggested questions:", *s["content"]["questions"], sep="\n  - ")
    print(c.post(f"{BASE}/summaries/{s['id']}/approve", headers=doc).json())
    print("PDF bytes:", len(c.get(f"{BASE}/summaries/{s['id']}/pdf", headers=doc).content))

    step(7, "Guardrails: unsafe requests are refused in code")
    for q in ("Which antibiotic should I take?", "I want to end my life"):
        print(q, "->", c.post(f"{BASE}/assistant/ask", headers=ravi, json={"text": q}).json()["text"][:110], "...")
