"""Pet insurance policy analyzer.

Reads the owner's own policy document(s) (PDF / photo / text) with Claude and extracts what a
pet parent actually needs to know: how the policy pays, limits, waiting periods, exclusions and
the clauses that are easy to miss. Modelled on the Ashlar *Policy Analyzer* (merged documents,
structured JSON, "never invent figures", critical limitations) but with a pet-insurance schema.

This module has no Streamlit or network code: the caller passes a `call(messages, system,
max_tokens, timeout) -> str` function (the app's `claude`) so it is easy to test.
"""
from __future__ import annotations

import base64
import datetime as _dt
import json
import re

MAX_FILES = 4
MAX_FILE_BYTES = 12 * 1024 * 1024
_IMG = {"image/jpeg", "image/png", "image/webp", "image/gif"}

SCHEMA_PROMPT = """You are an insurance analyst reading a PET insurance (or pet health programme) document \
for the pet's owner. Extract the facts below as ONE JSON object. Return ONLY the JSON: no preamble, no markdown fences.

{
  "is_pet_policy": true,
  "document_type": "certificate | wording | quote | ipid | other",
  "insurer": "<insurer or programme provider as stated, else null>",
  "product": "<product / plan / tier name as stated, else null>",
  "policy_number": "<as stated, else null>",
  "pet": {"name": null, "species": null, "breed": null, "birth_date": null},
  "policy_period": {"start_date": "<YYYY-MM-DD or null>", "end_date": "<YYYY-MM-DD or null>", "renewal": "<how/when it renews, else null>"},
  "premium": "<amount and frequency as stated, else null>",
  "how_it_pays": {
    "model": "reimbursement | direct_network_pricing | mixed | unclear",
    "explanation": "<1-3 plain sentences on HOW money flows: does the insurer reimburse the owner after a claim, \
does the owner pay the clinic reduced network prices directly, or both depending on the clinic? Say exactly what \
the document says. If the document does not say, use 'unclear'.>",
    "reimbursement_rate": "<e.g. '80% of eligible costs' or null>"
  },
  "limits": {
    "annual_limit": "<as stated or 'not stated'>",
    "per_condition_limit": "<as stated or 'not stated'>",
    "excess_or_deductible": "<as stated or 'not stated'>",
    "co_payment": "<as stated or 'not stated'>",
    "other": "<any other cap that matters, else null>"
  },
  "benefits": [
    {"category": "<e.g. accident, illness, hospitalisation, surgery, diagnostics, vaccinations, dental, prescription \
medicine, physiotherapy, behavioural, routine/preventive, third-party liability>",
     "status": "covered | not_covered | conditional | not_stated",
     "limit_or_cost": "<limit, co-payment or price as stated, else null>",
     "conditions": "<conditions that apply, else null>",
     "evidence": "<short VERBATIM quote, max 25 words, in the document's language>"}
  ],
  "waiting_periods": [
    {"applies_to": "<what the waiting period applies to>",
     "days": <integer number of days, or null if not expressed in days>,
     "detail": "<the period as written, e.g. '45 days' or '3 months'>",
     "starts_from": "policy_start | renewal | other",
     "evidence": "<short VERBATIM quote>"}
  ],
  "exclusions": [
    {"topic": "<short label>", "detail": "<what is not covered, with figures/conditions exactly as stated>",
     "evidence": "<short VERBATIM quote>"}
  ],
  "pre_existing_conditions": "<how pre-existing conditions are treated, or 'not stated'>",
  "age_or_breed_restrictions": "<entry/renewal age limits, breed restrictions, microchip or vaccination requirements, or 'not stated'>",
  "geographic_scope": "<where cover/network applies, or 'not stated'>",
  "claims_or_usage_requirements": ["<steps the owner MUST follow before treatment or when claiming, e.g. call a helpline first>"],
  "critical_limitations": [
    {"topic": "<short label>", "detail": "<sub-limit, cap, day limit or condition an owner could easily miss, with the exact figure>"}
  ],
  "missing_information": ["<important thing an owner would want to know that this document does NOT state>"],
  "confidence": "high | medium | low",
  "summary": "<2-4 plain sentences: what this policy is and the 2-3 things that matter most>"
}

Rules:
- Base every field strictly on the document text. If something is not stated, write "not stated" (or null / empty list). \
NEVER invent figures, dates or clauses, and never infer one benefit from a related one.
- Do not treat marketing language as contract terms. If the document is a brochure or quote rather than the \
contract, say so in "summary" and lower "confidence".
- If the document is clearly NOT a pet insurance / pet health programme document, set "is_pet_policy": false, \
explain in "summary", and leave other fields empty.
- Read the whole document: exclusions, waiting periods and sub-limits are often deep in the wording. If a \
"General exclusions" / "What is not covered" section exists, read it in full and reflect it in "exclusions".
- When several documents are supplied for the same policy, a certificate/quote controls the selected plan, \
figures and dates; the wording controls scope and exclusions. If they disagree, say so in "summary".
- Keep "evidence" quotes short and verbatim. Keep each free-text value concise (max 2 sentences). List at most \
15 benefits, 12 exclusions, 8 waiting periods and 8 critical limitations, most consequential first.
- Do NOT output the owner's name, address, ID number, phone, email, bank or payment details.
- Not medical or legal advice: only report what the document says."""


