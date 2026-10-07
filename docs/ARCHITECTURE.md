# Architecture

```mermaid
flowchart LR
  subgraph Client[PWA - en/ta/hi, voice, offline queue]
    UI[Role dashboards]
  end
  UI -->|HTTPS JWT| API[FastAPI async]
  API --> MW[Middleware: rate limit, security headers, metrics]
  API --> AUTH[Auth + RBAC + Consent + Audit]
  API --> MG[MedGuard engine]
  API --> CL[CareLoop engine]
  API --> GR[Guardrail pipeline]
  GR --> LLM[LLM gateway: mock / OpenAI-compatible]
  MG --> KB[(Seed drug KB JSON)]
  AUTH --> DB[(PostgreSQL / SQLite dev)]
  CL --> DB
  API -->|/metrics| PROM[Prometheus]
```

## Request path for any AI call
```mermaid
sequenceDiagram
  participant U as User
  participant G as Guardrails
  participant L as LLM gateway
  U->>G: free text
  G->>G: classify_input (self-harm / emergency / prescription / diagnosis)
  alt unsafe input
    G-->>U: fixed refusal/escalation template (model never called)
  else ok
    G->>L: render versioned prompt, cache, retry, timeout
    L-->>G: text (JSON-schema validated if structured)
    G->>G: validate_output (no dosing, stop, drug choice, diagnosis)
    G-->>U: text + disclaimer (or safe fallback)
  end
```

## Data model (ERD)
```mermaid
erDiagram
  USER ||--o| PATIENT_PROFILE : has
  USER ||--o{ CONSENT : "grants (patient) / receives (grantee)"
  USER ||--o{ MEDICATION : takes
  MEDICATION ||--o{ DOSE_LOG : logs
  USER ||--o{ MEASUREMENT : records
  USER ||--o{ APPOINTMENT : attends
  USER ||--o{ TASK : "subject of"
  USER ||--o{ SCREENING : completes
  USER ||--o{ VISIT_SUMMARY : "summarised in"
  USER ||--o{ REFRESH_TOKEN : sessions
  USER ||--o{ AUDIT_LOG : "actor/patient"
```
PHI text columns (allergies, conditions, dose text, notes, screening answers, summaries) use `EncryptedText` (Fernet). Numeric measurements stay queryable.

## Key decisions
- **Engines are pure functions** (`medguard/engine.py`, `careloop/engine.py`) so they are unit/golden tested without DB or network.
- **Every generated string goes through `ensure_safe`/`validate_output`**, including MedGuard explanations and CareLoop flags.
- **Consent model**: patient grants scopes (`medications, measurements, adherence, appointments, summary, screening`) per grantee; every access, allowed or denied, is audited; admins never read PHI.
- **LLM optional**: default offline `mock` provider is deterministic; swap via `LLM_PROVIDER=openai_compat` (OpenAI, vLLM, Ollama...).
- **Drug-knowledge ingestion design** (not implemented as code): RxNorm/openFDA/ATC loaders write to `ingredients/products/interactions` with `source`, `licence`, `retrieved_at`, `reviewed_by`; only `reviewed=true` rows may be shown as non-"unreviewed"; Indian brand maps come from licensed sources.
- **Interoperability**: `GET /patients/{id}/fhir` exports a FHIR R4 Bundle (Patient, MedicationStatement, Observation with LOINC). ABDM integration is out of scope.
