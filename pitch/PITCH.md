# Innovation-day pitch assets

## 10-slide outline with speaker notes
1. **Title - "AI assists. Humans decide."** Continuity of care for India's chronic patients. *Notes:* One platform, four user groups, one rule.
2. **Problem.** 100M+ Indians live with diabetes; hypertension is more common still. Care breaks between visits: duplicate medicines from several doctors, missed doses, unrecorded readings, family in the dark. *Notes:* Use Ravi's story; avoid quoting statistics you cannot source on stage.
3. **Meet Ravi.** 62, diabetes + hypertension, 4 medicines, daughter Priya far away. *Notes:* Everyone in the room knows a Ravi.
4. **Solution.** MedGuard + CareLoop at the core; literacy, elder support, antibiotic safety, well-being, cost help around it. *Notes:* Core is deep; others are working and honest about depth.
5. **MedGuard.** Brand -> generic -> ingredient; duplicates, interactions, allergies; plain language, source, confidence, "confirm with your doctor". *Notes:* Show Telma + Losar flagged; never says "stop".
6. **CareLoop.** Personal baselines and trends; every flag shows its numbers and rule. *Notes:* Explainable on purpose - no black-box alerts.
7. **The team around the patient.** Daughter's minimal dashboard, pharmacist task, doctor's draft summary she approves. *Notes:* Consent controls what each person sees.
8. **Safety by design** (see slide below).
9. **Evidence & honesty.** 95 automated tests, red-team refusal 100% on our set, golden interaction precision/recall 100% on seed set. *Notes:* Say clearly: small seed sets; this is not clinical validation. Honesty builds trust.
10. **Ask & roadmap.** Licensed drug KB, clinician review panel, pilot with a health-worker network, ABDM integration, native-language validation. *Notes:* Ask for clinical advisors and a pilot site.

## "Safety by design" slide
**AI can:** detect - summarise - remind - explain - translate - flag.
**AI cannot (enforced in code):** diagnose - prescribe - pick/stop/change a medicine or antibiotic - handle emergencies.
**How:** input classifier -> fixed escalation (112, Tele-MANAS 14416) - output validator on every string - human acknowledgement for major alerts - doctor-only approval of drafts - consent + audit on every data access - red-team tests in CI.

## 3-minute demo script
- **0:00** "This is Ravi's phone, set to Tamil with large buttons." Log in as Ravi; tap the mic: "I took my morning medicine" -> doses tick.
- **0:30** Switch to Dr. Meera. MedGuard clean. She tries to add Losar 50. **Alert: two ARB medicines** with source and "confirm with pharmacist". "The AI warns; she decides." She acknowledges.
- **1:10** CareLoop panel: "Recent BP higher than usual: 151 vs 135, here is the rule." Adherence flag with reasons.
- **1:40** Priya's view: medicine taken 5 of 6, BP recorded, appointment in 5 days - nothing more. "Ravi can revoke this anytime."
- **2:00** Anita's task list: "Follow up: medicine alert for Losar 50."
- **2:15** Back to Dr. Meera: generate summary -> badge **DRAFT**, suggested questions, approve, PDF.
- **2:45** Ravi's assistant: "Which antibiotic should I take?" -> refusal. "I want to end my life" -> Tele-MANAS 14416. "Safety is code, not copy."

## One-page summary
**Problem:** Care for chronic conditions fails between visits - unsafe medicine combinations, missed doses, silent trends, disconnected families.
**Solution:** A multilingual (English/Tamil/Hindi), voice-first platform where AI prepares information and humans decide: MedGuard checks the medicine list; CareLoop tracks readings and adherence with explainable flags; family, pharmacist and doctor see exactly what the patient allows; doctors get a concise, reviewable summary.
**Impact (hypotheses to test in a pilot, not claims):** fewer unnoticed duplicate/interacting prescriptions; earlier follow-up when adherence or BP drifts; shorter, better-prepared consultations; more family involvement.
**Safety & privacy:** guardrails enforced in code, human approval, consent + audit, encrypted PHI, DPDP-aligned design.
**Status & ask:** working prototype on synthetic data. Need: licensed clinician-reviewed drug data, clinical advisors, pilot partner.
