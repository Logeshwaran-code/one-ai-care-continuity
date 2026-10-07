"use strict";
const API = window.location.protocol === "file:" || window.location.port === "5500"
  ? `http://${window.location.hostname === "::1" ? "[::1]" : "127.0.0.1"}:8000/api/v1`
  : "/api/v1";
const T = {
  en: { login: "Log in", email: "Email", password: "Password", today: "Today's medicines", taken: "Taken", mark: "Mark taken", voice: "Speak: I took my morning medicine", bp: "Record blood pressure", sys: "Top number (systolic)", dia: "Bottom number (diastolic)", glu: "Record sugar (mg/dL)", save: "Save",
    insights: "Your health trends", addmed: "Add a medicine", check: "Check medicine", confirm: "Yes, this is my medicine", doctor: "Show your doctor", gen: "Create visit summary", pdf: "Download PDF", approve: "Approve (doctor)", tasks: "Follow-up tasks", done: "Mark done",
    family: "Family dashboard", cost: "Medicine cost help", ask: "Ask a question", send: "Send", consent: "Who can see my data", revoke: "Revoke", listen: "Read aloud", screening: "Well-being check-in (PHQ-9)", submit: "Submit", audit: "Audit log", patients: "Patients", prescribe: "Prescribe (doctor decision)", ack: "Prescribe anyway (I have reviewed the alerts)" },
  ta: { login: "உள்நுழை", email: "மின்னஞ்சல்", password: "கடவுச்சொல்", today: "இன்றைய மருந்துகள்", taken: "எடுத்தாயிற்று", mark: "எடுத்தேன்", voice: "பேசுங்கள்: காலை மருந்து எடுத்தேன்", bp: "இரத்த அழுத்தம் பதிவு", sys: "மேல் எண்", dia: "கீழ் எண்", glu: "சர்க்கரை (mg/dL)", save: "சேமி",
    insights: "உங்கள் உடல்நலப் போக்குகள்", addmed: "மருந்து சேர்", check: "மருந்தைச் சரிபார்", confirm: "ஆம், இது என் மருந்து", doctor: "மருத்துவரிடம் காட்டுங்கள்", gen: "சுருக்கம் உருவாக்கு", pdf: "PDF பதிவிறக்கம்", approve: "அங்கீகரி (மருத்துவர்)", tasks: "தொடர் பணிகள்", done: "முடிந்தது",
    family: "குடும்ப நிலை", cost: "மருந்து விலை உதவி", ask: "கேள்வி கேளுங்கள்", send: "அனுப்பு", consent: "என் தரவை யார் பார்க்கலாம்", revoke: "திரும்பப்பெறு", listen: "படித்துக் காட்டு", screening: "மன நல பரிசோதனை (PHQ-9)", submit: "சமர்ப்பி", audit: "தணிக்கை பதிவு", patients: "நோயாளிகள்", prescribe: "பரிந்துரை (மருத்துவர் முடிவு)", ack: "மதிப்பாய்வு செய்தேன், தொடர்க" },
  hi: { login: "लॉग इन", email: "ईमेल", password: "पासवर्ड", today: "आज की दवाइयाँ", taken: "ली गई", mark: "ले ली", voice: "बोलें: मैंने सुबह की दवा ली", bp: "रक्तचाप दर्ज करें", sys: "ऊपर की संख्या", dia: "नीचे की संख्या", glu: "शुगर (mg/dL)", save: "सहेजें",
    insights: "आपकी सेहत के रुझान", addmed: "दवा जोड़ें", check: "दवा जाँचें", confirm: "हाँ, यह मेरी दवा है", doctor: "डॉक्टर को दिखाएँ", gen: "सारांश बनाएँ", pdf: "PDF डाउनलोड", approve: "मंज़ूर करें (डॉक्टर)", tasks: "फ़ॉलो-अप कार्य", done: "पूरा हुआ",
    family: "परिवार डैशबोर्ड", cost: "दवा की कीमत में मदद", ask: "सवाल पूछें", send: "भेजें", consent: "मेरा डेटा कौन देख सकता है", revoke: "वापस लें", listen: "पढ़कर सुनाएँ", screening: "मन की सेहत जाँच (PHQ-9)", submit: "जमा करें", audit: "ऑडिट लॉग", patients: "मरीज़", prescribe: "दवा लिखें (डॉक्टर का निर्णय)", ack: "समीक्षा कर ली, आगे बढ़ें" },
};
const VOICE_LANG = { en: "en-IN", ta: "ta-IN", hi: "hi-IN" };
let lang = localStorage.getItem("lang") || "en";
let session = JSON.parse(sessionStorage.getItem("session") || "null");
const t = (k) => (T[lang] && T[lang][k]) || T.en[k] || k;
const $ = (s) => document.querySelector(s);