def lang_directive(lang: str) -> str:
    if lang == "el":
        return ("Write all descriptive values (explanations, details, summary, missing_information, conditions) in GREEK. "
                "Keep 'evidence' quotes verbatim in the document's own language.")
    return ("Write all descriptive values in ENGLISH. Keep 'evidence' quotes verbatim in the document's own language.")


def build_content(files, lang: str = "en"):
    """files: list of (filename, bytes, mime). Returns (content_blocks, error). PDFs and images go straight to
    Claude (no extra OCR dependency); plain text is inlined."""
    if not files:
        return None, "no_files"
    blocks = []
    for name, data, mime in files[:MAX_FILES]:
        if not data:
            continue
        if len(data) > MAX_FILE_BYTES:
            return None, "too_large"
        label = f"--- Document: {name} ---"
        mime = (mime or "").lower()
        low = (name or "").lower()
        if mime == "application/pdf" or low.endswith(".pdf"):
            blocks.append({"type": "text", "text": label})
            blocks.append({"type": "document", "source": {"type": "base64", "media_type": "application/pdf",
                                                           "data": base64.b64encode(data).decode()}})
        elif mime in _IMG or low.endswith((".jpg", ".jpeg", ".png", ".webp")):
            mt = mime if mime in _IMG else ("image/png" if low.endswith(".png") else
                                            "image/webp" if low.endswith(".webp") else "image/jpeg")
            blocks.append({"type": "text", "text": label})
            blocks.append({"type": "image", "source": {"type": "base64", "media_type": mt,
                                                       "data": base64.b64encode(data).decode()}})
        elif mime.startswith("text/") or low.endswith(".txt"):
            txt = data.decode("utf-8", errors="ignore")[:150000]
            blocks.append({"type": "text", "text": f"{label}\n{txt}"})
        else:
            return None, "unsupported"
    if not blocks:
        return None, "no_files"
    blocks.append({"type": "text", "text": "Now return the JSON object described in the system instructions."})
    return blocks, ""


def _json_from(raw: str):
    raw = (raw or "").strip()
    raw = re.sub(r"^```[a-zA-Z]*\n?", "", raw).strip()
    raw = re.sub(r"\n?```$", "", raw).strip()
    m = re.search(r"\{.*\}", raw, re.DOTALL)
    if not m:
        return None
    try:
        return json.loads(m.group(0))
    except Exception:
        return None


def _s(v, n=600):
    if v is None:
        return None
    v = str(v).strip()
    return v[:n] if v else None


def _list(v, cap):
    return v[:cap] if isinstance(v, list) else []


_PRIVATE = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+|\+?\d[\d\s().-]{8,}\d")


def _clean(v):
    """Defence in depth: drop e-mail addresses / long digit runs (phones, IDs) that slipped into free text."""
    if isinstance(v, str):
        return _PRIVATE.sub("…", v) if not re.fullmatch(r"[\w/.-]{3,40}", v) else v
    return v


