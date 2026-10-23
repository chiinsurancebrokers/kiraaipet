"""Clinic workbench (demo): patient Folder, exam-enhanced report, second opinion.

No Streamlit / network code here. The caller passes `call(messages, system, max_tokens, timeout) -> str`
(the app's `claude`). DEMO MODE: patients are fictional and live only in the browser session.
"""
from __future__ import annotations

import datetime as _dt
import json
import re

import pet_policy as _pp

DOC_TYPES = ("blood", "urine", "imaging", "ecg", "cytology", "vaccination", "report", "prescription", "other")

# Physical-exam fields: (key, label_el, label_en, kind) — kind: 'num' | 'text'
EXAM_FIELDS = [
    ("temp", "Θερμοκρασία (°C)", "Temperature (°C)", "num"),
    ("hr", "Καρδιακός ρυθμός (bpm)", "Heart rate (bpm)", "num"),
    ("rr", "Αναπνοές (/min)", "Respiratory rate (/min)", "num"),
    ("weight", "Βάρος (kg)", "Weight (kg)", "num"),
    ("bcs", "BCS (1-9)", "Body condition score (1-9)", "num"),
    ("mm", "Βλεννογόνοι / CRT", "Mucous membranes / CRT", "text"),
    ("hydration", "Αφυδάτωση", "Hydration", "text"),
    ("heart", "Ακρόαση καρδιάς", "Heart auscultation", "text"),
    ("lungs", "Ακρόαση πνευμόνων", "Lung auscultation", "text"),
    ("abdomen", "Ψηλάφηση κοιλιάς", "Abdominal palpation", "text"),
    ("skin", "Δέρμα / τρίχωμα", "Skin / coat", "text"),
    ("eyes_ears", "Μάτια / αυτιά / στόμα", "Eyes / ears / mouth", "text"),
    ("msk", "Μυοσκελετικό / νευρολογικό", "Musculoskeletal / neuro", "text"),
    ("other", "Άλλα ευρήματα", "Other findings", "text"),
]

ORGANISE_PROMPT = """You are a veterinary records assistant. Read the attached document(s) for ONE pet patient and \
return ONE JSON object per document set, no preamble, no markdown fences:

{
  "entries": [
    {"doc_type": "blood | urine | imaging | ecg | cytology | vaccination | report | prescription | other",
     "title": "<short title, e.g. 'Complete blood count + biochemistry'>",
     "date": "<YYYY-MM-DD or null>",
     "center": "<lab / clinic as stated or null>",
     "summary": "<1-3 plain sentences: what the document shows>",
     "values": [{"name": "<test>", "value": "<value as written>", "unit": "<unit or ''>", "ref": "<reference range as printed or ''>",
                 "flag": "high | low | normal | unknown"}],
     "medications": ["<drug + dose if stated>"],
     "notes": "<important remarks, or ''>"}
  ],
  "patient_hint": {"name": null, "species": null, "microchip": null}
}

Rules:
- Use ONLY what the document says. Never invent values, dates or reference ranges. Flag high/low only when a reference range \
is printed or the document itself marks the value; otherwise "unknown".
- One entry per distinct exam/document. At most 12 entries, at most 40 values per entry (most abnormal first).
- Do NOT output owner name, address, phone or e-mail.
- Not a diagnosis: summarise findings, do not interpret them."""

REPORT_SYSTEM = """You are a veterinary clinical-documentation assistant writing a DRAFT report for the treating veterinarian to \
edit and sign. You are decision support, not the clinician: do not state a definitive diagnosis; use "findings consistent with", \
"differentials to consider". Use ONLY the data supplied (owner's pre-visit assessment, folder documents, the vet's physical exam). \
If something is not provided, write "not recorded" — never invent values.

Structure (markdown, concise):
## Patient
## Presenting complaint / history (from owner's assessment)
## Physical examination (as recorded by the vet; mark values outside typical ranges for the species)
## Investigations (from the folder: key values with dates; flag abnormal)
## Assessment (problem list; differentials to consider, most likely first, with one-line reasoning)
## Suggested next steps (tests, monitoring, owner advice; flag anything urgent)
## Notes
End with: "Draft prepared with AI decision support — to be reviewed and signed by the treating veterinarian."
{lang}"""

