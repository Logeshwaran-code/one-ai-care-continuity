# Final requirements checklist (honest)
Legend: DONE = implemented and tested here - PARTIAL = implemented in reduced form - NOT DONE.

## Principle & modules
| Requirement | Status | Notes |
|---|---|---|
| "AI assists, humans decide" enforced in code | DONE | `guardrails.py`, tests, red-team set, 409 acknowledgements, doctor-only approval |
| 1 MedGuard (normalise, duplicate, interaction, allergy, severity, sources, OCR w/ confirmation) | DONE (seed data) | KB is 18 ingredients / 9 rules, unreviewed; Tesseract OCR provider exists but was not run here (text path tested) |
| 2 CareLoop (BP/glucose/weight, adherence, baseline, trends, explainable flags, summary PDF + in-app) | DONE | PDF English only |
| 3 Health Literacy (simplify, levels, translate, TTS/STT) | PARTIAL | Offline glossary simplifier + fixed-phrase translation; full simplify/translate needs configured LLM; TTS/STT via browser |
| 4 Elder Support (voice, large buttons, voice logging, family dashboard) | DONE | Voice recognition depends on browser support |
| 5 Antibiotic Safety | DONE | Course tracking, education, refusal; never selects |
| 6 Mental Well-being (PHQ-9/GAD-7, escalation, crisis resources) | DONE (English items) | Validated Tamil/Hindi items not bundled |
| 7 Cost Help | PARTIAL | Demo values labelled; CSV importer for real lists |
| 8 Clinician Copilot, 9 workflow engine | SCAFFOLD (as requested) | `app/scaffold/` interfaces |
## Platform
| Requirement | Status | Notes |
|---|---|---|
| RBAC (5 roles), consent scopes, audit log | DONE | Admin has no PHI access |
| FastAPI async, SQLAlchemy 2, Alembic, PostgreSQL | DONE / UNVERIFIED | Postgres path not run in sandbox; SQLite verified incl. migration |
| Redis, Celery/Arq | NOT DONE | |
| Next.js + Tailwind | NOT DONE | Replaced by dependency-free PWA |
| PWA offline, i18n en/ta/hi, elder mode, WCAG 2.2 AA | PARTIAL | App shell cached, offline write queue, i18n core strings; not audited; translations need native review |
| React Native | NOT DONE | PWA installable instead |
| LLM gateway (provider-agnostic, versioned prompts, schema validation, cache, retry, timeout, cost/latency logs) | DONE | Mock + OpenAI-compatible; OpenAI-compat path untested against a live server |
| RAG with pgvector | NOT DONE | |
| Guardrails on every AI call, red-team suite | DONE | Rule-based; small set |
| Drug-data ingestion pipeline | NOT DONE (design documented) | Seed + price CSV loader only |
| JWT + refresh rotation | DONE | Reuse detection tested |
| OAuth/OTP login | NOT DONE | |
| Field-level PHI encryption, rate limiting, validation, OWASP, data export/delete, FHIR R4 export | DONE | Per-process rate limiter; no key rotation |
| DPDP alignment | PARTIAL | Design-level only |
| Logging, Prometheus, health | DONE | |
| OpenTelemetry | NOT DONE | |
| Docker/compose, Makefile, .env.example, seed + demo scripts | DONE (compose not run here) | |
| GitHub Actions, pre-commit | WRITTEN, NOT RUN | |
| Tests: unit, integration, contract, red-team, golden | DONE | 95 pass; 96% on core engines |
| Frontend component tests, Playwright E2E | WRITTEN (E2E), NOT RUN; no component tests | |
| Evaluation harness | DONE | Seed-set metrics only |
| Performance benchmarks | NOT DONE | Design choices documented only |
| Docs (README, ARCHITECTURE, API, SAFETY, PRIVACY, TESTING, DEPLOYMENT, ASSUMPTIONS, LIMITATIONS) + PRD | DONE | |
| Pitch assets | DONE | `pitch/PITCH.md` |
| Demo scenario end-to-end with seeded users | DONE | `scripts/demo_walkthrough.py` verified against a live server |
