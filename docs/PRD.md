# Phase 0: PRD summary, personas, journeys, risks

## Problem
Chronic-care patients in India (diabetes + hypertension, often elderly) lose continuity between visits: duplicate/interacting medicines from multiple prescribers, missed doses, unrecorded BP/sugar, caregivers without visibility, and clinicians without a concise picture at the visit.

## Product
One backend/database/design system with seven working modules (MedGuard, CareLoop, Health Literacy, Elder Support, Antibiotic Safety, Mental Well-being, Cost Help) and two scaffolds (Clinician Copilot, workflow engine). Core principle: AI assists, humans decide.

## Personas
- **Ravi, 62** - diabetes + hypertension, 4 medicines, Tamil speaker, low tech confidence. Needs voice, big buttons, simple language.
- **Priya, 34** - Ravi's daughter, works in another city. Needs reassurance status (taken? BP recorded? appointment?) without seeing everything.
- **Anita, community pharmacist/health worker** - needs a prioritised follow-up list, not noise.
- **Dr. Meera** - 6 minutes per patient. Needs trends, adherence, flags with reasons, and suggested questions; must stay the decision maker.
- **Admin** - manages accounts and audit; has no access to health data.

## Journeys (demo)
1. Doctor adds a medicine -> MedGuard shows duplicate/interaction/allergy alert with source -> doctor decides (acknowledges) -> task to pharmacist.
2. Ravi logs by voice and records BP/sugar (works offline) -> CareLoop explains any flag.
3. Priya opens the family dashboard (only what Ravi consented to).
4. Anita completes the follow-up task.
5. Doctor opens an AI-drafted summary (marked DRAFT), edits/reviews, approves, downloads PDF.

## Risk register
| Id | Risk | Type | Mitigation | Residual |
|----|------|------|-----------|----------|
| R1 | Model/rule gives dosing, stop, or drug-choice advice | Clinical | Input classifier + output validator + fixed templates + red-team tests | Regex can miss novel phrasing; needs ongoing red-teaming |
| R2 | Emergency/self-harm handled by software | Clinical | Immediate fixed escalation (112, Tele-MANAS 14416), no model call | Multilingual coverage is keyword-based |
| R3 | Wrong brand->generic or interaction data | Clinical | Seed labelled, every alert has source+confidence+"unreviewed", user must confirm names, no auto-save from OCR | Production needs licensed, clinician-reviewed KB |
| R4 | Alert fatigue / false alarms | Clinical | Severity levels, explainable rules, personal baselines | Thresholds need clinician tuning |
| R5 | Missed interactions give false reassurance | Clinical | UI states the list is incomplete and to ask pharmacist | Inherent to a seed KB |
| R6 | PHI leak / over-sharing | Technical | Consent scopes, data minimisation, audit, field encryption, admin has no PHI | Key management is deployment-specific |
| R7 | Token theft | Technical | 15-min access tokens, rotating refresh with reuse detection | No device binding/MFA yet |
| R8 | LLM outage/latency | Technical | Timeouts, retries, caching, deterministic fallback | - |
| R9 | Mistranslation | Clinical | Fixed reviewed phrases only in offline mode; LLM translation flagged for review | Native-speaker review needed |
| R10 | Over-reliance on AI | Clinical | DRAFT labelling, doctor-only approval | Human factors need study |