OPINION_SYSTEM = """You are giving a veterinarian a quick SECOND OPINION as decision support. The vet's judgement decides. \
Use ONLY the supplied data. Be brief and practical (max ~250 words), in this structure:
**Agree / consider:** what fits the findings and what else could explain them (differentials, most likely first).
**Could rule in/out:** 3-5 tests or checks that would discriminate.
**Red flags:** anything that needs urgent action or that would change management.
**Gaps:** key information not recorded that would sharpen the picture.
Never state a definitive diagnosis, never invent values, mention dosing only if the vet asked. {lang}"""


def _lang(lang):
    return ("Write in GREEK." if lang == "el" else "Write in ENGLISH.")


def parse_json(raw):
    return _pp._json_from(raw)


def _s(v, n=300):
    v = "" if v is None else str(v).strip()
    return v[:n]


def normalize_entries(data):
    out = []
    for e in (data or {}).get("entries", [])[:12] if isinstance(data, dict) else []:
        if not isinstance(e, dict):
            continue
        vals = []
        for v in (e.get("values") or [])[:40]:
            if isinstance(v, dict) and _s(v.get("name"), 80):
                vals.append({"name": _s(v.get("name"), 80), "value": _s(v.get("value"), 40), "unit": _s(v.get("unit"), 20),
                             "ref": _s(v.get("ref"), 40),
                             "flag": v.get("flag") if v.get("flag") in ("high", "low", "normal", "unknown") else "unknown"})
        out.append({
            "doc_type": e.get("doc_type") if e.get("doc_type") in DOC_TYPES else "other",
            "title": _s(e.get("title"), 120) or "Document",
            "date": _pp._iso(e.get("date")),
            "center": _s(e.get("center"), 100) or None,
            "summary": _s(e.get("summary"), 500),
            "values": vals,
            "medications": [_s(m, 100) for m in (e.get("medications") or [])[:10] if _s(m, 100)],
            "notes": _s(e.get("notes"), 400),
        })
    return out


def organise(call, files, lang="en"):
    """files: [(name, bytes, mime)] -> (entries, error_code)."""
    content, err = _pp.build_content(files, lang)
    if err:
        return None, err
    system = ORGANISE_PROMPT + "\n\n" + _pp.lang_directive(lang)
    raw = ""
    for _ in range(2):
        raw = call(messages=[{"role": "user", "content": content}], system=system, max_tokens=6000, timeout=150)
        if raw.startswith("⚠️"):
            continue
        entries = normalize_entries(parse_json(raw))
        if entries:
            return entries, ""
    return None, ("unreachable" if (raw or "").startswith("⚠️") else "unparsable")


def folder_text(patient):
    """Compact text of the folder for prompts (most recent first)."""
    rows = sorted(patient.get("entries", []), key=lambda e: e.get("date") or "", reverse=True)
    parts = []
    for e in rows[:25]:
        vals = "; ".join(
            f"{v['name']} {v['value']}{(' ' + v['unit']) if v.get('unit') else ''}"
            + (f" [{v['flag']}]" if v.get("flag") in ("high", "low") else "") for v in e.get("values", [])[:25])
        parts.append(f"- {e.get('date') or 'undated'} · {e['doc_type']} · {e['title']}"
                     + (f" ({e['center']})" if e.get("center") else "")
                     + f": {e.get('summary', '')}" + (f" Values: {vals}." if vals else "")
                     + (f" Meds: {', '.join(e['medications'])}." if e.get("medications") else ""))
    return "\n".join(parts) or "No documents in the folder."


def exam_text(exam):
    rows = []
    for k, _el, en, _kind in EXAM_FIELDS:
        v = (exam or {}).get(k)
        if v not in (None, "", 0, 0.0):
            rows.append(f"- {en}: {v}")
    return "\n".join(rows) or "No physical exam recorded."


def patient_header(p):
    bits = [p.get("name", ""), p.get("species", ""), p.get("breed", ""), f"{p.get('age', '')}", p.get("sex", "")]
    return ", ".join(b for b in bits if b) + (f" · microchip {p['chip']}" if p.get("chip") else "")


def _payload(p, exam, complaint):
    return (f"PATIENT: {patient_header(p)}\n\nOWNER'S PRE-VISIT ASSESSMENT / COMPLAINT:\n{complaint or p.get('previsit') or 'not provided'}\n\n"
            f"PHYSICAL EXAM (by the vet):\n{exam_text(exam)}\n\nFOLDER:\n{folder_text(p)}")


