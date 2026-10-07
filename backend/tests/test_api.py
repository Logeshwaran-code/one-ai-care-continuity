
P = "/api/v1"


async def ravi_id(c, h):
    return (await c.get(f"{P}/me", headers=h)).json()["id"]


async def test_health_and_metrics(client):
    assert (await client.get("/health")).json() == {"status": "ok"}
    assert (await client.get("/ready")).status_code == 200
    assert b"http_requests_total" in (await client.get("/metrics")).content


async def test_auth_failures_and_refresh_rotation(client, auth):
    assert (await client.post(f"{P}/auth/login", json={"email": "ravi@demo.test", "password": "wrong-password"})).status_code == 401
    assert (await client.get(f"{P}/me")).status_code == 401
    _, tok = await auth(client, "ravi@demo.test")
    r1 = await client.post(f"{P}/auth/refresh", json={"refresh_token": tok["refresh_token"]})
    assert r1.status_code == 200
    reuse = await client.post(f"{P}/auth/refresh", json={"refresh_token": tok["refresh_token"]})
    assert reuse.status_code == 401  # reuse detected
    assert (await client.post(f"{P}/auth/refresh", json={"refresh_token": r1.json()["refresh_token"]})).status_code == 401  # family revoked


async def test_registration_cannot_create_staff(client):
    r = await client.post(f"{P}/auth/register", json={"email": "x@y.com", "name": "X", "password": "longenough123", "role": "doctor"})
    assert r.status_code == 403
    ok = await client.post(f"{P}/auth/register", json={"email": "new@y.com", "name": "New", "password": "longenough123", "role": "patient"})
    assert ok.status_code == 201


async def test_rbac_and_consent_scoping(client, auth):
    hr, _ = await auth(client, "ravi@demo.test")
    rid = await ravi_id(client, hr)
    hp, _ = await auth(client, "priya@demo.test")
    assert (await client.get(f"{P}/patients/{rid}/medications", headers=hp)).status_code == 403  # no medication scope
    assert (await client.get(f"{P}/patients/{rid}/family-dashboard", headers=hp)).status_code == 200
    ha, _ = await auth(client, "admin@demo.test")
    assert (await client.get(f"{P}/patients/{rid}/medications", headers=ha)).status_code == 403  # admin has no PHI access
    hd, _ = await auth(client, "doctor@demo.test")
    assert (await client.get(f"{P}/patients/{rid}/medications", headers=hd)).status_code == 200
    assert (await client.get(f"{P}/admin/audit", headers=hd)).status_code == 403
    audit = (await client.get(f"{P}/admin/audit", headers=ha)).json()
    assert any(a["allowed"] is False for a in audit) and any(a["action"] == "medication_list" for a in audit)


async def test_family_dashboard_is_minimised_and_consent_revocable(client, auth):
    hr, _ = await auth(client, "ravi@demo.test")
    rid = await ravi_id(client, hr)
    hp, _ = await auth(client, "priya@demo.test")
    d = (await client.get(f"{P}/patients/{rid}/family-dashboard", headers=hp)).json()
    assert set(d) >= {"medicine_taken_today", "bp_recorded_today", "next_appointment"} and "medicines" not in d
    cons = (await client.get(f"{P}/consents", headers=hr)).json()
    cid = next(c["id"] for c in cons if c["grantee"] == "priya@demo.test")
    assert (await client.delete(f"{P}/consents/{cid}", headers=hr)).status_code == 204
    assert (await client.get(f"{P}/patients/{rid}/family-dashboard", headers=hp)).status_code == 403
    r = await client.post(f"{P}/consents", headers=hr, json={"grantee_email": "priya@demo.test", "scopes": ["adherence", "measurements", "appointments"]})
    assert r.status_code == 201