function h(tag, props = {}, ...kids) {
  const el = document.createElement(tag);
  for (const [k, v] of Object.entries(props)) {
    if (k.startsWith("on")) el.addEventListener(k.slice(2), v); else if (v !== false && v != null) el.setAttribute(k, v === true ? "" : v);
  }
  for (const c of kids.flat()) el.append(c instanceof Node ? c : document.createTextNode(String(c)));
  return el;
}
const card = (title, ...kids) => h("section", { class: "card" }, h("h2", {}, title), ...kids);
const icon = (text) => h("span", { class: "icon-badge", "aria-hidden": "true" }, text);
const pageIntro = (eyebrow, title, description) => h("section", { class: "page-intro" },
  h("div", {}, h("p", { class: "eyebrow" }, eyebrow), h("h2", {}, title), h("p", { class: "intro-copy" }, description)),
  h("div", { class: "live-pill" }, h("span", { class: "live-dot" }), navigator.onLine ? "Connected" : "Offline"));
const stat = (label, value, detail, cls = "") => h("div", { class: "stat " + cls }, h("span", { class: "stat-label" }, label), h("strong", {}, value), h("small", {}, detail));

// ------------------------------------------------------------------ API + offline queue
async function api(path, opts = {}, retry = true) {
  const headers = { "Content-Type": "application/json", ...(session ? { Authorization: "Bearer " + session.access_token } : {}) };
  let r;
  try {
    r = await fetch(API + path, { ...opts, headers, signal: AbortSignal.timeout(15000) });
  } catch (error) {
    const e = new Error("Care server is not running. Start the project with run.ps1, then try again.");
    e.cause = error;
    throw e;
  }
  if (r.status === 401 && session && retry) {
    const rr = await fetch(API + "/auth/refresh", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ refresh_token: session.refresh_token }) });
    if (rr.ok) { session = await rr.json(); sessionStorage.setItem("session", JSON.stringify(session)); return api(path, opts, false); }
    logout();
  }
  const data = r.status === 204 ? null : await r.json().catch(() => null);
  if (!r.ok) { const e = new Error(typeof data?.detail === "string" ? data.detail : data?.detail?.message || "Error " + r.status); e.status = r.status; e.detail = data?.detail; throw e; }
  return data;
}
const queue = () => JSON.parse(localStorage.getItem("queue") || "[]");
async function queued(path, body) { // offline-first writes for measurements and dose logs
  try { return await api(path, { method: "POST", body: JSON.stringify(body) }); }
  catch (e) { if (e.status) throw e; localStorage.setItem("queue", JSON.stringify([...queue(), { path, body }])); return { queued: true }; }
}
async function flush() {
  const q = queue(); if (!q.length || !session) return; localStorage.setItem("queue", "[]");
  for (const it of q) { try { await api(it.path, { method: "POST", body: JSON.stringify(it.body) }); } catch (e) { if (!e.status) localStorage.setItem("queue", JSON.stringify([...queue(), it])); } }
}
function netState() { $("#offline").hidden = navigator.onLine; if (navigator.onLine) flush(); }
addEventListener("online", netState); addEventListener("offline", netState);

