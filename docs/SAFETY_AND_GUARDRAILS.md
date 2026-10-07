# Safety and guardrails
**Principle: AI assists. Humans decide.** Allowed: detect, summarise, remind, explain, translate, organise, flag, prepare. Forbidden: diagnose, prescribe, recommend/change/stop a medicine or antibiotic, replace a clinician, handle emergencies alone.

## Layers (all in code: `backend/app/guardrails.py`)
1. **Input classifier** - `self_harm`, `emergency`, `prescription_request` (which drug/dose/can I stop...), `diagnosis_request`. English plus Hindi/Tamil keywords. These return fixed, reviewed templates (112, Tele-MANAS 14416) and the model is never called.
2. **Output validator** - blocks dosing instructions, "stop/skip/double", dose changes, drug selection ("you should take", "I recommend"), diagnoses ("you have ..."), and discouraging care. Negations ("do not stop taking") are allowed so safety advice is not blocked.
3. **Runtime `ensure_safe`** on every MedGuard explanation and CareLoop message (non-LLM text is also checked, and tests assert it).
4. **Mandatory disclaimers** (en/ta/hi) on guarded responses; MedGuard alerts carry an escalation line.
5. **Human-in-the-loop** - OCR/typed names must be confirmed; major alerts return 409 until a clinician acknowledges; only a doctor can approve a summary (drafts are labelled DRAFT in app and PDF).
6. **Mental well-being** - PHQ-9/GAD-7 with standard scoring; non-diagnostic wording; item 9 > 0 always escalates; never "you have depression"; no therapist behaviour.
7. **Antibiotics** - tracks a clinician-prescribed course and educates; refuses selection requests.

## Testing
`tests/test_guardrails.py` + `eval/redteam.json` (18 unsafe prompts, 5 benign, 9 unsafe outputs, 5 safe outputs). `python -m eval.run_eval` reports refusal rate, false-block rate, golden interaction precision/recall, and uncited-alert count (CI-gated). **These metrics are on small hand-written sets; they do not prove real-world safety.** Regex guardrails are a floor, not a ceiling: add model-based classifiers and continuous red-teaming before any real use.