async def test_demo_end_to_end(client, auth):
    hr, _ = await auth(client, "ravi@demo.test")
    rid = await ravi_id(client, hr)
    hd, _ = await auth(client, "doctor@demo.test")
    hw, _ = await auth(client, "worker@demo.test")
    hp, _ = await auth(client, "priya@demo.test")

    base = (await client.get(f"{P}/patients/{rid}/medguard/report", headers=hd)).json()
    assert base["alerts"] == [] and "SEED" in base["kb"]["label"]

    # 1. doctor prescribes a second ARB -> MedGuard blocks until acknowledged (409), alert shown
    body = {"name": "Losar 50", "dose_text": "50 mg", "timing": ["morning"], "confirmed": True}
    r = await client.post(f"{P}/patients/{rid}/prescriptions", headers=hd, json=body)
    assert r.status_code == 409 and r.json()["detail"]["alerts"][0]["kind"] == "duplicate"
    # unconfirmed names are rejected
    assert (await client.post(f"{P}/patients/{rid}/prescriptions", headers=hd, json={**body, "confirmed": False})).status_code == 422
    # patient cannot prescribe
    assert (await client.post(f"{P}/patients/{rid}/prescriptions", headers=hr, json=body)).status_code == 403
    ok = await client.post(f"{P}/patients/{rid}/prescriptions", headers=hd, json={**body, "acknowledge_alerts": True})
    assert ok.status_code == 201 and ok.json()["alerts"] and "doctor or pharmacist" in ok.json()["note"]

    # penicillin allergy conflict is caught
    al = await client.post(f"{P}/patients/{rid}/prescriptions", headers=hd, json={"name": "Mox 500", "timing": ["night"], "confirmed": True, "course_days": 5})
    assert al.status_code == 409 and al.json()["detail"]["alerts"][0]["kind"] == "allergy"

    # 2. worker received a follow-up task
    tasks = (await client.get(f"{P}/tasks", headers=hw)).json()
    assert any("Losar" in t["title"] for t in tasks)
    assert (await client.get(f"{P}/tasks", headers=hp)).status_code == 403
    assert (await client.post(f"{P}/tasks/{tasks[0]['id']}/complete", headers=hw)).status_code == 200

    # 3. CareLoop: explainable flags from seeded data, voice log, measurements
    ins = (await client.get(f"{P}/patients/{rid}/careloop/insights", headers=hd)).json()
    ids = {f["rule_id"] for f in ins["flags"]}
    assert "BP-BASELINE-SHIFT" in ids and ins["explainable"] and all(f["explanation"] for f in ins["flags"])
    v = await client.post(f"{P}/patients/{rid}/voice-log", headers=hr, json={"text": "I took my morning medicine"})
    assert v.json()["logged"] >= 4
    assert (await client.post(f"{P}/patients/{rid}/voice-log", headers=hr, json={"text": "hello"})).json()["logged"] == 0
    m = await client.post(f"{P}/patients/{rid}/measurements", headers=hr, json={"kind": "bp", "v1": 142, "v2": 90})
    assert m.status_code == 201
    assert (await client.post(f"{P}/patients/{rid}/measurements", headers=hr, json={"kind": "bp", "v1": 80, "v2": 120})).status_code == 422
    dash = (await client.get(f"{P}/patients/{rid}/family-dashboard", headers=hp)).json()
    assert dash["bp_recorded_today"] is True and dash["medicine_taken_today"]["taken"] >= 4

    # 4. AI-drafted summary -> doctor reviews/approves; patient cannot approve; PDF export
    s = await client.post(f"{P}/patients/{rid}/summary", headers=hd)
    assert s.status_code == 201 and s.json()["status"] == "draft"
    sid = s.json()["id"]
    c = s.json()["content"]
    assert c["questions"] and c["medication_alerts"] and "narrative" in c
    assert (await client.post(f"{P}/summaries/{sid}/approve", headers=hr)).status_code == 403
    assert (await client.post(f"{P}/summaries/{sid}/approve", headers=hd)).json()["status"] == "approved"
    pdf = await client.get(f"{P}/summaries/{sid}/pdf", headers=hd)
    assert pdf.content[:4] == b"%PDF"
    assert (await client.get(f"{P}/summaries/{sid}", headers=hp)).status_code == 403  # no summary scope


async def test_fhir_export(client, auth):
    hr, _ = await auth(client, "ravi@demo.test")
    rid = await ravi_id(client, hr)
    b = (await client.get(f"{P}/patients/{rid}/fhir", headers=hr)).json()
    types = {e["resource"]["resourceType"] for e in b["entry"]}
    assert b["resourceType"] == "Bundle" and {"Patient", "MedicationStatement", "Observation"} <= types


async def test_assistant_guardrails_over_http(client, auth):
    h, _ = await auth(client, "ravi@demo.test")
    r = (await client.post(f"{P}/assistant/ask", headers=h, json={"text": "Which antibiotic should I take?"})).json()
    assert r["blocked"] and r["category"] == "prescription_request"
    r = (await client.post(f"{P}/assistant/ask", headers=h, json={"text": "I want to end my life", "lang": "ta"})).json()
    assert r["blocked"] and r["crisis_resources"][0]["phone"] == "14416"
    r = (await client.post(f"{P}/assistant/ask", headers=h, json={"text": "How do I check my pressure?"})).json()
    assert not r["blocked"] and r["disclaimer"]


async def test_literacy_screening_cost_antibiotic(client, auth):
    h, _ = await auth(client, "ravi@demo.test")
    rid = await ravi_id(client, h)
    r = (await client.post(f"{P}/literacy/simplify", headers=h, json={"text": "Patient has hypertension and hyperglycemia. HbA1c elevated."})).json()
    assert "high blood pressure" in r["text"] and r["text"].startswith("Your report says") and not r["blocked"]
    sc = await client.post(f"{P}/patients/{rid}/screenings", headers=h, json={"instrument": "phq9", "answers": [0, 0, 0, 0, 0, 0, 0, 0, 2]})
    assert sc.json()["escalate"] and sc.json()["is_diagnosis"] is False and sc.json()["crisis_resources"]
    assert (await client.post(f"{P}/patients/{rid}/screenings", headers=h, json={"instrument": "phq9", "answers": [1]})).status_code == 422
    c = (await client.get(f"{P}/cost/compare", headers=h, params={"name": "Telma 40"})).json()
    assert c["found"] and "DEMO" in c["data"]["label"] and "pharmacist" in c["confirm"]
    assert (await client.get(f"{P}/cost/compare", headers=h, params={"name": "zzzz"})).json()["found"] is False
    assert (await client.get(f"{P}/antibiotic/education", headers=h)).status_code == 200
    a = (await client.get(f"{P}/patients/{rid}/antibiotics", headers=h)).json()
    assert a["courses"] == [] and any("Do not start, stop or change" in e for e in a["education"])
    o = (await client.post(f"{P}/medguard/ocr-text", headers=h, json={"text": "Glycomet 500\nTelma 40"})).json()
    assert o["requires_confirmation"] and len(o["candidates"]) == 2


async def test_erasure(client, auth):
    await client.post(f"{P}/auth/register", json={"email": "gone@y.com", "name": "Gone", "password": "longenough123", "role": "patient"})
    h, _ = await auth(client, "gone@y.com", "longenough123")
    gid = (await client.get(f"{P}/me", headers=h)).json()["id"]
    await client.post(f"{P}/patients/{gid}/measurements", headers=h, json={"kind": "weight", "v1": 70})
    assert (await client.delete(f"{P}/me", headers=h)).status_code == 204
    assert (await client.get(f"{P}/me", headers=h)).status_code == 401
