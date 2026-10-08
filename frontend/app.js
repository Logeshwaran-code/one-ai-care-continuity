"use strict";
const API = window.location.protocol === "file:" || window.location.port === "5500"
  ? `http://${window.location.hostname === "::1" ? "[::1]" : "127.0.0.1"}:8000/api/v1`
  : "/api/v1";
const T = {
  en: { login: "Log in", email: "Email", password: "Password", today: "Today's medicines", taken: "Taken", mark: "Mark taken", voice: "Speak: I took my morning medicine", bp: "Record blood pressure", sys: "Top number (systolic)", dia: "Bottom number (diastolic)", glu: "Record sugar (mg/dL)", save: "Save",
    insights: "Your health trends", addmed: "Add a medicine", check: "Check medicine", confirm: "Yes, this is my medicine", doctor: "Show your doctor", gen: "Create visit summary", pdf: "Download PDF", approve: "Approve (doctor)", tasks: "Follow-up tasks", done: "Mark done", care: "Today's Care", medicines: "Medicines", healthCheck: "Health check", wellbeing: "Well-being", followup: "Follow-up",
    family: "Family dashboard", cost: "Medicine cost help", medicationSafety: "Medication Safety", safetyCheck: "Check safety", listReview: "Review my medication list", ask: "CareSync AI", askCompanion: "Your personal care companion", send: "Ask CareSync", consent: "Privacy & Care Sharing", share: "Share care access", revoke: "Revoke access", listen: "Read aloud", wellbeingCheck: "Well-being Check", screening: "Validated PHQ-9 screening", submit: "Submit", audit: "Audit log", patients: "Patients", prescribe: "Prescribe (doctor decision)", ack: "Prescribe anyway (I have reviewed the alerts)", careSummary: "Care Team Summary" },
  ta: { login: "உள்நுழை", email: "மின்னஞ்சல்", password: "கடவுச்சொல்", today: "இன்றைய மருந்துகள்", taken: "எடுத்தாயிற்று", mark: "எடுத்தேன்", voice: "பேசுங்கள்: காலை மருந்து எடுத்தேன்", bp: "இரத்த அழுத்தம் பதிவு", sys: "மேல் எண்", dia: "கீழ் எண்", glu: "சர்க்கரை (mg/dL)", save: "சேமி",
    insights: "உங்கள் உடல்நலப் போக்குகள்", addmed: "மருந்து சேர்", check: "மருந்தைச் சரிபார்", confirm: "ஆம், இது என் மருந்து", doctor: "மருத்துவரிடம் காட்டுங்கள்", gen: "சுருக்கம் உருவாக்கு", pdf: "PDF பதிவிறக்கம்", approve: "அங்கீகரி (மருத்துவர்)", tasks: "தொடர் பணிகள்", done: "முடிந்தது", care: "இன்றைய பராமரிப்பு", medicines: "மருந்துகள்", healthCheck: "உடல்நலச் சோதனை", wellbeing: "நல்வாழ்வு", followup: "தொடர்புப் பணி",
    family: "குடும்ப நிலை", cost: "மருந்து விலை உதவி", medicationSafety: "மருந்து பாதுகாப்பு", safetyCheck: "பாதுகாப்பைச் சரிபார்", listReview: "என் மருந்துப் பட்டியலைச் சரிபார்", ask: "CareSync AI", askCompanion: "உங்கள் தனிப்பட்ட பராமரிப்பு துணை", send: "CareSync-ஐ கேளுங்கள்", consent: "தனியுரிமை மற்றும் பராமரிப்பு பகிர்வு", share: "பராமரிப்பு அணுகலைப் பகிர்", revoke: "அணுகலைத் திரும்பப்பெறு", listen: "படித்துக் காட்டு", wellbeingCheck: "நல்வாழ்வு சோதனை", screening: "சரிபார்க்கப்பட்ட PHQ-9 பரிசோதனை", submit: "சமர்ப்பி", audit: "தணிக்கை பதிவு", patients: "நோயாளிகள்", prescribe: "பரிந்துரை (மருத்துவர் முடிவு)", ack: "மதிப்பாய்வு செய்தேன், தொடர்க", careSummary: "மருத்துவக் குழு சுருக்கம்" },
  hi: { login: "लॉग इन", email: "ईमेल", password: "पासवर्ड", today: "आज की दवाइयाँ", taken: "ली गई", mark: "ले ली", voice: "बोलें: मैंने सुबह की दवा ली", bp: "रक्तचाप दर्ज करें", sys: "ऊपर की संख्या", dia: "नीचे की संख्या", glu: "शुगर (mg/dL)", save: "सहेजें",
    insights: "आपकी सेहत के रुझान", addmed: "दवा जोड़ें", check: "दवा जाँचें", confirm: "हाँ, यह मेरी दवा है", doctor: "डॉक्टर को दिखाएँ", gen: "सारांश बनाएँ", pdf: "PDF डाउनलोड", approve: "मंज़ूर करें (डॉक्टर)", tasks: "फ़ॉलो-अप कार्य", done: "पूरा हुआ", care: "आज की देखभाल", medicines: "दवाइयाँ", healthCheck: "स्वास्थ्य जाँच", wellbeing: "मन की सेहत", followup: "फ़ॉलो-अप",
    family: "परिवार डैशबोर्ड", cost: "दवा की कीमत में मदद", medicationSafety: "दवा सुरक्षा", safetyCheck: "सुरक्षा जाँचें", listReview: "मेरी दवा सूची जाँचें", ask: "CareSync AI", askCompanion: "आपका व्यक्तिगत देखभाल साथी", send: "CareSync से पूछें", consent: "प्राइवेसी और देखभाल साझा करना", share: "देखभाल की पहुँच साझा करें", revoke: "पहुँच वापस लें", listen: "पढ़कर सुनाएँ", wellbeingCheck: "सेहत और मन की जाँच", screening: "मान्य PHQ-9 स्क्रीनिंग", submit: "जमा करें", audit: "ऑडिट लॉग", patients: "मरीज़", prescribe: "दवा लिखें (डॉक्टर का निर्णय)", ack: "समीक्षा कर ली, आगे बढ़ें", careSummary: "केयर टीम सारांश" },
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
const continuityStat = (label, value, detail, cls = "") => h("div", { class: "continuity-stat " + cls }, h("span", { class: "stat-label" }, label), h("strong", {}, value), h("small", {}, detail));

// ------------------------------------------------------------------ API + offline queue
async function authorizedFetch(path, opts = {}, retry = true) {
  const isMultipart = opts.body instanceof FormData;
  const headers = {
    ...(isMultipart ? {} : { "Content-Type": "application/json" }),
    ...(session ? { Authorization: "Bearer " + session.access_token } : {}),
    ...(opts.headers || {}),
  };
  const timeoutMs = path === "/assistant/document" ? 120000 : path === "/assistant/ask" ? 60000 : 15000;
  const r = await fetch(API + path, { ...opts, headers, signal: AbortSignal.timeout(timeoutMs) });
  if (r.status === 401 && session && retry) {
    const rr = await fetch(API + "/auth/refresh", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ refresh_token: session.refresh_token }) });
    if (rr.ok) {
      session = await rr.json();
      sessionStorage.setItem("session", JSON.stringify(session));
      return authorizedFetch(path, opts, false);
    }
    logout();
  }
  return r;
}

