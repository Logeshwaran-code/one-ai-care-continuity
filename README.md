# ONE AI Healthcare Continuity Platform

> **AI assists. Humans decide.** The platform detects, summarises, reminds, explains and flags. It never diagnoses, prescribes, or recommends/changes a medicine. This is enforced in code (see `SAFETY_AND_GUARDRAILS.md`).

**Status: working prototype / innovation-day demo. Not a medical device. Not for clinical use** (see `LIMITATIONS.md`).

## Run it in under 5 minutes
```bash
docker compose up --build        # Postgres + API + web app + Prometheus
# open http://localhost:8000   (API docs: http://localhost:8000/docs, metrics: :8000/metrics, Prometheus: :9090)
```
No Docker? Create a virtual environment, install `backend/requirements.txt`, then run `python -m app.bootstrap` and `uvicorn app.main:app` from `backend` (SQLite, serves the web app at `/`). The local default disables OCR so no native system package is required; set `OCR_PROVIDER=tesseract` only after installing Tesseract and configuring its executable on your machine.

On Windows, after installing dependencies, run `.\run.ps1` from the project root. It bootstraps the local database, seeds the demo accounts, and starts the complete app at `http://127.0.0.1:8000`.

Demo logins (password `Demo@12345`): `ravi@demo.test` (patient), `priya@demo.test` (family caregiver), `doctor@demo.test`, `worker@demo.test` (pharmacist/health worker), `admin@demo.test`.
Scripted walkthrough: `python scripts/demo_walkthrough.py http://localhost:8000` (needs `pip install httpx`).

For development checks, install `backend/requirements-dev.txt` as well. Run tests from either the repository root (`python -m pytest`) or `backend` (`python -m pytest`); both commands execute the full async suite.

## Develop
`make test` · `make cov` (>=80% gate on core) · `make eval` (AI safety + interaction metrics) · `make types` · `make lint` · `make e2e` (Playwright; needs Node).

## Layout
```
backend/app/guardrails.py      input classifier, output validator, refusals, disclaimers
backend/app/llm.py             provider-agnostic gateway (mock | openai_compat), versioned prompts in app/prompts
backend/app/medguard/          knowledge base + normaliser + duplicate/interaction/allergy engine + pluggable OCR
backend/app/careloop/          baselines, trends, adherence, explainable flags, visit summary + PDF
backend/app/wellbeing.py       PHQ-9 / GAD-7 scoring     backend/app/antibiotic.py   course tracking + education
backend/app/cost.py            brand vs generic price help (demo values)   backend/app/scaffold/  future modules 8-9
backend/app/routers/           auth, patient-scoped API, tools      backend/eval/   golden + red-team sets and metrics harness
frontend/                      dependency-free PWA (en/ta/hi, voice, large-button mode, offline queue)
docs/ pitch/ scripts/ e2e/     documentation, pitch assets, demo script, Playwright specs
```
Read `CHECKLIST.md` first for an honest account of what is and is not done.
