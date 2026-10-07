"""Demo data: Ravi (62, diabetes + hypertension), daughter Priya (caregiver), Dr. Meera, health worker Anita, admin.
All data is SYNTHETIC. Safe to run repeatedly."""
import asyncio
import json
import random
from datetime import date, timedelta

from sqlalchemy import select

from app.db import SessionLocal, init_db
from app.models import Appointment, Consent, DoseLog, Measurement, Medication, PatientProfile, User, utcnow
from app.security import hash_password

PASSWORD = "Demo@12345"
USERS = [("admin@demo.test", "Admin Asha", "admin"), ("doctor@demo.test", "Dr. Meera", "doctor"), ("worker@demo.test", "Anita (Pharmacist)", "health_worker"),
         ("ravi@demo.test", "Ravi", "patient"), ("priya@demo.test", "Priya (Ravi's daughter)", "family")]


async def seed() -> None:
    await init_db()
    async with SessionLocal() as s:
        existing = await s.scalar(select(User).where(User.email == "ravi@demo.test"))

        if existing:
            users = {u.email: u for u in (await s.scalars(select(User).where(User.email.in_([email for email, _, _ in USERS])))).all()}
            for demo_user in users.values():
                demo_user.password_hash = hash_password(PASSWORD)
            patient = users.get("ravi@demo.test")
            if patient:
                required_consents = {
                    "priya@demo.test": ["adherence", "measurements", "appointments"],
                    "doctor@demo.test": ["medications", "measurements", "adherence", "appointments", "summary"],
                    "worker@demo.test": ["medications", "measurements", "adherence", "appointments"],
                }
                for email, scopes in required_consents.items():
                    grantee = users.get(email)
                    if grantee:
                        consent = await s.scalar(select(Consent).where(Consent.patient_id == patient.id, Consent.grantee_id == grantee.id))
                        if consent is None or consent.revoked_at is not None:
                            s.add(Consent(patient_id=patient.id, grantee_id=grantee.id, scopes=scopes))
            await s.commit()
            return
        ids: dict[str, int] = {}
        for email, name, role in USERS:
            u = User(email=email, name=name, role=role, password_hash=hash_password(PASSWORD), language="ta" if role == "patient" else "en")
            s.add(u)
            await s.flush()
            ids[email] = u.id
        rid = ids["ravi@demo.test"]
        s.add(PatientProfile(user_id=rid, birth_year=1964, allergies_enc=json.dumps(["penicillin"]), conditions_enc=json.dumps(["type 2 diabetes", "hypertension"])))
        today = date.today()
        specs = [("Glycomet 500", "500 mg", ["morning", "night"]), ("Amaryl 1", "1 mg", ["morning"]), ("Telma 40", "40 mg", ["morning"]), ("Stamlo 5", "5 mg", ["morning"])]
        meds = []
        for name, dose, timing in specs:
            from app.medguard.engine import get_kb
            res = get_kb().resolve(name)
            m = Medication(patient_id=rid, prescriber_id=ids["doctor@demo.test"], raw_name=name, product_key=res.product_key, generic_name=res.generic_name,
                           dose_text=dose, timing=timing, start_date=today - timedelta(days=60), confirmed=True)
            s.add(m)
            meds.append(m)
        await s.flush()
        rnd = random.Random(42)
        now = utcnow()
        for d in range(30, -1, -1):
            day = now - timedelta(days=d)
            drift = 12 if d <= 3 else 0  # synthetic recent rise to trigger a baseline-shift flag
            s.add(Measurement(patient_id=rid, kind="bp", v1=round(rnd.gauss(134, 3) + drift), v2=round(rnd.gauss(84, 2) + drift / 3), measured_at=day.replace(hour=8, minute=0), source="manual"))
            s.add(Measurement(patient_id=rid, kind="glucose", v1=round(rnd.gauss(142, 18)), measured_at=day.replace(hour=7, minute=30)))
            if d % 7 == 0:
                s.add(Measurement(patient_id=rid, kind="weight", v1=round(78 + rnd.gauss(0, 0.4), 1), measured_at=day.replace(hour=7, minute=0)))
            for m in meds:
                for slot in m.timing:
                    if d == 0 and slot == "night":
                        continue
                    miss = d <= 4 and rnd.random() < 0.45  # recent adherence dip (synthetic)
                    if d == 0:
                        miss = True  # today starts with nothing logged
                    if not miss:
                        s.add(DoseLog(patient_id=rid, medication_id=m.id, day=today - timedelta(days=d), slot=slot))
        s.add(Appointment(patient_id=rid, when=now + timedelta(days=5), with_name="Dr. Meera"))
        s.add(Consent(patient_id=rid, grantee_id=ids["priya@demo.test"], scopes=["adherence", "measurements", "appointments"]))
        s.add(Consent(patient_id=rid, grantee_id=ids["doctor@demo.test"], scopes=["medications", "measurements", "adherence", "appointments", "summary"]))
        s.add(Consent(patient_id=rid, grantee_id=ids["worker@demo.test"], scopes=["medications", "measurements", "adherence", "appointments"]))
        await s.commit()


if __name__ == "__main__":
    asyncio.run(seed())
