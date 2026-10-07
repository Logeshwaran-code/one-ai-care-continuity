# Assumptions
1. Prototype scope: one working vertical slice > many shallow features. Demo values and synthetic data throughout.
2. Seed drug KB is small, hand-written from general drug-labeling knowledge, and unreviewed by clinicians; every alert says so.
3. Thresholds (BP 160/100 watch, 180/120 urgent; glucose <70/<54, >=250/>=300 mg/dL) are common general cut-offs, configurable in `Thresholds`, and must be set by a clinician per patient.
4. "Pharmacist/Health worker" is one role (`health_worker`). Doctors and workers see only data patients consent to; admins never see PHI.
5. A prescription is a doctor's recorded decision; MedGuard warns and requires acknowledgement but does not forbid it.
6. SQLite is used for tests/dev, PostgreSQL in compose. The PostgreSQL path was not run in the build sandbox.
7. Frontend is a dependency-free PWA instead of Next.js to keep it runnable with no build step; porting to Next.js/Tailwind is straightforward because all logic is in the API.
8. Offline LLM mock gives deterministic glossary-based simplification; real translation/simplification needs an LLM provider.
9. Voice uses the browser Web Speech API (quality and Tamil/Hindi support vary by browser/OS).
10. Hindi/Tamil UI strings were written by an AI and need native-speaker review. PHQ-9/GAD-7 items are English only (validated translations must be sourced).
11. Date/time handling is naive-UTC; time zone display is not handled.