def draft_report(call, patient, exam, complaint, lang="en"):
    return call(messages=[{"role": "user", "content": _payload(patient, exam, complaint)}],
                system=REPORT_SYSTEM.format(lang=_lang(lang)), max_tokens=2200, timeout=90)


def second_opinion(call, patient, exam, complaint, working_dx, lang="en"):
    msg = _payload(patient, exam, complaint) + f"\n\nVET'S WORKING DIAGNOSIS / QUESTION:\n{working_dx or 'not stated'}"
    return call(messages=[{"role": "user", "content": msg}],
                system=OPINION_SYSTEM.format(lang=_lang(lang)), max_tokens=1400, timeout=75)


def search(patients, q):
    q = (q or "").strip().lower()
    if not q:
        return patients
    return [p for p in patients if q in (p.get("name", "") + " " + p.get("chip", "") + " " + p.get("species", "")).lower()]


def new_patient(name, species, breed="", chip="", age="", sex=""):
    return {"id": "p" + re.sub(r"\W", "", f"{name}{_dt.datetime.now():%H%M%S%f}")[:14], "name": name.strip(), "species": species,
            "breed": breed.strip(), "chip": chip.strip(), "age": age.strip(), "sex": sex, "entries": [], "previsit": "", "demo": True}


def _e(dt, typ, title, center, summary, values=(), meds=(), notes=""):
    return {"doc_type": typ, "title": title, "date": dt, "center": center, "summary": summary,
            "values": [dict(name=n, value=v, unit=u, ref=r, flag=f) for n, v, u, r, f in values],
            "medications": list(meds), "notes": notes}


def demo_patients(today=None):
    """Fictional patients (no real data)."""
    t = today or _dt.date.today()
    d = lambda days: (t - _dt.timedelta(days=days)).isoformat()
    rex = new_patient("Rex (demo)", "Dog", "Labrador", "900-000-000-0001", "7 y", "M")
    rex["id"] = "demo1"
    rex["previsit"] = ("Owner reports 3 days of reduced appetite, vomiting twice a day and lethargy. Drinking more than usual. "
                       "First assessment: URGENT — same-day vet visit recommended.")
    rex["entries"] = [
        _e(d(6), "blood", "Complete blood count + biochemistry", "Demo Lab", "Mild elevation of kidney values; mild anaemia.",
           [("Creatinine", "2.1", "mg/dL", "0.5-1.5", "high"), ("Urea", "78", "mg/dL", "15-50", "high"),
            ("Haematocrit", "34", "%", "37-55", "low"), ("ALT", "62", "U/L", "10-100", "normal")]),
        _e(d(40), "vaccination", "Annual vaccination", "Demo Clinic", "Core vaccines up to date.", meds=["DHPP", "Rabies"]),
        _e(d(5), "imaging", "Abdominal ultrasound", "Demo Imaging", "Kidneys of reduced corticomedullary definition; no free fluid.",
           notes="Recommend urine analysis and recheck of kidney values."),
    ]
    mimi = new_patient("Mimi (demo)", "Cat", "Domestic shorthair", "900-000-000-0002", "12 y", "F")
    mimi["id"] = "demo2"
    mimi["previsit"] = "Owner reports weight loss and a big appetite for 2 months. First assessment: SEE A VET within days."
    mimi["entries"] = [
        _e(d(14), "blood", "Thyroid panel", "Demo Lab", "Total T4 above the reference range.",
           [("Total T4", "6.8", "µg/dL", "0.8-4.7", "high"), ("Creatinine", "1.4", "mg/dL", "0.8-2.4", "normal")]),
        _e(d(90), "prescription", "Dental treatment", "Demo Clinic", "Dental scaling; one extraction.", meds=["Meloxicam 0.05 mg/kg for 3 days"]),
    ]
    bun = new_patient("Bunny (demo)", "Rabbit", "Holland Lop", "", "3 y", "M")
    bun["id"] = "demo3"
    bun["previsit"] = "Owner reports no droppings for 12 hours and a bloated belly. First assessment: EMERGENCY."
    bun["entries"] = [_e(d(200), "vaccination", "Myxomatosis / RHD vaccine", "Demo Clinic", "Vaccinated.", meds=["Myxo-RHD"])]
    return [rex, mimi, bun]