async function api(path, opts = {}) {
  let r;
  try {
    r = await authorizedFetch(path, opts);
  } catch (error) {
    const timedOut = error instanceof DOMException && error.name === "TimeoutError";
    const e = new Error(timedOut
      ? "CareSync is taking longer than expected. Please try again, or check that Ollama is running."
      : "Care server is not reachable. Start the project with run.ps1, then try again.");
    e.name = timedOut ? "TimeoutError" : "NetworkError";
    e.cause = error;
    throw e;
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
function cleanForSpeech(text) {
  return String(text)
    .replace(/```[\s\S]*?```/g, "")
    .replace(/\*\*(.*?)\*\*/g, "$1")
    .replace(/__(.*?)__/g, "$1")
    .replace(/`([^`]+)`/g, "$1")
    .replace(/^\s*#{1,6}\s*/gm, "")
    .replace(/^\s*[-*+]\s+/gm, "")
    .replace(/^\s*\d+[.)]\s+/gm, "")
    .replace(/[🔊✨⚠️✅]/gu, "")
    .replace(/\s+/g, " ")
    .trim();
}
const say = (text) => h("button", { class: "alt", "aria-label": t("listen"), onclick: () => speak(cleanForSpeech(text)) }, "🔊 " + t("listen"));
const note = (text, cls = "muted") => h("p", { class: cls, role: "status" }, text);
function playNotificationChime() {
  try {
    const AudioContext = window.AudioContext || window.webkitAudioContext;
    if (!AudioContext) return false;
    const context = new AudioContext();
    const now = context.currentTime;
    [659.25, 783.99].forEach((frequency, index) => {
      const oscillator = context.createOscillator();
      const gain = context.createGain();
      oscillator.type = "sine";
      oscillator.frequency.value = frequency;
      gain.gain.setValueAtTime(0.0001, now + index * 0.16);
      gain.gain.exponentialRampToValueAtTime(0.12, now + index * 0.16 + 0.02);
      gain.gain.exponentialRampToValueAtTime(0.0001, now + index * 0.16 + 0.22);
      oscillator.connect(gain).connect(context.destination);
      oscillator.start(now + index * 0.16);
      oscillator.stop(now + index * 0.16 + 0.24);
    });
    window.setTimeout(() => context.close().catch(() => {}), 700);
    return true;
  } catch {
    return false;
  }
}
function missedDoseAlert(today) {
  if (!today.alert) return null;
  const signature = today.missed_doses.map((dose) => `${dose.medication_id}:${dose.slot}`).join("|");
  const previous = localStorage.getItem("missed-dose-alert-signature");
  const soundEnabled = localStorage.getItem("missed-dose-sound") === "on";
  if (soundEnabled && signature !== previous) {
    playNotificationChime();
  }
  localStorage.setItem("missed-dose-alert-signature", signature);
  const soundButton = h("button", { type: "button", class: "alert-sound-button", onclick: () => {
    if (playNotificationChime()) {
      localStorage.setItem("missed-dose-sound", "on");
      soundButton.textContent = "🔔 Notification sound enabled";
    }
  } }, soundEnabled ? "🔔 Test notification sound" : "🔔 Enable notification sound");
  return h("section", { class: "missed-dose-alert", role: "alert" },
    h("div", { class: "missed-dose-alert-title" }, h("span", {}, "⚠️"), h("strong", {}, today.alert.title)),
    h("p", {}, today.alert.message),
    h("div", { class: "missed-dose-list" }, ...today.missed_doses.map((d) => h("span", {}, `${d.name} · ${d.slot}`))),
    h("div", { class: "missed-dose-alert-actions" }, soundButton),
    h("small", {}, "This is a reminder, not a dosing instruction."));
}

// ------------------------------------------------------------------ shared widgets
function alertsView(alerts) {
  return alerts.map((a) => h("div", { class: "alert sev-" + a.severity }, h("strong", {}, `${a.title} (${a.severity})`), h("p", {}, a.explanation), h("p", { class: "muted" }, `${a.escalation} Source: ${a.source}. Confidence: ${a.confidence}. Not clinician-reviewed.`)));
}
function flagsView(flags) {
  return flags.map((f) => h("div", { class: "flag " + f.severity }, h("strong", {}, f.title), h("p", {}, f.explanation), h("p", { class: "muted" }, "Rule: " + f.rule_id)));
}
async function insightsCard(pid) {
  const i = await api(`/patients/${pid}/careloop/insights`);
  const [bp, glucose, weight] = await Promise.all([
    api(`/patients/${pid}/measurements?kind=bp&limit=8`),
    api(`/patients/${pid}/measurements?kind=glucose&limit=8`),
    api(`/patients/${pid}/measurements?kind=weight&limit=8`),
  ]);
  const a = i.adherence;
  const trend = (rows, label, format) => {
    if (!rows.length) return [label, "Waiting for your first check", "neutral"];
    if (rows.length < 2) return [label, `${format(rows[0])} recorded`, "neutral"];
    const newest = rows[0].v1;
    const previous = rows[1].v1;
    const direction = newest === previous ? "steady" : newest > previous ? "up from your last check" : "down from your last check";
    return [label, `${format(rows[0])} · ${direction}`, direction === "steady" ? "good" : "watch"];
  };
  const signals = [
    trend(bp, "BP trend", (r) => `${r.v1}/${r.v2}`),
    trend(glucose, "Blood sugar trend", (r) => `${r.v1} mg/dL`),
    trend(weight, "Weight trend", (r) => `${r.v1} kg`),
    ["Medication adherence", a.rate == null ? "Start logging doses" : `${Math.round(a.rate * 100)}% of recent doses logged`, a.rate == null || a.rate < 0.8 ? "watch" : "good"],
    ["Well-being trend", "Your check-in is ready when you are", "neutral"],
  ];
  return h("section", { class: "card insights-card" },
    h("div", { class: "section-heading" }, h("span", {}, icon("🧠"), h("strong", {}, "AI Health Insights")), h("span", { class: "insight-badge" }, "PERSONAL BASELINE")),
    h("p", { class: "insight-lead" }, "A supportive view of your patterns—not a diagnosis. Your care team can help interpret any change."),
    h("div", { class: "insight-summary" }, h("strong", {}, a.rate == null ? "—" : `${a.taken}/${a.expected}`), h("span", {}, "doses logged in the last 7 days")),
    h("div", { class: "signal-grid" }, ...signals.map(([label, value, state]) => h("div", { class: `signal-item ${state}` }, h("span", {}, label), h("strong", {}, value)))),
    h("div", { class: "ai-insight-callout" }, h("strong", {}, "✨ AI reflection"), h("p", {}, bp.length > 1 ? "Your recent readings show a pattern worth noticing. Keep recording consistently and consider discussing meaningful changes with your healthcare professional." : "The more consistently you record, the more useful your personal pattern becomes. You are building a clearer picture one check at a time.")),
    ...(i.flags.length ? flagsView(i.flags) : [h("p", { class: "ok" }, "No flags right now.")]), note(i.threshold_note));
}
async function medAddCard(pid, prescribing) {
  const out = h("div"); const name = h("input", { id: "mn", placeholder: "e.g. Telma 40", "aria-label": t("addmed") });
  const timing = h("select", { "aria-label": "time" }, ...["morning", "afternoon", "evening", "night"].map((s) => h("option", { value: s }, s)));
  const safetyOut = h("div", { class: "medication-safety-output", role: "status" });
  const safetyBrief = (x) => h("div", { class: "safety-brief" },
    h("div", { class: "safety-brief-head" }, h("strong", {}, `💊 ${x.query || "Medicine review"}`), h("span", { class: x.product_key ? "safety-confidence" : "safety-confidence unknown" }, x.product_key ? `${Math.round(x.confidence * 100)}% match` : "Needs review")),
    h("div", { class: "safety-brief-grid" },
      h("div", {}, h("small", {}, "Purpose"), h("strong", {}, x.generic_name ? `Information about ${x.generic_name}` : "Not identified")),
      h("div", {}, h("small", {}, "How to take"), h("strong", {}, "Follow the prescribed instructions")),
      h("div", {}, h("small", {}, "Important"), h("strong", {}, "Never start, stop, or change it without your doctor or pharmacist"))),
    h("p", { class: "safety-escalation" }, "⚠ Discuss possible concerns with your pharmacist or doctor. This tool supports a safer conversation; it does not prescribe."));
  const reviewList = async () => {
    safetyOut.replaceChildren(note("Reviewing your active medication list...", "muted"));
    try {
      const [meds, report] = await Promise.all([api(`/patients/${pid}/medications`), api(`/patients/${pid}/medguard/report`)]);
      const alerts = report.alerts || [];
      safetyOut.replaceChildren(
        h("div", { class: "safety-list-header" }, h("strong", {}, "Your active medicines"), h("span", {}, `${meds.length} listed`)),
        h("div", { class: "medicine-chip-list" }, ...(meds.length ? meds.map((m) => h("span", {}, `${m.name}${m.dose ? ` · ${m.dose}` : ""}`)) : [h("span", {}, "No active medicines listed yet")])),
        alerts.length ? h("div", { class: "safety-alert-stack" }, h("strong", {}, `${alerts.length} item${alerts.length === 1 ? "" : "s"} to review`), ...alertsView(alerts)) :
          h("p", { class: "ok" }, "No known signals found in the current safety knowledge base. Keep your list up to date and review it with your care team."));
    } catch (e) { safetyOut.replaceChildren(note(e.message, "alert")); }
  };
  const doAdd = async (ack) => {
    out.replaceChildren();
    try { const r = await api(`/patients/${pid}/${prescribing ? "prescriptions" : "medications"}`, { method: "POST", body: JSON.stringify({ name: name.value, timing: [timing.value], confirmed: true, acknowledge_alerts: ack }) });
      out.append(note("Saved.", "ok"), ...alertsView(r.alerts)); }
    catch (e) { if (e.status === 409) { out.append(note(e.message, "muted"), ...alertsView(e.detail.alerts), h("button", { onclick: () => doAdd(true) }, t("ack"))); } else out.append(note(e.message, "alert")); }
  };
  const check = async () => { out.replaceChildren(); safetyOut.replaceChildren(note("Checking the medicine safely...", "muted")); const r = await api("/medguard/resolve", { method: "POST", body: JSON.stringify({ names: [name.value] }) }); const x = r.results[0];
    safetyOut.replaceChildren(safetyBrief(x), ...(r.alerts.length ? [h("div", { class: "safety-alert-stack" }, h("strong", {}, "Possible concerns to discuss"), ...alertsView(r.alerts))] : []));
    out.append(note(x.product_key ? `Possible match: ${x.generic_name} (confidence ${x.confidence}). Please confirm.` : "Not recognised. Check the spelling or ask your pharmacist."));
    if (x.product_key) out.append(h("button", { onclick: () => doAdd(false) }, prescribing ? t("prescribe") : t("confirm"))); };
  const jump = (selector) => () => document.querySelector(selector)?.scrollIntoView({ behavior: "smooth", block: "center" });
  const actions = h("div", { class: "care-plan-actions", "aria-label": "Care plan actions" },
    h("button", { type: "button", class: "plan-action active", onclick: () => name.focus() }, h("span", {}, "💊"), h("strong", {}, "Add medicine"), h("small", {}, "Build your safe schedule")),
    h("button", { type: "button", class: "plan-action", onclick: jump(".health-check-panel") }, h("span", {}, "🩺"), h("strong", {}, "Add health check"), h("small", {}, "Record what matters today")),
    h("button", { type: "button", class: "plan-action", onclick: jump(".ask-card") }, h("span", {}, "✦"), h("strong", {}, "Ask AI"), h("small", {}, "Understand your next step")),
    h("button", { type: "button", class: "plan-action", onclick: jump(".screening-card") }, h("span", {}, "💗"), h("strong", {}, "Well-being"), h("small", {}, "Check in when ready")));
  return h("section", { class: "card care-plan-card" },
    h("div", { class: "section-heading" }, h("span", {}, icon("💊"), h("strong", {}, "Care Plan")), h("span", { class: "insight-badge" }, "ONE JOURNEY")),
    h("p", { class: "muted" }, "Your care plan connects medicines, health checks, questions, and well-being in one calm place."),
    actions,
    h("div", { class: "plan-medicine-form" }, h("strong", {}, prescribing ? t("prescribe") : "Medicine setup"), name, timing, h("button", { onclick: check }, t("check")), out),
    h("section", { class: "medication-safety-panel" }, h("div", { class: "section-heading" }, h("span", {}, icon("🛡"), h("strong", {}, t("medicationSafety"))), h("span", { class: "insight-badge" }, "PHARMACIST READY")),
      h("p", { class: "muted" }, "Understand what you entered, surface possible concerns, and prepare a clear question for your care team. No medication changes are recommended here."),
      h("div", { class: "safety-actions" }, h("button", { type: "button", onclick: () => name.value.trim() ? check() : name.focus() }, "🔎 " + t("safetyCheck")), h("button", { type: "button", class: "alt", onclick: reviewList }, "🧾 " + t("listReview"))), safetyOut));
}
async function summaryCard(pid, canApprove) {
  const out = h("div");
  const show = async (r) => { const c = r.content; out.replaceChildren(h("p", {}, h("strong", {}, `Status: ${r.status}`), r.status === "draft" ? " (AI-assisted draft: clinician review required)" : ""), h("p", {}, c.narrative),
    ...(c.flags.length ? [h("h3", {}, "Flags"), ...flagsView(c.flags)] : []), ...(c.medication_alerts.length ? [h("h3", {}, "Medicine alerts"), ...alertsView(c.medication_alerts)] : []), h("h3", {}, "Suggested questions"), h("ul", {}, c.questions.map((q) => h("li", {}, q))),
    h("button", { class: "alt", onclick: async () => { const resp = await authorizedFetch(`/summaries/${r.id}/pdf`); if (!resp.ok) throw new Error("The PDF could not be downloaded."); window.open(URL.createObjectURL(await resp.blob())); } }, t("pdf")),
    ...(canApprove && r.status === "draft" ? [h("button", { onclick: async () => { await api(`/summaries/${r.id}/approve`, { method: "POST" }); show(await api(`/summaries/${r.id}`)); } }, t("approve"))] : [])); };
  return h("section", { class: "card care-summary-card" },
    h("div", { class: "section-heading" }, h("span", {}, icon("🧑‍⚕️"), h("strong", {}, t("careSummary"))), h("span", { class: "insight-badge" }, "CLINICIAN HANDOFF")),
    h("p", { class: "muted" }, "Create a focused, AI-assisted snapshot for a care conversation. It can bring together recent trends, adherence, measurements, well-being changes, and questions."),
    h("div", { class: "summary-pillars" }, ...["Recent health trends", "Medication adherence", "Missed doses", "Recent measurements", "Well-being changes", "Questions for doctor"].map((x) => h("span", {}, x))),
    h("div", { class: "summary-review-note" }, "Clinician review required. This summary supports a conversation; it does not make medical decisions."),
    h("button", { onclick: async () => show(await api(`/patients/${pid}/summary`, { method: "POST" })) }, "✨ Generate Care Team Summary"),
    out);
}

function careHub(completed, total) {
  const medicineDone = total > 0 && completed === total;
  const items = [
    [t("medicines"), medicineDone ? "All doses recorded" : `${completed}/${total} doses recorded`, "💊", medicineDone],
    [t("healthCheck"), "Record a reading", "🩺", false],
    [t("wellbeing"), "Take a gentle check-in", "💗", false],
    [t("followup"), "Review your care insights", "🗓️", false],
  ];
  return h("div", { class: "care-hub", "aria-label": t("care") },
    h("div", { class: "care-hub-title" }, h("strong", {}, "Your care, in one place"), h("span", {}, "TODAY")),
    h("div", { class: "care-hub-grid" }, ...items.map(([label, detail, emoji, done]) =>
      h("div", { class: `care-tile${done ? " is-done" : ""}` }, h("span", { class: "care-tile-icon", "aria-hidden": "true" }, emoji), h("strong", {}, label), h("small", {}, detail), done ? h("span", { class: "care-tile-status" }, "✓") : null))),
    h("p", { class: "care-hub-note" }, "A complete day is more than medicine: notice your body, mood, and next step."));
}

function quickHealthCheck(pid) {
  const panel = h("div", { class: "health-check-panel" });
  const choices = [
    ["bp", "Blood pressure", "🩺"],
    ["glucose", "Blood sugar", "🩸"],
    ["weight", "Weight", "⚖️"],
    ["temperature", "Temperature", "🌡️"],
    ["symptoms", "Symptoms", "📝"],
    ["other", "Other", "＋"],
  ];
  const input = h("input", { type: "number", step: "any", placeholder: "Enter a value" });
  const second = h("input", { type: "number", step: "any", placeholder: "Bottom number" });
  const noteInput = h("textarea", { rows: "3", placeholder: "Describe what you noticed..." });
  const message = h("p", { class: "muted", role: "status" });
  let selected = "bp";
  const render = () => {
    const isBp = selected === "bp";
    const isText = selected === "symptoms" || selected === "other";
    input.placeholder = isText ? "Optional title" : selected === "glucose" ? "mg/dL" : selected === "weight" ? "kg" : "°C";
    input.type = isText ? "text" : "number";
    second.hidden = !isBp;
    noteInput.hidden = !isText;
    save.hidden = isText;
    message.textContent = isText ? "For personal notes, use Ask a question below to describe this safely to your care team." : "Your care team can review this with your consent.";
  };
  const save = h("button", { type: "button", onclick: async () => {
    const value = Number(input.value);
    if (!value || (selected === "bp" && !Number(second.value))) { message.textContent = "Enter the requested values first."; message.className = "alert"; return; }
    try { await queued(`/patients/${pid}/measurements`, { kind: selected, v1: value, v2: selected === "bp" ? Number(second.value) : undefined }); message.textContent = "Saved. You are taking a positive step for your health."; message.className = "ok"; input.value = ""; second.value = ""; } catch (e) { message.textContent = e.message; message.className = "alert"; }
  } }, t("save"));
  const buttons = h("div", { class: "health-choice-grid" }, ...choices.map(([kind, label, emoji]) => h("button", { type: "button", class: kind === selected ? "health-choice active" : "health-choice", onclick: (e) => { selected = kind; buttons.querySelectorAll("button").forEach((b) => b.classList.remove("active")); e.currentTarget.classList.add("active"); render(); } }, h("span", {}, emoji), label)));
  render();
  panel.append(buttons, h("div", { class: "health-entry" }, input, second, noteInput, save), message);
  return card("🩺 Quick Health Check", h("p", { class: "muted" }, "Choose what feels useful today. Every small check helps you understand your health journey."), panel);
}

// ------------------------------------------------------------------ role views
async function patientView(main) {
  const pid = session.user_id; const today = await api(`/patients/${pid}/today`);
  const completed = today.doses.filter((d) => d.taken).length;
  const total = today.doses.length;
  const missedAlert = missedDoseAlert(today);
  const list = h("div", {}, ...(today.doses.length ? today.doses.map((d) => h("div", { class: "dose" },
    h("span", {}, `${d.name} ${d.dose || ""} - ${d.slot}`),
    d.taken ? h("span", { class: "ok" }, "✔ " + t("taken")) : h("button", { onclick: async () => { await queued(`/patients/${pid}/doses`, { medication_id: d.medication_id, slot: d.slot }); route(); } }, t("mark")))) : [
    h("div", { class: "empty-medicine-state" }, h("span", {}, "💊"), h("strong", {}, "Your medicine list is ready for you"), h("p", {}, "Add each medicine manually so your schedule reflects what your doctor or pharmacist has actually prescribed."), h("small", {}, "Nothing is pre-filled. You stay in control of every medicine."), h("button", { type: "button", onclick: () => document.querySelector(".plan-medicine-form")?.scrollIntoView({ behavior: "smooth", block: "center" }) }, "＋ Set up my medicines")),
  ]));
  const voiceOut = h("p", { role: "status" });
  const sys = h("input", { type: "number", "aria-label": t("sys") }), dia = h("input", { type: "number", "aria-label": t("dia") }), glu = h("input", { type: "number", "aria-label": t("glu") });
  main.append(pageIntro("YOUR CARE OVERVIEW", "Good to see you, Ravi", "Keep your care routine simple. Record what matters and bring questions to your care team."), ...(missedAlert ? [missedAlert] : []),
    h("div", { class: "stats-grid futuristic-stats" },
      continuityStat("Care continuity score", `${total ? Math.round((completed / total) * 100) : 0}%`, "Based on your recent care activity", "score"),
      continuityStat("Today's care", `${completed}/${total}`, "tasks completed", "today"),
      continuityStat("AI recommendation", completed < total ? "Record your health reading" : "Keep your care routine going", "next helpful step", "recommendation")),
    h("div", { class: "content-grid" },
      card(t("care"), h("div", { class: "section-heading" }, h("span", {}, icon("✓"), t("medicines")), h("span", { class: "progress-label" }, `${completed}/${total}`)), list, h("button", { class: "voice-action", onclick: () => listen(async (txt) => { const r = await api(`/patients/${pid}/voice-log`, { method: "POST", body: JSON.stringify({ text: txt }) }); voiceOut.textContent = r.reply; speak(r.reply); route(); }) }, "🎤 " + t("voice")), voiceOut, careHub(completed, total)),
      quickHealthCheck(pid)),
    await insightsCard(pid),
    await medAddCard(pid, false), await summaryCard(pid, false),
    h("section", { class: "care-tools" }, h("h2", {}, "More care tools"), h("p", { class: "muted" }, "Use these whenever you have time. Nothing here replaces a clinician."), await extras(pid)));
}
async function extras(pid) {
  const out = h("div", { class: "answer-panel", role: "status" }), q = h("textarea", { "aria-label": t("ask"), placeholder: lang === "ta" ? "உங்கள் கேள்வியை இங்கே தட்டச்சு செய்யுங்கள்..." : lang === "hi" ? "अपना सवाल यहाँ लिखें..." : "Type your question here...", rows: "3", maxlength: "2000" });
  const examples = {
    en: ["What do I need to do today?", "Explain my recent health trends", "Prepare me for my doctor visit", "What care tasks are pending?", "Explain my medicine instructions"],
    ta: ["இன்று நான் என்ன செய்ய வேண்டும்?", "என் சமீபத்திய உடல்நலப் போக்குகளை விளக்குங்கள்", "மருத்துவர் சந்திப்புக்கு என்னைத் தயார்படுத்துங்கள்", "எந்த பராமரிப்பு பணிகள் நிலுவையில் உள்ளன?", "என் மருந்து வழிமுறைகளை விளக்குங்கள்"],
    hi: ["आज मुझे क्या करना है?", "मेरी हाल की सेहत के रुझान समझाएँ", "डॉक्टर से मिलने के लिए मुझे तैयार करें", "देखभाल के कौन से काम बाकी हैं?", "मेरी दवा के निर्देश समझाएँ"],
  }[lang] || [];
  const exampleButtons = h("div", { class: "question-chips", "aria-label": "Example questions" }, ...examples.map((example) => h("button", { type: "button", class: "chip", onclick: () => { q.value = example; q.focus(); } }, example)));
  const count = h("span", { class: "character-count" }, "0/2000");
  q.addEventListener("input", () => { count.textContent = `${q.value.length}/2000`; });
  const featureList = h("ul", { class: "ask-features" },
    h("li", {}, "Type any question in your own words"),
    h("li", {}, "Answers follow your selected language"),
    h("li", {}, "Ask about health terms, readings, medicines, or visits"),
    h("li", {}, "Safety checks protect against urgent or unsafe advice"));
  const documentInput = h("input", { type: "file", accept: ".pdf,.txt,.md,.csv,.json,image/png,image/jpeg,image/webp", "aria-label": "Upload medical document" });
  const documentOut = h("div", { class: "document-answer-panel", role: "status" });
  const followupQ = h("textarea", { "aria-label": "Ask another CareSync question", placeholder: "Ask another question...", rows: "3", maxlength: "2000" });
  const followupCount = h("span", { class: "character-count" }, "0/2000");
  const followupStatus = h("span", { class: "followup-status", role: "status" });
  followupQ.addEventListener("input", () => { followupCount.textContent = `${followupQ.value.length}/2000`; });
  const followupForm = h("form", { class: "ask-followup-form", onsubmit: async (e) => {
    e.preventDefault();
    const text = followupQ.value.trim();
    if (!text) { followupStatus.replaceChildren(note("Type another question first.", "alert")); return; }
    followupStatus.replaceChildren(note("Preparing a safe answer...", "muted"));
    try {
      const answer = await api("/assistant/ask", { method: "POST", body: JSON.stringify({ text, lang }) });
      const answerBlock = h("div", { class: "answer-panel followup-answer" },
        h("p", { class: "answer-text" }, answer.text),
        say(answer.text),
        note(answer.disclaimer),
        ...(answer.crisis_resources || []).map((c) => h("p", {}, `${c.name}: ${c.phone}`)));
      out.insertBefore(answerBlock, followupForm);
      followupQ.value = "";
      followupCount.textContent = "0/2000";
      followupStatus.replaceChildren();
    } catch (error) { followupStatus.replaceChildren(note(error.message, "alert")); }
  } }, h("strong", {}, "Continue this conversation"), followupQ, h("div", { class: "ask-actions" }, followupCount, h("button", { type: "submit" }, "Ask CareSync")), followupStatus);
  const explainDocument = async () => {
    const file = documentInput.files?.[0];
    if (!file) { documentOut.replaceChildren(note("Choose a medical document first.", "alert")); return; }
    documentOut.replaceChildren(note("Reading your document securely...", "muted"));
    const form = new FormData(); form.append("file", file); form.append("lang", lang);
    try {
      const result = await api("/assistant/document", { method: "POST", body: form });
      const facts = result.document_facts?.length
        ? [h("div", { class: "document-facts" }, h("strong", {}, "Verified details from your document"), h("small", {}, "Check these lines against the original before acting."), h("ul", {}, ...result.document_facts.map((fact) => h("li", {}, fact))))]
        : [];
      documentOut.replaceChildren(h("div", { class: "document-answer-head" }, h("strong", {}, "📄 " + result.filename), h("span", {}, result.stored ? "Stored" : "Not stored")), ...facts, h("p", { class: "answer-text" }, result.text), say(result.text), note(result.disclaimer), ...(result.crisis_resources || []).map((c) => h("p", {}, `${c.name}: ${c.phone}`)));
    } catch (error) {
      documentOut.replaceChildren(note(error.name === "TimeoutError"
        ? "The image is taking longer than expected. Please try a clearer image or upload the original PDF."
        : error.message, "alert"));
    }
  };
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
  const wellbeingFields = [
    ["Mood", "How are you feeling emotionally today?"],
    ["Stress", "How much stress are you carrying today?"],
    ["Sleep", "How restorative was your sleep?"],
    ["Energy", "How much energy do you have today?"],
    ["Daily functioning", "How manageable do today's activities feel?"],
  ];
  const wellbeingValues = ["Needs support", "A little difficult", "Okay", "Going well", "Strong today"];
  const wellbeingControls = wellbeingFields.map(([label, prompt]) => h("label", { class: "wellbeing-row" },
    h("span", {}, h("strong", {}, label), h("small", {}, prompt)),
    h("select", { "aria-label": label }, ...wellbeingValues.map((value, index) => h("option", { value: index }, value)))));
  const wellbeingOut = h("div", { role: "status" });
  const saveWellbeing = () => {
    const values = wellbeingControls.map((row) => Number(row.querySelector("select").value));
    localStorage.setItem(`wellbeing-check-${pid}`, JSON.stringify({ day: new Date().toISOString().slice(0, 10), values }));
    const average = values.reduce((sum, value) => sum + value, 0) / values.length;
    wellbeingOut.replaceChildren(h("p", { class: "wellbeing-success" }, average >= 3 ? "✨ You are building a steady picture of your well-being. Keep choosing the small steps that support you." : "✨ Thank you for checking in. A gentler day is still progress—consider sharing what feels difficult with someone you trust or your care team."), h("p", { class: "muted" }, "Saved on this device for today. This check-in is not a diagnosis."));
  };
  const consentEmail = h("input", { type: "email", placeholder: "doctor@demo.test", "aria-label": "Care team email" });
  const consentScope = h("select", { "aria-label": "Access level" }, ...[
    ["summary", "Care summary"],
    ["medications", "Medicines"],
    ["measurements", "Health readings"],
    ["adherence", "Care progress"],
    ["appointments", "Appointments"],
    ["screening", "Well-being screening"],
  ].map(([value, label]) => h("option", { value }, label)));
  const consentOut = h("div", { role: "status" });
  const shareAccess = async () => {
    if (!consentEmail.value.trim()) { consentOut.replaceChildren(note("Enter the care team member's email first.", "alert")); return; }
    try {
      const enteredEmail = consentEmail.value.trim().toLowerCase();
      const email = enteredEmail.replace(/@(demo)\.com$/i, "@$1.test");
      if (email !== enteredEmail) {
        consentOut.replaceChildren(note("Using the demo account address " + email + ".", "muted"));
      }
      await api("/consents", { method: "POST", body: JSON.stringify({ grantee_email: email, scopes: [consentScope.value] }) });
      consentEmail.value = ""; consentOut.replaceChildren(note("Access shared. You remain in control and can revoke it at any time.", "ok")); route();
    } catch (e) { consentOut.replaceChildren(note(e.message, "alert")); }
  };
  const roleGuide = h("div", { class: "privacy-role-grid" },
    h("div", {}, "🧑‍⚕️", h("strong", {}, "Doctor"), h("small", {}, "Clinical decisions and visit preparation")),
    h("div", {}, "💊", h("strong", {}, "Pharmacist"), h("small", {}, "Medicine and safety review")),
    h("div", {}, "👨‍👩‍👧", h("strong", {}, "Caregiver"), h("small", {}, "Support with daily care and progress")));
  return h("div", {},
    h("section", { class: "card ask-card primary-ai-card" }, h("div", { class: "section-heading" }, h("span", {}, icon("🤖"), h("strong", {}, t("ask"))), h("span", { class: "insight-badge" }, "PRIMARY AI COMPANION")), h("p", { class: "ai-companion-line" }, t("askCompanion")), h("p", { class: "muted" }, lang === "ta" ? "எந்த கேள்வியையும் தட்டச்சு செய்யுங்கள். உங்கள் மொழியில் எளிய பதில் கிடைக்கும்." : lang === "hi" ? "कोई भी सवाल लिखें। आपको अपनी भाषा में सरल उत्तर मिलेगा।" : "Ask anything about your care journey. CareSync AI turns your question into a clear, practical next step in your selected language."), featureList, exampleButtons, h("form", { class: "ask-form", onsubmit: async (e) => { e.preventDefault(); if (!q.value.trim()) { out.replaceChildren(note(lang === "ta" ? "முதலில் ஒரு கேள்வியை எழுதுங்கள்." : lang === "hi" ? "पहले अपना सवाल लिखें।" : "Type a question first.", "alert")); return; } out.replaceChildren(note(lang === "ta" ? "பாதுகாப்பான பதிலை உருவாக்குகிறது..." : lang === "hi" ? "सुरक्षित उत्तर तैयार हो रहा है..." : "Preparing a safe answer...", "muted")); try { const r = await api("/assistant/ask", { method: "POST", body: JSON.stringify({ text: q.value.trim(), lang }) }); out.replaceChildren(h("div", { class: "answer-panel" }, h("p", { class: "answer-text" }, r.text), say(r.text), note(r.disclaimer), ...(r.crisis_resources || []).map((c) => h("p", {}, `${c.name}: ${c.phone}`))), followupForm); } catch (err) { out.replaceChildren(note(err.message, "alert")); } } }, q, h("div", { class: "ask-actions" }, count, h("button", { type: "submit" }, t("send")))), out, h("div", { class: "document-upload-panel" }, h("strong", {}, "📄 Ask about a medical document"), h("p", { class: "muted" }, "Upload a report, prescription, or lab document. CareSync explains readable text in your selected language and does not store the file."), h("div", { class: "document-upload-row" }, documentInput, h("button", { type: "button", onclick: explainDocument }, "✨ Explain document")), documentOut)),
    h("section", { class: "card wellbeing-card" },
      h("div", { class: "section-heading" }, h("span", {}, icon("💗"), h("strong", {}, t("wellbeingCheck"))), h("span", { class: "insight-badge" }, "YOUR DAILY SIGNALS")),
      h("p", { class: "wellbeing-lead" }, "A five-minute pause to notice the whole you—not just symptoms."),
      h("div", { class: "wellbeing-grid" }, ...wellbeingControls),
      h("button", { class: "primary-wide wellbeing-button", onclick: saveWellbeing }, "✨ Save today's check-in"), wellbeingOut,
      h("div", { class: "validated-screening" },
        h("div", { class: "section-heading" }, h("span", {}, icon("◌"), h("strong", {}, t("screening"))), h("span", { class: "insight-badge" }, "OPTIONAL")),
        h("p", { class: "muted" }, "Use this validated questionnaire when you want a deeper, structured check-in. It is a screening tool, not a diagnosis."),
        progress, phq,
        h("button", { class: "primary-wide", onclick: async () => { const r = await api(`/patients/${pid}/screenings`, { method: "POST", body: JSON.stringify({ instrument: "phq9", answers }) }); phqOut.replaceChildren(h("p", {}, r.message), ...r.crisis_resources.map((c) => h("p", {}, `${c.name}: ${c.phone}`))); } }, t("submit")), phqOut)),
    h("section", { class: "card privacy-card" },
      h("div", { class: "section-heading" }, h("span", {}, icon("🔐"), h("strong", {}, t("consent"))), h("span", { class: "insight-badge" }, "YOU DECIDE")),
      h("p", { class: "privacy-lead" }, "Your care information is yours. Share only what helps, with only the people you trust."),
      roleGuide,
      h("div", { class: "privacy-share-form" }, h("strong", {}, t("share")), consentEmail, consentScope, h("button", { onclick: shareAccess }, "🔗 Share access")),
      h("p", { class: "privacy-help" }, "For this demo, use doctor@demo.test, worker@demo.test, or priya@demo.test."),
      consentOut,
      h("h3", {}, "Who currently has access"),
      ...(consents.length ? consents.map((c) => h("div", { class: "consent-row" }, h("span", {}, `${c.name} (${c.role})`, h("small", {}, c.scopes.join(" · "))), h("button", { class: "alt", onclick: async () => { await api("/consents/" + c.id, { method: "DELETE" }); route(); } }, t("revoke")))) : [h("p", { class: "muted" }, "No one has active access yet.")]),
      h("p", { class: "privacy-note" }, "Every share and revoke action is permission-checked and recorded. CareSync AI cannot grant access on your behalf.")),
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
