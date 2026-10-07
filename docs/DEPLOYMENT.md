# Deployment
**Local/demo:** `docker compose up --build` (dev secrets, demo seed).
**Local Python:** install `backend/requirements.txt`, run `python -m app.bootstrap` from `backend`, then start `uvicorn app.main:app`. The `.env.example` default uses `OCR_PROVIDER=none`; enable Tesseract only when the native binary is installed.
**Production minimum:** set `ENV=prod`, strong `JWT_SECRET`, `PHI_ENCRYPTION_KEY` (Fernet key from a secrets manager), `SEED_DEMO=false`, managed PostgreSQL, TLS termination (reverse proxy), `LLM_PROVIDER` + keys if used, run Alembic migrations (`alembic upgrade head`), restrict `/metrics`, shared rate limiting (the built-in limiter is per-process), backups, log shipping. Scale API horizontally (stateless). Background work (reminder delivery, missed-dose materialisation) needs a worker (Arq/Celery) - not included.
**Health:** `/health`, `/ready`. **Metrics:** `/metrics` (HTTP latency/count, LLM latency/outcomes, guardrail decisions).
**Performance notes:** async I/O, indexed (patient, kind, time) queries, paginated lists, LLM response cache. Formal benchmarks were NOT run (see LIMITATIONS).