// ------------------------------------------------------------------ voice
function speak(text) { if (!("speechSynthesis" in window)) return; const u = new SpeechSynthesisUtterance(text); u.lang = VOICE_LANG[lang]; speechSynthesis.cancel(); speechSynthesis.speak(u); }
function listen(onText) {
  const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SR) { const v = prompt("Voice input is not supported in this browser. Type instead:"); if (v) onText(v); return; }
  const r = new SR(); r.lang = VOICE_LANG[lang]; r.onresult = (e) => onText(e.results[0][0].transcript); r.start();
}
const say = (text) => h("button", { class: "alt", "aria-label": t("listen"), onclick: () => speak(text) }, "🔊 " + t("listen"));
const note = (text, cls = "muted") => h("p", { class: cls, role: "status" }, text);

// ------------------------------------------------------------------ shared widgets
function alertsView(alerts) {
  return alerts.map((a) => h("div", { class: "alert sev-" + a.severity }, h("strong", {}, `${a.title} (${a.severity})`), h("p", {}, a.explanation), h("p", { class: "muted" }, `${a.escalation} Source: ${a.source}. Confidence: ${a.confidence}. Not clinician-reviewed.`)));
}
function flagsView(flags) {
  return flags.map((f) => h("div", { class: "flag " + f.severity }, h("strong", {}, f.title), h("p", {}, f.explanation), h("p", { class: "muted" }, "Rule: " + f.rule_id)));
}
async function insightsCard(pid) {
  const i = await api(`/patients/${pid}/careloop/insights`);
  const a = i.adherence;
  return h("section", { class: "card insights-card" },
    h("div", { class: "section-heading" }, h("span", {}, icon("↗"), h("strong", {}, t("insights"))), h("span", { class: "insight-badge" }, "PERSONAL BASELINE")),
    h("p", { class: "insight-lead" }, "Patterns from your recent readings, explained in plain language."),
    h("div", { class: "insight-summary" }, h("strong", {}, a.rate == null ? "—" : `${a.taken}/${a.expected}`), h("span", {}, "doses logged in the last 7 days")),
    ...(i.flags.length ? flagsView(i.flags) : [h("p", { class: "ok" }, "No flags right now.")]), note(i.threshold_note));
}
async function medAddCard(pid, prescribing) {
  const out = h("div"); const name = h("input", { id: "mn", placeholder: "e.g. Telma 40", "aria-label": t("addmed") });
  const timing = h("select", { "aria-label": "time" }, ...["morning", "afternoon", "evening", "night"].map((s) => h("option", { value: s }, s)));
  const doAdd = async (ack) => {
    out.replaceChildren();
    try { const r = await api(`/patients/${pid}/${prescribing ? "prescriptions" : "medications"}`, { method: "POST", body: JSON.stringify({ name: name.value, timing: [timing.value], confirmed: true, acknowledge_alerts: ack }) });
      out.append(note("Saved.", "ok"), ...alertsView(r.alerts)); }
    catch (e) { if (e.status === 409) { out.append(note(e.message, "muted"), ...alertsView(e.detail.alerts), h("button", { onclick: () => doAdd(true) }, t("ack"))); } else out.append(note(e.message, "alert")); }
  };
  const check = async () => { out.replaceChildren(); const r = await api("/medguard/resolve", { method: "POST", body: JSON.stringify({ names: [name.value] }) }); const x = r.results[0];
    out.append(note(x.product_key ? `Possible match: ${x.generic_name} (confidence ${x.confidence}). Please confirm.` : "Not recognised. Check the spelling or ask your pharmacist."));
    if (x.product_key) out.append(h("button", { onclick: () => doAdd(false) }, prescribing ? t("prescribe") : t("confirm"))); };
  return card(prescribing ? t("prescribe") : t("addmed"), name, timing, h("button", { onclick: check }, t("check")), out);
}
async function summaryCard(pid, canApprove) {
  const out = h("div");
  const show = async (r) => { const c = r.content; out.replaceChildren(h("p", {}, h("strong", {}, `Status: ${r.status}`), r.status === "draft" ? " (AI-assisted draft: clinician review required)" : ""), h("p", {}, c.narrative),
    ...(c.flags.length ? [h("h3", {}, "Flags"), ...flagsView(c.flags)] : []), ...(c.medication_alerts.length ? [h("h3", {}, "Medicine alerts"), ...alertsView(c.medication_alerts)] : []), h("h3", {}, "Suggested questions"), h("ul", {}, c.questions.map((q) => h("li", {}, q))),
    h("button", { class: "alt", onclick: async () => { const resp = await fetch(`${API}/summaries/${r.id}/pdf`, { headers: { Authorization: "Bearer " + session.access_token } }); window.open(URL.createObjectURL(await resp.blob())); } }, t("pdf")),
    ...(canApprove && r.status === "draft" ? [h("button", { onclick: async () => { await api(`/summaries/${r.id}/approve`, { method: "POST" }); show(await api(`/summaries/${r.id}`)); } }, t("approve"))] : [])); };
  return card(t("doctor"), h("button", { onclick: async () => show(await api(`/patients/${pid}/summary`, { method: "POST" })) }, t("gen")), out);
}

