# API
Interactive spec: `/docs` (Swagger) and `docs/openapi.json` (snapshot). Base path `/api/v1`. Bearer JWT. Errors: 401 unauthenticated, 403 role/consent, 409 needs human acknowledgement, 422 validation, 429 rate limit.

| Area | Endpoint | Who |
|---|---|---|
| Auth | `POST /auth/register` (patient/family), `/auth/login`, `/auth/refresh` (rotating), `GET /me` | all |
| Admin | `POST /admin/users`, `GET /admin/audit` | admin |
| Consent | `POST/GET /consents`, `DELETE /consents/{id}`, `GET /patients` | patient / grantees |
| MedGuard | `POST /medguard/resolve`, `/medguard/ocr-text`, `/medguard/ocr` (image), `GET /patients/{id}/medguard/report` | consented |
| Medicines | `GET/POST /patients/{id}/medications` (needs `confirmed=true`), `POST /patients/{id}/prescriptions` | doctor (prescribe) |
| CareLoop | `POST/GET /patients/{id}/measurements`, `POST /patients/{id}/doses`, `GET .../careloop/insights`, `GET .../today` | self / consented |
| Summary | `POST /patients/{id}/summary`, `GET /summaries/{id}`, `/summaries/{id}/pdf`, `POST /summaries/{id}/approve` | approve: doctor only |
| Elder | `POST /patients/{id}/voice-log`, `GET /patients/{id}/family-dashboard` | self / family w/ consent |
| Tasks | `GET /tasks`, `POST /tasks/{id}/complete` | doctor, health worker |
| Literacy | `POST /literacy/simplify` | all |
| Assistant | `POST /assistant/ask` (guardrail-wrapped) | all |
| Antibiotic | `GET /antibiotic/education`, `GET /patients/{id}/antibiotics` | consented |
| Well-being | `GET /wellbeing/instruments/{phq9\|gad7}`, `POST /patients/{id}/screenings` | self / consented |
| Cost | `GET /cost/compare?name=` | all |
| Data rights | `GET /patients/{id}/fhir`, `DELETE /me` | self / consented |
| Ops | `/health`, `/ready`, `/metrics` | public |

Contract tests live in `backend/tests/test_api.py`.
