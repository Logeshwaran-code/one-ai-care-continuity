# Testing
| Layer | Where | Run |
|---|---|---|
| Interaction-engine golden tests | `tests/test_medguard.py`, `eval/golden_interactions.json` | `make test` |
| CareLoop unit tests (stats, thresholds, adherence) | `tests/test_careloop.py` | `make test` |
| Guardrail + red-team + PHQ-9/GAD-7 | `tests/test_guardrails.py`, `eval/redteam.json` | `make test` |
| API contract + RBAC + consent + audit + full demo flow | `tests/test_api.py` | `make test` |
| AI evaluation metrics | `eval/run_eval.py` | `make eval` |
| Browser E2E (Playwright) | `e2e/demo.spec.ts` | `make e2e` (needs running stack) |
Coverage gate: >=80% on `app` excluding seed/bootstrap/main (`make cov`). Measured at build: 96% across the gated core modules (OCR provider 76%, because the Tesseract image path needs the binary).
Note: the Playwright specs and frontend component tests were not executed in the build environment (no browser); the frontend has a syntax check only. See CHECKLIST.md.