def normalize(data: dict) -> dict:
    """Coerce the model output to a safe, bounded structure the UI can render without guarding every key."""
    d = data if isinstance(data, dict) else {}
    pet = d.get("pet") if isinstance(d.get("pet"), dict) else {}
    per = d.get("policy_period") if isinstance(d.get("policy_period"), dict) else {}
    hp = d.get("how_it_pays") if isinstance(d.get("how_it_pays"), dict) else {}
    lim = d.get("limits") if isinstance(d.get("limits"), dict) else {}
    out = {
        "is_pet_policy": d.get("is_pet_policy") is not False,
        "document_type": _s(d.get("document_type"), 30),
        "insurer": _s(d.get("insurer"), 120), "product": _s(d.get("product"), 160),
        "policy_number": _s(d.get("policy_number"), 60),
        "pet": {k: _s(pet.get(k), 80) for k in ("name", "species", "breed", "birth_date")},
        "policy_period": {"start_date": _iso(per.get("start_date")), "end_date": _iso(per.get("end_date")),
                          "renewal": _s(per.get("renewal"), 200)},
        "premium": _s(d.get("premium"), 120),
        "how_it_pays": {"model": hp.get("model") if hp.get("model") in ("reimbursement", "direct_network_pricing", "mixed", "unclear") else "unclear",
                        "explanation": _s(hp.get("explanation"), 700), "reimbursement_rate": _s(hp.get("reimbursement_rate"), 120)},
        "limits": {k: _s(lim.get(k), 300) for k in ("annual_limit", "per_condition_limit", "excess_or_deductible", "co_payment", "other")},
        "benefits": [], "waiting_periods": [], "exclusions": [], "critical_limitations": [],
        "pre_existing_conditions": _s(d.get("pre_existing_conditions"), 500),
        "age_or_breed_restrictions": _s(d.get("age_or_breed_restrictions"), 500),
        "geographic_scope": _s(d.get("geographic_scope"), 400),
        "claims_or_usage_requirements": [_s(x, 300) for x in _list(d.get("claims_or_usage_requirements"), 8) if _s(x, 300)],
        "missing_information": [_s(x, 300) for x in _list(d.get("missing_information"), 10) if _s(x, 300)],
        "confidence": d.get("confidence") if d.get("confidence") in ("high", "medium", "low") else "low",
        "summary": _s(d.get("summary"), 900),
        "analyzed_on": _dt.date.today().isoformat(),
    }
    for b in _list(d.get("benefits"), 15):
        if isinstance(b, dict) and _s(b.get("category"), 80):
            out["benefits"].append({
                "category": _s(b.get("category"), 80),
                "status": b.get("status") if b.get("status") in ("covered", "not_covered", "conditional", "not_stated") else "not_stated",
                "limit_or_cost": _s(b.get("limit_or_cost"), 200), "conditions": _s(b.get("conditions"), 300),
                "evidence": _s(b.get("evidence"), 300)})
    for w in _list(d.get("waiting_periods"), 8):
        if isinstance(w, dict) and _s(w.get("applies_to"), 200):
            days = w.get("days")
            try:
                days = int(days) if days is not None and 0 < int(days) < 1500 else None
            except Exception:
                days = None
            out["waiting_periods"].append({
                "applies_to": _s(w.get("applies_to"), 200), "days": days, "detail": _s(w.get("detail"), 120),
                "starts_from": w.get("starts_from") if w.get("starts_from") in ("policy_start", "renewal", "other") else "policy_start",
                "evidence": _s(w.get("evidence"), 300)})
    for e in _list(d.get("exclusions"), 12):
        if isinstance(e, dict) and (_s(e.get("topic"), 120) or _s(e.get("detail"), 400)):
            out["exclusions"].append({"topic": _s(e.get("topic"), 120), "detail": _s(e.get("detail"), 400), "evidence": _s(e.get("evidence"), 300)})
    for c in _list(d.get("critical_limitations"), 8):
        if isinstance(c, dict) and (_s(c.get("topic"), 120) or _s(c.get("detail"), 400)):
            out["critical_limitations"].append({"topic": _s(c.get("topic"), 120), "detail": _s(c.get("detail"), 400)})
    # strip stray personal identifiers from free text (never from policy_number / quotes of figures)
    for k in ("summary", "premium", "pre_existing_conditions", "age_or_breed_restrictions", "geographic_scope"):
        out[k] = _clean(out[k])
    out["claims_or_usage_requirements"] = [x for x in out["claims_or_usage_requirements"]]
    return out


def _iso(v):
    try:
        return _dt.date.fromisoformat(str(v)[:10]).isoformat()
    except Exception:
        return None


def analyze(call, files, lang: str = "en", pet: dict | None = None):
    """Returns (analysis_dict | None, error_code). error_code is '' on success."""
    content, err = build_content(files, lang)
    if err:
        return None, err
    ctx = ""
    if isinstance(pet, dict) and pet.get("name"):
        ctx = (f"\nThe owner says the pet is: {pet.get('name')} ({pet.get('species_label') or pet.get('species_key') or ''}"
               f"{', ' + str(pet.get('breed')) if pet.get('breed') else ''}). Use this only to sanity-check the document.")
    system = SCHEMA_PROMPT + "\n\n" + lang_directive(lang) + ctx
    raw = ""
    for _ in range(2):
        raw = call(messages=[{"role": "user", "content": content}], system=system, max_tokens=7000, timeout=150)
        if raw.startswith("⚠️"):
            continue
        data = _json_from(raw)
        if data:
            return normalize(data), ""
    return None, ("unreachable" if (raw or "").startswith("⚠️") else "unparsable")


def waiting_rows(analysis: dict, start: _dt.date | None, today: _dt.date | None = None):
    """Waiting periods with computed end dates when the start date and a day count are known."""
    today = today or _dt.date.today()
    rows = []
    for w in (analysis or {}).get("waiting_periods", []):
        row = dict(w)
        row["end"] = None
        row["days_left"] = None
        row["state"] = "unknown"
        if w.get("days") and w.get("starts_from") == "policy_start" and start:
            end = start + _dt.timedelta(days=int(w["days"]))
            left = (end - today).days
            row.update(end=end, days_left=max(left, 0), state="done" if left <= 0 else "active")
        rows.append(row)
    return rows


def facts_for_prompt(analysis: dict) -> str:
    """Compact text the chat model treats as the authority on THIS owner's policy."""
    if not analysis:
        return ""
    a = {k: v for k, v in analysis.items() if k not in ("analyzed_on",)}
    return json.dumps(a, ensure_ascii=False, separators=(",", ":"))[:14000]
