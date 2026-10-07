# Limitations (read before any use)
- **Not a medical device; no clinical validation; do not use for real patients.**
- Drug data is a tiny SEED (18 ingredients, 9 interaction rules). A real deployment needs a licensed, clinician-reviewed knowledge base (e.g. licensed interaction database + current CDSCO/Indian brand data) and an ingestion pipeline for RxNorm/openFDA/WHO ATC (designed, not implemented).
- Cost data are ILLUSTRATIVE demo numbers; only a CSV importer for real price lists exists.
- Guardrails are rule/regex-based; paraphrases, code-mixing and other languages can slip through. Red-team sets are small.
- Not implemented: Next.js/Tailwind frontend, React Native, OTP/OAuth login, Redis, Celery/Arq jobs, pgvector RAG, OpenTelemetry tracing, LLM-based OCR cleanup, Tamil/Hindi OCR (Tesseract English only in image), reminder push notifications, key rotation, MFA.
- Not executed in the build environment: Docker/PostgreSQL stack, Playwright E2E, GitHub Actions, pre-commit, pip-audit/bandit, Lighthouse/WCAG audit, load benchmarks.
- Accessibility: built with WCAG 2.2 AA practices (labels, focus, 44px targets, contrast tokens, large mode, skip link, live regions) but not audited.
- Missed-dose logic derives from schedules at request time; no timezone handling; "taken" is self-reported.
- In-memory rate limiter and LLM cache are per-process.