// ------------------------------------------------------------------ role views
async function patientView(main) {
  const pid = session.user_id; const today = await api(`/patients/${pid}/today`);
  const completed = today.doses.filter((d) => d.taken).length;
  const total = today.doses.length;
  const list = h("div", {}, today.doses.map((d) => h("div", { class: "dose" }, h("span", {}, `${d.name} ${d.dose || ""} - ${d.slot}`),
    d.taken ? h("span", { class: "ok" }, "✔ " + t("taken")) : h("button", { onclick: async () => { await queued(`/patients/${pid}/doses`, { medication_id: d.medication_id, slot: d.slot }); route(); } }, t("mark")))));
  const voiceOut = h("p", { role: "status" });
  const sys = h("input", { type: "number", "aria-label": t("sys") }), dia = h("input", { type: "number", "aria-label": t("dia") }), glu = h("input", { type: "number", "aria-label": t("glu") });
  main.append(pageIntro("YOUR CARE OVERVIEW", "Good to see you, Ravi", "Keep your care routine simple. Record what matters and bring questions to your care team."),
    h("div", { class: "stats-grid" }, stat("Today's progress", `${completed}/${total}`, completed === total ? "All doses recorded" : "Doses recorded", "accent"), stat("Care plan", "On track", "Based on recent entries", "positive"), stat("Next step", "Record", "Your next reading", "soft")),
    h("div", { class: "content-grid" },
      card(t("today"), h("div", { class: "section-heading" }, h("span", {}, icon("✓"), "Medicine schedule"), h("span", { class: "progress-label" }, `${completed}/${total}`)), list, h("button", { class: "voice-action", onclick: () => listen(async (txt) => { const r = await api(`/patients/${pid}/voice-log`, { method: "POST", body: JSON.stringify({ text: txt }) }); voiceOut.textContent = r.reply; speak(r.reply); route(); }) }, "🎤 " + t("voice")), voiceOut),
      card("Quick record", h("p", { class: "muted" }, "Add a reading in a few seconds. Your care team can see it with your consent."),
        h("div", { class: "metric-form" }, h("label", {}, t("sys"), sys), h("label", {}, t("dia"), dia), h("button", { onclick: async () => { await queued(`/patients/${pid}/measurements`, { kind: "bp", v1: +sys.value, v2: +dia.value }); route(); } }, t("save"))),
        h("div", { class: "metric-form single" }, h("label", {}, t("glu"), glu), h("button", { onclick: async () => { await queued(`/patients/${pid}/measurements`, { kind: "glucose", v1: +glu.value }); route(); } }, t("save"))))),
    await insightsCard(pid),
    await medAddCard(pid, false), await summaryCard(pid, false),
    h("section", { class: "care-tools" }, h("h2", {}, "More care tools"), h("p", { class: "muted" }, "Use these whenever you have time. Nothing here replaces a clinician."), await extras(pid)));
}
async function extras(pid) {
  const out = h("div", { class: "answer-panel", role: "status" }), q = h("textarea", { "aria-label": t("ask"), placeholder: lang === "ta" ? "உங்கள் கேள்வியை இங்கே தட்டச்சு செய்யுங்கள்..." : lang === "hi" ? "अपना सवाल यहाँ लिखें..." : "Type your question here...", rows: "3", maxlength: "2000" }), cn = h("input", { placeholder: "Telma 40", "aria-label": t("cost") }), costOut = h("div");
  const examples = {
    en: ["What is blood pressure?", "How can I prepare for my doctor visit?", "What should I record with my blood sugar?"],
    ta: ["இரத்த அழுத்தம் என்றால் என்ன?", "மருத்துவர் சந்திப்புக்கு எப்படி தயாராகலாம்?", "சர்க்கரை அளவை எப்போது பதிவு செய்ய வேண்டும்?"],
    hi: ["ब्लड प्रेशर क्या है?", "डॉक्टर से मिलने की तैयारी कैसे करें?", "ब्लड शुगर के साथ क्या लिखना चाहिए?"],
  }[lang] || [];
  const exampleButtons = h("div", { class: "question-chips", "aria-label": "Example questions" }, ...examples.map((example) => h("button", { type: "button", class: "chip", onclick: () => { q.value = example; q.focus(); } }, example)));
  const count = h("span", { class: "character-count" }, "0/2000");
  q.addEventListener("input", () => { count.textContent = `${q.value.length}/2000`; });
  const featureList = h("ul", { class: "ask-features" },
    h("li", {}, "Type any question in your own words"),
    h("li", {}, "Answers follow your selected language"),
    h("li", {}, "Ask about health terms, readings, medicines, or visits"),
    h("li", {}, "Safety checks protect against urgent or unsafe advice"));
  const consents = await api("/consents");
  const phq = h("div", { class: "questionnaire" }); const answers = Array(9).fill(0); const items = (await api("/wellbeing/instruments/phq9"));
  const progress = h("div", { class: "question-progress" }, "Question 1 of 9");
  items.items.forEach((it, i) => {
    const select = h("select", { "aria-label": `Question ${i + 1}`, onchange: (e) => {
      answers[i] = +e.target.value;
      progress.textContent = `Question ${Math.min(i + 2, items.items.length)} of ${items.items.length}`;
    } }, items.options.map((o, v) => h("option", { value: v }, o)));
    phq.append(h("fieldset", { class: "question-row" }, h("legend", {}, h("span", { class: "question-number" }, String(i + 1).padStart(2, "0")), it), select));
  });
  const phqOut = h("div");
  return h("div", {},
    h("section", { class: "card ask-card" }, h("div", { class: "section-heading" }, h("span", {}, icon("✦"), h("strong", {}, t("ask"))), h("span", { class: "insight-badge" }, "AI + MANUAL INPUT")), h("p", { class: "muted" }, lang === "ta" ? "எந்த கேள்வியையும் தட்டச்சு செய்யுங்கள். உங்கள் மொழியில் எளிய பதில் கிடைக்கும்." : lang === "hi" ? "कोई भी सवाल लिखें। आपको अपनी भाषा में सरल उत्तर मिलेगा।" : "Type any question in your own words. You will receive a simple answer in your selected language."), featureList, exampleButtons, h("form", { class: "ask-form", onsubmit: async (e) => { e.preventDefault(); if (!q.value.trim()) { out.replaceChildren(note(lang === "ta" ? "முதலில் ஒரு கேள்வியை எழுதுங்கள்." : lang === "hi" ? "पहले अपना सवाल लिखें।" : "Type a question first.", "alert")); return; } out.replaceChildren(note(lang === "ta" ? "பாதுகாப்பான பதிலை உருவாக்குகிறது..." : lang === "hi" ? "सुरक्षित उत्तर तैयार हो रहा है..." : "Preparing a safe answer...", "muted")); try { const r = await api("/assistant/ask", { method: "POST", body: JSON.stringify({ text: q.value.trim(), lang }) }); out.replaceChildren(h("p", { class: "answer-text" }, r.text), say(r.text), note(r.disclaimer), ...(r.crisis_resources || []).map((c) => h("p", {}, `${c.name}: ${c.phone}`))); } catch (err) { out.replaceChildren(note(err.message, "alert")); } } }, q, h("div", { class: "ask-actions" }, count, h("button", { type: "submit" }, t("send")))), out),
    card(t("cost"), cn, h("button", { onclick: async () => { const r = await api("/cost/compare?name=" + encodeURIComponent(cn.value)); costOut.replaceChildren(note(`${r.data.label} - source: ${r.data.source}, as of ${r.data.as_of}`, "alert"), h("p", {}, r.found ? `Brand ₹${r.brand_price_inr} vs possible generic ₹${r.generic_price_inr} (${r.pack})` : r.message), note(r.confirm)); } }, t("check")), costOut),
    h("section", { class: "card screening-card" },
      h("div", { class: "section-heading" }, h("span", {}, icon("♡"), h("strong", {}, t("screening"))), h("span", { class: "insight-badge" }, "9 QUESTIONS")),
      h("p", { class: "muted" }, "Answer one question at a time. This is a screening tool, not a diagnosis."),
      progress, phq,
      h("button", { class: "primary-wide", onclick: async () => { const r = await api(`/patients/${pid}/screenings`, { method: "POST", body: JSON.stringify({ instrument: "phq9", answers }) }); phqOut.replaceChildren(h("p", {}, r.message), ...r.crisis_resources.map((c) => h("p", {}, `${c.name}: ${c.phone}`))); } }, t("submit")), phqOut),
    card(t("consent"), ...consents.map((c) => h("div", { class: "row" }, h("span", {}, `${c.name} (${c.role}): ${c.scopes.join(", ")}`), h("button", { class: "alt", onclick: async () => { await api("/consents/" + c.id, { method: "DELETE" }); route(); } }, t("revoke")))))
  );
}
async function familyView(main) {
  const ps = await api("/patients");
  for (const p of ps) { const d = await api(`/patients/${p.id}/family-dashboard`);
    main.append(card(`${t("family")}: ${d.patient}`, ...(d.medicine_taken_today ? [h("p", {}, `Medicine taken today: ${d.medicine_taken_today.taken} of ${d.medicine_taken_today.scheduled}`)] : []),
      ...("bp_recorded_today" in d ? [h("p", {}, `BP recorded today: ${d.bp_recorded_today ? "Yes" : "No"}`)] : []), ...("next_appointment" in d ? [h("p", {}, d.next_appointment ? `Next appointment: ${new Date(d.next_appointment.when).toLocaleString()} with ${d.next_appointment.with}` : "No appointment scheduled")] : []), note("Shown with the patient's consent. They can change this any time."))); }
}
async function workerView(main) {
  const tasks = await api("/tasks");
  main.append(card(t("tasks"), ...(tasks.length ? tasks.map((k) => h("div", { class: "alert" }, h("strong", {}, `${k.patient}: ${k.title}`), h("p", {}, k.detail || ""), h("button", { onclick: async () => { await api(`/tasks/${k.id}/complete`, { method: "POST" }); route(); } }, t("done")))) : [h("p", {}, "No open tasks.")])));
  for (const p of await api("/patients")) { const r = await api(`/patients/${p.id}/medguard/report`); main.append(card(`${p.name}: MedGuard`, ...(r.alerts.length ? alertsView(r.alerts) : [h("p", { class: "ok" }, "No alerts")]), note(r.kb.warning))); }
}
async function doctorView(main) {
  for (const p of await api("/patients")) { const r = await api(`/patients/${p.id}/medguard/report`);
    main.append(h("h2", {}, `${t("patients")}: ${p.name}`), card("MedGuard", ...(r.alerts.length ? alertsView(r.alerts) : [h("p", { class: "ok" }, "No alerts")]), note(r.kb.warning)), await insightsCard(p.id), await medAddCard(p.id, true), await summaryCard(p.id, true)); }
}
async function adminView(main) {
  const rows = await api("/admin/audit?limit=50");
  main.append(card(t("audit"), h("table", {}, h("tr", {}, ["time", "actor", "role", "patient", "action", "allowed"].map((x) => h("th", {}, x))), ...rows.map((r) => h("tr", {}, [r.at, r.actor_id, r.role, r.patient_id, r.action, r.allowed].map((x) => h("td", {}, x ?? "-")))))));
}
function loginView(main) {
  const em = h("input", { id: "em", type: "email", autocomplete: "username" }), pw = h("input", { id: "pw", type: "password", autocomplete: "current-password" }), err = h("p", { class: "alert", role: "alert" });
  const go = async (e, p) => {
    err.textContent = "";
    try {
      session = await api("/auth/login", { method: "POST", body: JSON.stringify({ email: e.trim(), password: p }) }, false);
      sessionStorage.setItem("session", JSON.stringify(session));
      await route();
    } catch (x) {
      err.textContent = x.message || "Unable to sign in. Check the server and try again.";
    }
  };
  const form = h("form", { onsubmit: (event) => { event.preventDefault(); return go(em.value, pw.value); } },
    h("label", { for: "em" }, t("email")), em, h("label", { for: "pw" }, t("password")), pw,
    h("button", { type: "submit" }, t("login")), err);
  const demos = [["ravi@demo.test", "Ravi · patient", "Ravi (patient)"], ["priya@demo.test", "Priya · family", "Priya (family)"], ["doctor@demo.test", "Dr. Meera · doctor", "Dr. Meera (doctor)"], ["worker@demo.test", "Anita · care team", "Anita (pharmacist)"], ["admin@demo.test", "Admin · operations", "Admin"]];
  main.append(h("div", { class: "login-layout" },
    h("section", { class: "login-hero" }, h("p", { class: "eyebrow" }, "ONE AI CARE CONTINUITY"), h("h2", {}, "A calmer way to stay on top of care."), h("p", {}, "One simple place for medicines, readings, questions, and care-team follow-up. Built to be clear for every family."),
      h("div", { class: "login-points" }, ...["Private by design", "Simple, accessible actions", "Human review always comes first"].map((x) => h("div", { class: "login-point" }, h("b", {}, "✓"), x)))),
    h("section", { class: "card login-card" }, h("h2", {}, t("login")), h("p", { class: "muted" }, "Use your account to continue securely."), form,
      h("div", { class: "demo-divider" }, "Quick demo access"), h("p", { class: "muted" }, "Demo password: Demo@12345"),       h("div", { class: "demo-list" }, ...demos.map(([e, n, accessibleName]) => h("button", { class: "alt", "aria-label": accessibleName, onclick: () => go(e, "Demo@12345") }, n))))));
}
const VIEWS = { patient: patientView, family: familyView, health_worker: workerView, doctor: doctorView, admin: adminView };
async function route() {
  const main = $("#main"); main.replaceChildren(); $("#logout").hidden = !session; $("#logout").textContent = "Log out";
  if (session) main.append(h("div", { class: "loading-state", role: "status" }, h("span", { class: "loader" }), "Loading your care space..."));
  try {
    if (!session) loginView(main);
    else if (VIEWS[session.role]) { main.replaceChildren(); await VIEWS[session.role](main); }
    else throw new Error("This account role is not supported by the current app.");
  } catch (e) { main.replaceChildren(note(e.message || "Something went wrong. Please try again.", "alert")); }
  main.focus();
}
function logout() { session = null; sessionStorage.removeItem("session"); route(); }
$("#logout").addEventListener("click", logout);
$("#theme").addEventListener("click", () => {
  const dark = document.body.classList.toggle("dark");
  localStorage.setItem("theme", dark ? "dark" : "light");
});
$("#lang").value = lang; document.documentElement.lang = lang;
$("#lang").addEventListener("change", (e) => { lang = e.target.value; localStorage.setItem("lang", lang); document.documentElement.lang = lang; route(); });
$("#big").addEventListener("click", (e) => { const on = document.body.classList.toggle("big"); e.target.setAttribute("aria-pressed", on); localStorage.setItem("big", on ? "1" : ""); });
if (localStorage.getItem("big")) { document.body.classList.add("big"); $("#big").setAttribute("aria-pressed", "true"); }
if (localStorage.getItem("theme") === "dark") {
  localStorage.removeItem("theme");
  document.body.classList.remove("dark");
}
if ("serviceWorker" in navigator) navigator.serviceWorker.register("/sw.js").catch(() => {});
netState(); route();
