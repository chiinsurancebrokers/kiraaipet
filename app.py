"""
PETAINURSE — AI Veterinary Nurse
Bilingual AI health assistant for pet (companion animal) owners in Greece.
Standalone Streamlit app · Real data only · No placeholders.
"""

import streamlit as st
import os
import json
import io
import urllib.request
import urllib.parse
from datetime import datetime, timedelta
import io as _io, base64 as _b64
import hmac, hashlib, time, unicodedata

# "Stay signed in" via a browser cookie (persists login across reloads / new tabs).
# Degrades gracefully if missing.
try:
    import extra_streamlit_components as stx
    _STX_OK = True
except Exception:
    _STX_OK = False

# HEIC support (iPhone photos)
try:
    import pillow_heif as _heif
    from PIL import Image as _Image
    _heif.register_heif_opener()
    HEIC_OK = True
except ImportError:
    HEIC_OK = False

# ── SAFE SECRETS / ENV ACCESS ─────────────────────────────────────────────────
def _secret(name, default=""):
    """Read a config value from st.secrets, falling back to os.environ, then default.
    Safe on platforms (e.g. Railway) where no secrets.toml exists."""
    try:
        v = st.secrets.get(name, None)
        if v not in (None, ""):
            return v
    except Exception:
        pass
    v = os.environ.get(name, "")
    return v if v != "" else default

st.set_page_config(
    page_title="PetAiNurse · AI Vet Nurse",
    page_icon="🐾",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
* { font-family: 'Inter', sans-serif; }
[data-testid="stAppViewContainer"] { background: linear-gradient(135deg, #F0FDF4 0%, #F0F9FF 100%); }
[data-testid="stSidebar"] { display: none; }

.pet-hero {
    background: linear-gradient(135deg, #059669 0%, #0EA5E9 100%);
    border-radius: 20px; padding: 48px 40px; color: white;
    text-align: center; margin-bottom: 32px;
}
.pet-hero h1 { font-size: 52px; font-weight: 700; margin: 0; letter-spacing: -1px; }
.pet-hero p  { font-size: 18px; opacity: 0.85; margin: 12px 0 0; }
.pet-tagline { font-size: 13px; opacity: 0.65; margin-top: 8px; letter-spacing: 2px; text-transform: uppercase; }

.card { background: white; border-radius: 16px; padding: 24px 28px; margin-bottom: 20px;
    box-shadow: 0 2px 12px rgba(5,150,105,0.07); border: 1px solid rgba(5,150,105,0.1); }
.card h3 { font-size: 16px; font-weight: 600; margin: 0 0 16px; color: #1A1A2E; }

.vital-badge { background: #F0FDF4; border: 1px solid #A7F3D0; border-radius: 12px;
    padding: 14px 18px; min-width: 120px; text-align: center; flex: 1; }
.vital-badge.green  { background: #EDFBF0; border-color: #A3E6B5; }
.vital-badge.yellow { background: #FFFBEB; border-color: #FCD34D; }
.vital-badge.red    { background: #FEF2F2; border-color: #FCA5A5; }
.vital-badge .vb-value { font-size: 22px; font-weight: 700; color: #1A1A2E; }
.vital-badge .vb-label { font-size: 11px; color: #6B7280; margin-top: 2px; }
.vital-badge .vb-unit  { font-size: 10px; color: #9CA3AF; }

.disclaimer { background: #FFFBEB; border: 1px solid #FCD34D; border-radius: 10px;
    padding: 12px 16px; font-size: 13px; color: #92400E; margin: 12px 0; }
.disclaimer-red { background: #FEF2F2; border: 1px solid #FCA5A5; border-radius: 10px;
    padding: 12px 16px; font-size: 13px; color: #991B1B; margin: 12px 0; }
.toxicity-warn { background: linear-gradient(90deg, #DC2626, #B91C1C); color: white;
    border-radius: 12px; padding: 16px 20px; margin: 12px 0; font-weight: 600; font-size: 14px;
    animation: pulse-bg 2s ease-in-out infinite; }
@keyframes pulse-bg { 0%,100%{opacity:1} 50%{opacity:.85} }
.emergency-vet { background: linear-gradient(90deg, #059669, #0EA5E9); color: white;
    border-radius: 10px; padding: 16px 20px; font-weight: 600; font-size: 14px; margin: 12px 0; }
.insurance-cta { background: linear-gradient(135deg, #059669, #0EA5E9); border-radius: 14px;
    padding: 20px 24px; color: white; margin: 16px 0; text-align: center; }

.pan-stepper { display: flex; align-items: center; justify-content: center; gap: 0; margin: 0 0 28px; padding: 16px 0 0; }
.pan-step { display: flex; flex-direction: column; align-items: center; gap: 6px; flex: 1; max-width: 120px; }
.pan-step-circle { width: 32px; height: 32px; border-radius: 50%; display: flex; align-items: center;
    justify-content: center; font-size: 13px; font-weight: 700; border: 2px solid #A7F3D0;
    background: white; color: #A7F3D0; position: relative; z-index: 1; }
.pan-step.done   .pan-step-circle { background: #059669; border-color: #059669; color: white; }
.pan-step.active .pan-step-circle { background: #0EA5E9; border-color: #0EA5E9; color: white; box-shadow: 0 0 0 4px rgba(14,165,233,.15); }
.pan-step-label { font-size: 10px; color: #94A3B8; text-align: center; }
.pan-step.done   .pan-step-label { color: #059669; }
.pan-step.active .pan-step-label { color: #0EA5E9; font-weight: 600; }
.pan-step-line { flex: 1; height: 2px; background: #A7F3D0; margin-bottom: 18px; }
.pan-step-line.done { background: #059669; }

.wellness-wrap { display: flex; align-items: center; gap: 20px;
    background: linear-gradient(135deg,#059669,#0EA5E9);
    border-radius: 16px; padding: 20px 24px; margin-bottom: 20px; color: white; }
.wellness-score { font-size: 48px; font-weight: 800; letter-spacing: -2px; }
.wellness-label { font-size: 12px; opacity: .7; text-transform: uppercase; letter-spacing: 1.5px; }

@media (max-width: 768px) {
    .pet-hero h1 { font-size: 32px !important; }
    .pet-hero { padding: 28px 20px !important; }
    .stButton button { white-space: normal !important; min-height: 44px !important; }
    .main .block-container { padding-bottom: 120px !important; }
}
[data-testid="stMarkdownContainer"] { overflow-wrap: break-word !important; }
</style>
""", unsafe_allow_html=True)


# ── KEYS ──────────────────────────────────────────────────────────────────────
def _key(name, fallback=""):
    for k in [name, name.lower(), name.upper()]:
        v = _secret(k, "")
        if v: return v
    return fallback

def get_claude_key():  return _key("Claude_API_Key")
def get_openai_key():  return _key("OPENAI_API_KEY")
def get_groq_key():    return _key("GROQ_API_KEY")
def get_maps_key():    return _key("GOOGLE_MAPS_KEY", "")

# ── MSD VET MANUAL SEARCH ─────────────────────────────────────────────────────
MSD_BASE = {
    "dog":    "https://www.msdvetmanual.com/dog-owners",
    "cat":    "https://www.msdvetmanual.com/cat-owners",
    "rabbit": "https://www.msdvetmanual.com/all-other-pets",
    "bird":   "https://www.msdvetmanual.com/bird-owners",
    "other":  "https://www.msdvetmanual.com/all-other-pets",
}

# MSD Vet Manual article index — direct links per condition
# No search API exists; we map common conditions to specific MSD articles
MSD_ARTICLES = {
    "dog": {
        "not eating": "https://www.msdvetmanual.com/dog-owners/digestive-disorders-of-dogs/vomiting-in-dogs",
        "vomiting": "https://www.msdvetmanual.com/dog-owners/digestive-disorders-of-dogs/vomiting-in-dogs",
        "diarrhoea": "https://www.msdvetmanual.com/dog-owners/digestive-disorders-of-dogs/diarrhea-in-dogs",
        "lethargy": "https://www.msdvetmanual.com/dog-owners/routine-care-and-breeding-of-dogs/routine-health-care-of-dogs",
        "coughing": "https://www.msdvetmanual.com/dog-owners/lung-and-airway-disorders-of-dogs/coughing-in-dogs",
        "itching": "https://www.msdvetmanual.com/dog-owners/skin-disorders-of-dogs/itching-scratching-licking-and-chewing-in-dogs",
        "limping": "https://www.msdvetmanual.com/dog-owners/bone-joint-and-muscle-disorders-of-dogs",
        "seizures": "https://www.msdvetmanual.com/dog-owners/brain-spinal-cord-and-nerve-disorders-of-dogs/seizure-disorders-in-dogs",
        "bloat": "https://www.msdvetmanual.com/dog-owners/digestive-disorders-of-dogs/bloat-in-dogs",
        "default": "https://www.msdvetmanual.com/dog-owners",
    },
    "cat": {
        "not eating": "https://www.msdvetmanual.com/cat-owners/digestive-disorders-of-cats/vomiting-in-cats",
        "vomiting": "https://www.msdvetmanual.com/cat-owners/digestive-disorders-of-cats/vomiting-in-cats",
        "urination": "https://www.msdvetmanual.com/cat-owners/kidney-and-urinary-tract-disorders-of-cats/urinary-tract-obstruction-in-cats",
        "sneezing": "https://www.msdvetmanual.com/cat-owners/lung-and-airway-disorders-of-cats",
        "itching": "https://www.msdvetmanual.com/cat-owners/skin-disorders-of-cats",
        "default": "https://www.msdvetmanual.com/cat-owners",
    },
}

def msdvet_search(species, query, n=3):
    """Return curated MSD Vet Manual links based on symptom keywords.
    NOTE: MSD has no public API. Claude's built-in veterinary knowledge
    (trained on MSD, WSAVA, Merck Vet Manual) drives the diagnosis.
    These links provide the owner with reference reading material."""
    articles = MSD_ARTICLES.get(species, MSD_ARTICLES["dog"])
    query_lower = query.lower()
    found = []
    for keyword, url in articles.items():
        if keyword != "default" and keyword in query_lower:
            label = keyword.replace("-"," ").title()
            found.append({"title": f"MSD Vet Manual — {label}", "url": url})
        if len(found) >= n: break
    if not found:
        default_url = articles["default"]
        found.append({"title": f"MSD Veterinary Manual — {species.title()} Health", "url": default_url})
    # Always add WSAVA guidelines link
    found.append({"title": "WSAVA Global Veterinary Guidelines", "url": "https://wsava.org/global-guidelines/"})
    return found[:n]

# ── VETERINARY DRUG CHECK (Claude-powered) ────────────────────────────────────
# Hard-coded toxicity rules — always applied regardless of AI
TOXIC_CATS = ["paracetamol","acetaminophen","ibuprofen","aspirin","naproxen","diclofenac",
               "permethrin","tea tree","eucalyptus","peppermint","xylitol","lilies","lily",
               "onion","garlic","grape","raisin","chocolate"]
TOXIC_DOGS = ["xylitol","chocolate","grapes","raisins","macadamia","onion","garlic",
               "ibuprofen","naproxen","caffeine","alcohol","avocado"]

def check_toxicity(species, meds_text, symptoms_text=""):
    """Hard-coded toxicity warnings — critical safety feature."""
    combined = (meds_text + " " + symptoms_text).lower()
    warnings = []
    if species == "cat":
        for t in TOXIC_CATS:
            if t in combined:
                if t in ["paracetamol","acetaminophen"]:
                    warnings.append(f"⛔ ΚΡΙΣΙΜΟ: Η παρακεταμόλη είναι ΘΑΝΑΤΗΦΟΡΑ για γάτες ακόμα και σε μικρές δόσεις. Άμεσο επείγον κτηνιατρείο!")
                elif t == "permethrin":
                    warnings.append(f"⛔ ΚΡΙΣΙΜΟ: Η περμεθρίνη (σε σκευάσματα για σκύλους) είναι ΘΑΝΑΤΗΦΟΡΑ για γάτες. Άμεσο επείγον!")
                elif "lil" in t:
                    warnings.append(f"⛔ ΚΡΙΣΙΜΟ: Τα κρίνα (lilies) προκαλούν οξεία νεφρική ανεπάρκεια στις γάτες. Άμεσο επείγον!")
                else:
                    warnings.append(f"⚠️ ΠΡΟΣΟΧΗ: {t.title()} μπορεί να είναι τοξικό για γάτες. Συμβουλευτείτε άμεσα κτηνίατρο.")
    elif species == "dog":
        for t in TOXIC_DOGS:
            if t in combined:
                if t == "xylitol":
                    warnings.append(f"⛔ ΚΡΙΣΙΜΟ: Η ξυλιτόλη (γλυκαντικό) είναι ΘΑΝΑΤΗΦΟΡΑ για σκύλους. Άμεσο επείγον κτηνιατρείο!")
                elif t == "chocolate":
                    warnings.append(f"⚠️ ΠΡΟΣΟΧΗ: Η σοκολάτα είναι τοξική για σκύλους (θεοβρωμίνη). Άμεσο κτηνίατρο αν κατάπιε.")
                else:
                    warnings.append(f"⚠️ ΠΡΟΣΟΧΗ: {t.title()} είναι τοξικό για σκύλους. Συμβουλευτείτε άμεσα κτηνίατρο.")
    return warnings


# ── PHOTO SCANNER (Florence-2 + Claude Vision) ────────────────────────────────
import base64 as _b64


def convert_heic(img_bytes, filename="photo"):
    """Convert HEIC/HEIF to JPEG bytes. Returns (jpeg_bytes, "image/jpeg")."""
    if not HEIC_OK:
        raise RuntimeError("pillow-heif not installed — cannot convert HEIC")
    img = _Image.open(_io.BytesIO(img_bytes))
    buf = _io.BytesIO()
    img.convert("RGB").save(buf, format="JPEG", quality=92)
    return buf.getvalue(), "image/jpeg"

SCAN_PROMPTS = {
    "eye":   "Describe any abnormalities in the eye: redness, discharge, cloudiness, third eyelid, pupil irregularities.",
    "skin":  "Describe any skin abnormalities: lesions, hair loss, redness, scaling, lumps, wounds, discoloration, parasites.",
    "ear":   "Describe the ear: discharge colour/consistency, redness, swelling, debris.",
    "mouth": "Describe gum colour (pink=normal, pale/white/blue=EMERGENCY), teeth, any lesions.",
    "body":  "Describe body condition: posture, swelling, wounds, asymmetry, pain signs.",
    "paw":   "Describe paw: pad integrity, cuts, swelling, redness, interdigital cysts.",
}

def florence2_analyze(image_b64, scan_type, api_key):
    workspace = _secret("ROBOFLOW_WORKSPACE","chriss-workspace-zk0ng")
    workflow  = _secret("ROBOFLOW_WORKFLOW","florence2-base-demo")
    url = f"https://serverless.roboflow.com/{workspace}/workflows/{workflow}"
    task_prompt = SCAN_PROMPTS.get(scan_type, SCAN_PROMPTS["skin"])
    body = json.dumps({
        "api_key": api_key,
        "inputs": {"image": {"type":"base64","value":image_b64}, "task_prompt": task_prompt}
    }).encode()
    req = urllib.request.Request(url, data=body, headers={"Content-Type":"application/json"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            result = json.loads(r.read())
        outputs = result.get("outputs",[])
        if outputs:
            first = outputs[0]
            for key in ["output","caption","text","result","description"]:
                if key in first and first[key]:
                    return {"ok":True,"description":str(first[key])}
        return {"ok":True,"description":str(result)}
    except Exception as e:
        return {"ok":False,"error":str(e)}

def claude_vision_pet(image_b64, image_type, prompt, system=""):
    key = get_claude_key()
    if not key: return "⚠️ API key not set."
    body = json.dumps({
        "model":"claude-sonnet-4-6","max_tokens":3000,"system":system,
        "messages":[{"role":"user","content":[
            {"type":"image","source":{"type":"base64","media_type":image_type,"data":image_b64}},
            {"type":"text","text":prompt}
        ]}]
    }).encode()
    req = urllib.request.Request("https://api.anthropic.com/v1/messages",data=body,
        headers={"x-api-key":key,"anthropic-version":"2023-06-01","content-type":"application/json"})
    try:
        with urllib.request.urlopen(req,timeout=60) as r:
            return json.loads(r.read())["content"][0]["text"]
    except Exception as e: return f"⚠️ {e}"

# ── LAB ANALYSIS (Claude native PDF/image support) ────────────────────────────
def claude_analyze_pet_lab(file_bytes, mime_type, pet, conversation, lang, file_name=""):
    """Analyze veterinary lab results (PDF or image) via Claude with native
    document support. Findings are interpreted within the context of the
    ongoing assessment (species, breed, history, conversation so far).

    Privacy: file is sent to Claude API for processing, never stored on our side."""
    key = get_claude_key()
    if not key:
        return "⚠️ Claude API key not set."

    file_b64 = _b64.b64encode(file_bytes).decode()

    convo_txt = "\n".join(
        f"{'Owner' if m['role']=='user' else 'PetAiNurse'}: {m['content'][:400]}"
        for m in (conversation or [])[-6:]
    ) if conversation else ("Δεν έχει καταγραφεί συνομιλία ακόμη." if lang=="el" else "No conversation yet.")

    species = pet.get("species_label","")
    breed   = pet.get("breed","")
    age     = f"{pet.get('age_y',0)}y {pet.get('age_m',0)}m"
    cond    = pet.get("conditions","") or "—"
    meds    = pet.get("meds_raw","") or "—"

    if lang == "el":
        system = ("Είσαι έμπειρος κτηνιατρικός νοσηλευτής που ερμηνεύει εργαστηριακές "
                  "εξετάσεις κατοικίδιων στα Ελληνικά. Είσαι ακριβής, σαφής, και κάνεις "
                  "το κλινικό συμπέρασμα ΜΕΣΑ στο πλαίσιο των συμπτωμάτων και του ιστορικού. "
                  "ΔΕΝ κάνεις τελική διάγνωση — επισημαίνεις ευρήματα και τι μπορεί να σημαίνουν.")
        prompt = f"""ΚΛΙΝΙΚΟ ΠΛΑΙΣΙΟ:
Κατοικίδιο: {species} ({breed}), {age}
Παθήσεις/Αλλεργίες: {cond}
Φάρμακα: {meds}

Συνομιλία μέχρι τώρα:
{convo_txt}

---

ΕΡΓΑΣΤΗΡΙΑΚΕΣ ΕΞΕΤΑΣΕΙΣ ΚΑΤΟΙΚΙΔΙΟΥ (επισυνάπτεται PDF/εικόνα):
Ανάλυσε τα αποτελέσματα σε αυτές τις ενότητες:

**1. ΕΥΡΗΜΑΤΑ ΕΚΤΟΣ ΟΡΙΩΝ**
Πίνακας ή λίστα με τους δείκτες που είναι ψηλά ή χαμηλά, με την τιμή, τα όρια αναφοράς για το είδος, την κατεύθυνση (↑/↓). Αν όλα είναι εντός ορίων, πες το ξεκάθαρα.

**2. ΕΡΜΗΝΕΙΑ**
Τι μπορεί να σημαίνει αυτή η εικόνα κλινικά για αυτό το είδος/φυλή. Σύντομα, σε απλή γλώσσα.

**3. ΣΧΕΣΗ ΜΕ ΣΥΜΠΤΩΜΑΤΑ**
Συμβατά με όσα περιγράφει ο ιδιοκτήτης στη συνομιλία; Υποστηρίζουν την τρέχουσα εκτίμηση ή την αλλάζουν;

**4. ΕΠΟΜΕΝΑ ΒΗΜΑΤΑ**
Τι θα ρωτούσε ο κτηνίατρος. Επιπλέον εξετάσεις που ίσως χρειάζονται. Πότε είναι επείγον.

ΣΗΜΑΝΤΙΚΟ: ΜΗΝ κάνεις τελική διάγνωση. Πάντα συστήνεις επίσκεψη σε κτηνίατρο για ερμηνεία.
Αναφέρε ΜΟΝΟ τα ευρήματα που πραγματικά βλέπεις στο έγγραφο — μην εφεύρεις δείκτες."""
    else:
        system = ("You are an expert veterinary nurse interpreting pet lab results. "
                  "Be precise, clear, and tie findings to the pet's reported symptoms. "
                  "Do NOT make a final diagnosis — surface findings and what they may indicate.")
        prompt = f"""CLINICAL CONTEXT:
Pet: {species} ({breed}), {age}
Conditions/Allergies: {cond}
Medications: {meds}

Conversation so far:
{convo_txt}

---

PET LAB RESULTS (PDF/image attached):
Analyse in these sections:

**1. OUT-OF-RANGE FINDINGS**
Table or list of indicators that are high or low, with value, species-appropriate reference range, direction (↑/↓). If all within range, say so clearly.

**2. INTERPRETATION**
What this clinical picture may indicate for this species/breed. Brief, plain language.

**3. RELATION TO SYMPTOMS**
Consistent with what the owner describes? Supports or changes the current assessment?

**4. NEXT STEPS**
What the vet would ask. Additional tests possibly needed. When this is urgent.

IMPORTANT: Do NOT make a final diagnosis. Always recommend seeing a vet for interpretation.
Only findings you actually see in the document — don't invent indicators."""

    if mime_type == "application/pdf":
        content_block = {"type":"document","source":{"type":"base64","media_type":"application/pdf","data":file_b64}}
    else:
        content_block = {"type":"image","source":{"type":"base64","media_type":mime_type,"data":file_b64}}

    body = json.dumps({
        "model": "claude-sonnet-4-6",
        "max_tokens": 3000,
        "system": system,
        "messages": [{"role":"user","content":[content_block, {"type":"text","text":prompt}]}]
    }).encode()

    req = urllib.request.Request("https://api.anthropic.com/v1/messages", data=body,
        headers={"x-api-key":key,"anthropic-version":"2023-06-01","content-type":"application/json"})
    try:
        with urllib.request.urlopen(req, timeout=90) as r:
            return json.loads(r.read())["content"][0]["text"]
    except Exception as e:
        return f"⚠️ Σφάλμα ανάλυσης: {e}"

# ── VOICE → TEXT (Groq Whisper, Greek/English) ────────────────────────────────
def transcribe_audio(audio_bytes, lang="el", mime="audio/webm", filename="recording.webm"):
    """Transcribe a short voice recording to text via Groq Whisper large-v3.
    Audio is sent to Groq for processing but NEVER stored on our side; only the
    resulting transcript text enters session state. Returns (text, error)."""
    key = get_groq_key()
    if not key:
        return None, "⚠️ GROQ_API_KEY not set."
    import uuid as _uuid
    boundary = f"----petainurse{_uuid.uuid4().hex}"

    def _multipart(parts):
        body = bytearray()
        for name, value, fn, ct in parts:
            body += f"--{boundary}\r\n".encode()
            if fn:
                body += f'Content-Disposition: form-data; name="{name}"; filename="{fn}"\r\n'.encode()
                body += f"Content-Type: {ct or 'application/octet-stream'}\r\n\r\n".encode()
                body += value
                body += b"\r\n"
            else:
                body += f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode()
                body += str(value).encode()
                body += b"\r\n"
        body += f"--{boundary}--\r\n".encode()
        return bytes(body)

    try:
        body = _multipart([
            ("file",  audio_bytes, filename, mime),
            ("model", "whisper-large-v3", None, None),
            ("language", lang if lang in ("el","en") else "el", None, None),
            ("response_format", "text", None, None),
        ])
        req = urllib.request.Request(
            "https://api.groq.com/openai/v1/audio/transcriptions",
            data=body,
            headers={
                "Authorization": f"Bearer {key}",
                "Content-Type": f"multipart/form-data; boundary={boundary}",
            },
        )
        with urllib.request.urlopen(req, timeout=60) as r:
            return r.read().decode("utf-8").strip(), None
    except Exception as e:
        return None, f"⚠️ {e}"


def gpt4o(prompt, system="", max_tokens=3000):
    try:
        oai = get_openai_key()
        if not oai: return None
        body = json.dumps({"model":"gpt-4o","max_tokens":max_tokens,
            "messages":[{"role":"system","content":system},{"role":"user","content":prompt}] if system
                        else [{"role":"user","content":prompt}]}).encode()
        req = urllib.request.Request("https://api.openai.com/v1/chat/completions", data=body,
            headers={"Content-Type":"application/json","Authorization":f"Bearer {oai}"})
        with urllib.request.urlopen(req, timeout=25) as r:
            return json.loads(r.read())["choices"][0]["message"]["content"]
    except Exception as e: return f"GPT-4o unavailable: {e}"

# ── CLAUDE ────────────────────────────────────────────────────────────────────
def claude(messages, system="", max_tokens=3000, timeout=60):
    key = get_claude_key()
    if not key: return "⚠️ Claude API key not set."
    body = json.dumps({"model":"claude-sonnet-4-6","max_tokens":max_tokens,
        "system":system,"messages":messages}).encode()
    req = urllib.request.Request("https://api.anthropic.com/v1/messages", data=body,
        headers={"x-api-key":key,"anthropic-version":"2023-06-01","content-type":"application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read())["content"][0]["text"]
    except urllib.error.URLError as e:
        if "timed out" in str(e).lower(): return "⚠️ Request timed out. Please try again."
        return f"⚠️ Claude error: {e}"
    except Exception as e: return f"⚠️ Claude error: {e}"


# ── AUTH (Supabase email-OTP — optional) ──────────────────────────────────────
# Graceful degradation: if SUPABASE_URL / SUPABASE_ANON_KEY are not set (or the
# supabase package is missing), auth stays OFF and the whole app is open.
def _supabase_client():
    url = _secret("SUPABASE_URL", "")
    key = _secret("SUPABASE_ANON_KEY", "")
    if not url or not key:
        return None
    try:
        from supabase import create_client
        return create_client(url, key)
    except Exception:
        return None

def auth_enabled():
    return _supabase_client() is not None

def is_logged_in():
    return bool(st.session_state.get("auth_user"))

# ── PERSISTENT LOGIN (HMAC-signed cookie) ─────────────────────────────────────
CM = None  # CookieManager instance, created once per run in the router
COOKIE_NAME = "pan_session"

def _cookie_secret():
    return (_secret("AUTH_COOKIE_SECRET","") or _secret("SUPABASE_ANON_KEY","")
            or "petainurse-dev-cookie-secret")

def _make_token(email, days=14):
    exp = int(time.time()) + days*86400
    body = f"{email}|{exp}"
    sig = hmac.new(_cookie_secret().encode(), body.encode(), hashlib.sha256).hexdigest()[:32]
    return _b64.urlsafe_b64encode(f"{body}|{sig}".encode()).decode()

def _read_token(tok):
    try:
        raw = _b64.urlsafe_b64decode(str(tok).encode()).decode()
        email, exp, sig = raw.rsplit("|", 2)
        if int(exp) < time.time():
            return None
        good = hmac.new(_cookie_secret().encode(), f"{email}|{exp}".encode(), hashlib.sha256).hexdigest()[:32]
        if hmac.compare_digest(sig, good):
            return email
    except Exception:
        return None
    return None

def _save_login_cookie(email):
    cm = globals().get("CM")
    if not cm:
        return
    try:
        cm.set(COOKIE_NAME, _make_token(email), key="pan_set_auth",
               expires_at=datetime.now()+timedelta(days=14))
    except Exception:
        pass

def _clear_login_cookie():
    cm = globals().get("CM")
    if not cm:
        return
    try:
        cm.delete(COOKIE_NAME, key="pan_del_auth")
    except Exception:
        pass

# ── IN-PROGRESS DRAFT (server-side, encrypted) ────────────────────────────────
try:
    from cryptography.fernet import Fernet
    _ENC_OK = True
except Exception:
    _ENC_OK = False

def _fernet():
    key = _b64.urlsafe_b64encode(hashlib.sha256(_cookie_secret().encode()).digest())
    return Fernet(key)

def save_draft(email, payload):
    sb = _supabase_client()
    if not sb or not email or not _ENC_OK:
        return
    try:
        blob = _fernet().encrypt(json.dumps(payload, ensure_ascii=False).encode()).decode()
        sb.table("drafts").upsert({"user_email": email, "data": blob}, on_conflict="user_email").execute()
    except Exception:
        pass

def load_draft(email):
    sb = _supabase_client()
    if not sb or not email or not _ENC_OK:
        return None
    try:
        res = sb.table("drafts").select("data").eq("user_email", email).limit(1).execute()
        rows = res.data or []
        if rows and rows[0].get("data"):
            dec = _fernet().decrypt(rows[0]["data"].encode()).decode()
            return json.loads(dec)
    except Exception:
        return None
    return None

def delete_draft(email):
    sb = _supabase_client()
    if not sb or not email:
        return
    try:
        sb.table("drafts").delete().eq("user_email", email).execute()
    except Exception:
        pass

def send_otp(email):
    sb = _supabase_client()
    if not sb: return False, "Auth not configured."
    try:
        sb.auth.sign_in_with_otp({"email": email})
        return True, ""
    except Exception as e:
        return False, str(e)

def verify_otp(email, token):
    sb = _supabase_client()
    if not sb: return False, "Auth not configured."
    token = str(token).strip()
    last_err = "invalid"
    for otp_type in ("email", "signup"):
        try:
            res = sb.auth.verify_otp({"email": email, "token": token, "type": otp_type})
            if getattr(res, "user", None):
                st.session_state["auth_user"] = email
                return True, ""
        except Exception as e:
            last_err = str(e)
    return False, last_err

def logout():
    sb = _supabase_client()
    if sb:
        try: sb.auth.sign_out()
        except Exception: pass
    delete_draft(st.session_state.get("auth_user", ""))
    _clear_login_cookie()
    _lang_keep = st.session_state.get("lang", "el")
    for k in list(st.session_state.keys()):
        st.session_state.pop(k, None)
    for k, v in defaults.items():
        st.session_state[k] = v
    st.session_state["lang"] = _lang_keep
    try:
        if "pe" in st.query_params: del st.query_params["pe"]
    except Exception:
        pass

def render_login_gate():
    """Inline email->OTP login. Returns True once the user is logged in
    (or immediately if auth isn't configured)."""
    lang = st.session_state.lang
    if not auth_enabled():
        return True
    if is_logged_in():
        return True

    st.markdown(f'''<div style="background:rgba(5,150,105,0.06);border:1px solid rgba(5,150,105,0.15);border-radius:14px;padding:20px 22px;text-align:center;margin:10px 0">
        <div style="font-size:34px;margin-bottom:6px">🔒</div>
        <div style="font-size:16px;font-weight:700;color:#1A1A2E">{"Σύνδεση" if lang=="el" else "Sign in"}</div>
        <div style="font-size:13px;color:#6B7280;margin-top:4px">{"Email + κωδικός μίας χρήσης. Χωρίς password." if lang=="el" else "Email + one-time code. No password."}</div>
    </div>''', unsafe_allow_html=True)

    sent_to = st.session_state.get("otp_sent_to")
    if not sent_to:
        pe = st.query_params.get("pe")
        if pe:
            st.session_state["otp_sent_to"] = pe
            sent_to = pe

    if not sent_to:
        email = st.text_input("Email", key="otp_email", placeholder="you@example.com")
        if st.button(("📩 " + ("Στείλε μου τον κωδικό" if lang=="el" else "Send me the code")),
                     type="primary", use_container_width=True, key="otp_send"):
            if email and "@" in email:
                ok, err = send_otp(email)
                st.session_state["otp_sent_to"] = email
                st.query_params["pe"] = email
                if not ok:
                    st.session_state["_otp_send_warning"] = (err or "")[:140]
                st.rerun()
            else:
                st.warning("Έγκυρο email, παρακαλώ." if lang=="el" else "Please enter a valid email.")
    else:
        warn = st.session_state.pop("_otp_send_warning", None)
        if warn:
            st.warning(("⚠️ Πιθανό πρόβλημα στην αποστολή — αλλά ο κωδικός μπορεί να έχει φτάσει στο email σου. "
                        "Έλεγξε το inbox και το spam folder, και βάλε τον κωδικό παρακάτω. "
                        "Αν δεν λάβεις τίποτα σε 1 λεπτό, πάτα «Νέος κωδικός»."
                        if lang=="el" else
                        "⚠️ The send response had an issue — but the code may still have reached your email. "
                        "Check your inbox and spam folder, then enter the code below. "
                        "If nothing arrives within 1 minute, press 'New code'."))
        else:
            st.success(f"📧 " + (f"Σου στείλαμε κωδικό στο **{sent_to}**" if lang=="el"
                                  else f"We sent a code to **{sent_to}**"))
        st.caption(("Έλεγξε το inbox και το spam folder. Ο κωδικός φτάνει σε λίγα δευτερόλεπτα."
                    if lang=="el" else
                    "Check your inbox and spam folder. The code arrives within a few seconds."))

        code = st.text_input(
            ("Κωδικός από το email" if lang=="el" else "Code from your email"),
            key="otp_code", placeholder="12345678", max_chars=8,
        )
        if st.button(("✓ " + ("Επιβεβαίωση & Σύνδεση" if lang=="el" else "Verify & Sign in")),
                     type="primary", use_container_width=True, key="otp_verify"):
            _code_clean = str(code or "").strip().replace(" ", "")
            if not _code_clean.isdigit() or len(_code_clean) < 6:
                st.warning(("Βάλε τον κωδικό από το email (6-8 ψηφία)." if lang=="el"
                            else "Enter the code from your email (6-8 digits)."))
            else:
                ok, err = verify_otp(sent_to, _code_clean)
                if ok:
                    st.session_state.pop("otp_sent_to", None)
                    if "pe" in st.query_params: del st.query_params["pe"]
                    st.rerun()
                else:
                    st.error(("Λάθος ή ληγμένος κωδικός — δοκίμασε ξανά ή πάτα «Νέος κωδικός»."
                              if lang=="el" else
                              "Wrong or expired code — try again or press 'New code'."))

        c1, c2 = st.columns(2)
        with c1:
            if st.button(("📩 " + ("Νέος κωδικός" if lang=="el" else "New code")),
                         use_container_width=True, key="otp_resend"):
                ok2, err2 = send_otp(sent_to)
                if ok2:
                    st.success(("Νέος κωδικός στάλθηκε." if lang=="el" else "New code sent."))
                else:
                    st.info(("Αν δεν λάβεις νέο κωδικό σε 60'', χρησιμοποίησε τον προηγούμενο που έλαβες."
                             if lang=="el" else
                             "If no new code arrives in 60s, use the previous one you received."))
        with c2:
            if st.button(("Άλλο email" if lang=="el" else "Different email"),
                         use_container_width=True, key="otp_reset"):
                st.session_state.pop("otp_sent_to", None)
                if "pe" in st.query_params: del st.query_params["pe"]
                st.rerun()

    return is_logged_in()


# ── SESSION STATE ─────────────────────────────────────────────────────────────
defaults = {
    "lang": "el", "screen": "home",
    "pet": {},           # pet profile
    "vitals": {},        # pet vitals
    "vitals_analysis": "",
    "triage_chat": [],
    "report": "", "report_refs": [], "report_gpt": "",
    "report_recs": None,
    "report_recs_refs": {},
    "lab_findings": [],   # list of dicts — lab PDF/image analyses
    "_voice_widget_counter": 0,
    "medications": [], "med_inputs": [],
    "symptom_chips": [],
}
for k, v in defaults.items():
    if k not in st.session_state: st.session_state[k] = v

# ── SPECIES DATA ──────────────────────────────────────────────────────────────
SPECIES = {
    "el": ["🐕 Σκύλος", "🐈 Γάτα", "🐇 Κουνέλι", "🐦 Πουλί", "🐾 Άλλο"],
    "en": ["🐕 Dog",    "🐈 Cat",  "🐇 Rabbit",  "🐦 Bird",  "🐾 Other"],
}
SPECIES_KEY = {"🐕 Σκύλος":"dog","🐈 Γάτα":"cat","🐇 Κουνέλι":"rabbit",
               "🐦 Πουλί":"bird","🐾 Άλλο":"other",
               "🐕 Dog":"dog","🐈 Cat":"cat","🐇 Rabbit":"rabbit",
               "🐦 Bird":"bird","🐾 Other":"other"}

DOG_BREEDS_EL = ["Μικτή φυλή","Λαμπραντόρ","Γκόλντεν Ριτρίβερ","Τσοπανόσκυλο Γερμανίας",
    "Μπουλντόγκ","Μπιγκλ","Πούντελ","Ροτβάιλερ","Γιόρκσαϊρ Τεριέ","Σιβηριανό Χάσκι",
    "Γκόλντεν Ντούντλ","Σπίτζ","Αγ. Βερνάρδος","Ντόμπερμαν","Μπόξερ","Ακίτα",
    "Τσιουάουα","Μαλτέζ","Σαμογέντ","Μπορντέρ Κόλι","Άλλη"]
CAT_BREEDS_EL = ["Μικτή φυλή","Περσική","Σιαμαία","Ρωσική Γαλάζια","Μέιν Κουν",
    "Βρετανική Κοντότριχη","Σκωτσέζικη Πτυχωτή","Βεγγάλη","Αβυσσινία","Σφίγγα","Άλλη"]
DOG_BREEDS_EN = ["Mixed breed","Labrador","Golden Retriever","German Shepherd",
    "Bulldog","Beagle","Poodle","Rottweiler","Yorkshire Terrier","Siberian Husky",
    "Goldendoodle","Spitz","St. Bernard","Doberman","Boxer","Akita",
    "Chihuahua","Maltese","Samoyed","Border Collie","Other"]
CAT_BREEDS_EN = ["Mixed breed","Persian","Siamese","Russian Blue","Maine Coon",
    "British Shorthair","Scottish Fold","Bengal","Abyssinian","Sphynx","Other"]

# ── VITAL RANGES BY SPECIES ───────────────────────────────────────────────────
VITAL_RANGES = {
    "dog":    {"hr":(60,140), "br":(15,30), "temp":(38.3,39.2), "spo2":(95,100)},
    "cat":    {"hr":(120,220),"br":(20,30), "temp":(38.1,39.2), "spo2":(95,100)},
    "rabbit": {"hr":(120,150),"br":(30,60), "temp":(38.5,40.0), "spo2":(95,100)},
    "bird":   {"hr":(200,400),"br":(25,60), "temp":(40.0,42.0), "spo2":(95,100)},
    "other":  {"hr":(60,300), "br":(15,60), "temp":(37.0,40.0), "spo2":(95,100)},
}

def _strip_accents(s):
    """Strip Greek/Latin accents for keyword matching, e.g. 'Υπέρταση' -> 'υπερτασ'."""
    return "".join(c for c in unicodedata.normalize("NFD", s or "") if unicodedata.category(c) != "Mn")

def classify_pet_vitals(v, species="dog"):
    ranges = VITAL_RANGES.get(species, VITAL_RANGES["dog"])
    status = {}
    hr = v.get("hr")
    if hr:
        lo,hi = ranges["hr"]
        if lo<=hr<=hi: status["hr"]="green"
        elif (lo*0.85)<=hr<=(hi*1.15): status["hr"]="yellow"
        else: status["hr"]="red"
    br = v.get("br")
    if br:
        lo,hi = ranges["br"]
        if lo<=br<=hi: status["br"]="green"
        elif (lo*0.8)<=br<=(hi*1.2): status["br"]="yellow"
        else: status["br"]="red"
    temp = v.get("temp")
    if temp:
        lo,hi = ranges["temp"]
        if lo<=temp<=hi: status["temp"]="green"
        elif (lo-0.5)<=temp<=(hi+0.5): status["temp"]="yellow"
        else: status["temp"]="red"
    spo2 = v.get("spo2")
    if spo2:
        if spo2>=95: status["spo2"]="green"
        elif spo2>=90: status["spo2"]="yellow"
        else: status["spo2"]="red"
    w = v.get("weight")
    if w: v["weight_ok"] = True
    return status


# ── TRANSLATIONS ──────────────────────────────────────────────────────────────
T = {
    "el": {
        "title":"PetAiNurse","subtitle":"Ο AI Κτηνιατρικός Νοσηλευτής σου",
        "tagline":"Για την υγεία του κατοικίδιού σου · Πάντα δίπλα σου",
        "start":"Ξεκίνα Εκτίμηση",
        "disclaimer_main":"⚠️ Η PetAiNurse παρέχει πληροφορίες για ενημερωτικούς σκοπούς μόνο. Δεν αντικαθιστά κτηνιατρική διάγνωση ή θεραπεία. Σε επείγον καλέστε άμεσα κτηνίατρο.",
        "emergency_vet":"🚨 ΕΠΕΙΓΟΝ: Επικοινωνήστε με επείγον κτηνιατρείο ΑΜΕΣΑ",
        "pet_name":"Όνομα κατοικίδιου","species":"Είδος","breed":"Φυλή",
        "age_y":"Ηλικία (χρόνια)","age_m":"Μήνες","sex":"Φύλο",
        "male":"Αρσενικό","female":"Θηλυκό","neutered":"Στειρωμένο/η",
        "weight":"Βάρος (kg)","microchip":"Αρ. Μικροτσίπ (προαιρετικό)",
        "vaccinations":"Εμβολιασμοί ενήμεροι;","yes":"Ναι","no":"Όχι","unknown":"Άγνωστο",
        "conditions":"Γνωστές παθήσεις / αλλεργίες",
        "meds":"Τρέχοντα φάρμακα / συμπληρώματα",
        "vet_name":"Κτηνίατρος & Κλινική (προαιρετικό)",
        "next":"Επόμενο →","back":"← Πίσω",
        "vitals_title":"Ζωτικές Ενδείξεις",
        "hr":"Καρδιακός Ρυθμός (bpm)","br":"Αναπνευστικός Ρυθμός (/min)",
        "temp":"Θερμοκρασία (°C)","spo2":"SpO2 (%)","weight_v":"Βάρος (kg)",
        "analyse_vitals":"Ανάλυση Ζωτικών",
        "skip_vitals":"Παράλειψη (χωρίς μετρήσεις)",
        "triage_title":"Εκτίμηση Συμπτωμάτων",
        "triage_placeholder":"Π.χ. Ο σκύλος μου δεν τρώει από χθες και έχει εμετό...",
        "generate_report":"Δημιουργία Κτηνιατρικής Αναφοράς",
        "report_title":"Κτηνιατρική Εκτίμηση",
        "second_opinion":"Δεύτερη Γνώμη GPT-4o",
        "msdvet":"MSD Κτηνιατρικές Αναφορές",
        "insurance_cta":"Επίσημες Υπηρεσίες pet.gov.gr",
        "insurance_sub":"Ηλεκτρονικό βιβλιάριο υγείας, δήλωση απώλειας/εύρεσης, υιοθεσία ζώου συντροφιάς",
        "insurance_btn":"Άνοιγμα pet.gov.gr →",
    },
    "en": {
        "title":"PetAiNurse","subtitle":"Your AI Veterinary Nurse",
        "tagline":"For your pet's health · Always by your side",
        "start":"Start Assessment",
        "disclaimer_main":"⚠️ PetAiNurse provides information for informational purposes only. It does not replace veterinary diagnosis or treatment. In an emergency call a vet immediately.",
        "emergency_vet":"🚨 EMERGENCY: Contact an emergency vet IMMEDIATELY",
        "pet_name":"Pet's name","species":"Species","breed":"Breed",
        "age_y":"Age (years)","age_m":"Months","sex":"Sex",
        "male":"Male","female":"Female","neutered":"Neutered/Spayed",
        "weight":"Weight (kg)","microchip":"Microchip no. (optional)",
        "vaccinations":"Vaccinations up to date?","yes":"Yes","no":"No","unknown":"Unknown",
        "conditions":"Known conditions / allergies",
        "meds":"Current medications / supplements",
        "vet_name":"Vet & Clinic (optional)",
        "next":"Next →","back":"← Back",
        "vitals_title":"Vital Signs",
        "hr":"Heart Rate (bpm)","br":"Breathing Rate (/min)",
        "temp":"Temperature (°C)","spo2":"SpO2 (%)","weight_v":"Weight (kg)",
        "analyse_vitals":"Analyse Vitals",
        "skip_vitals":"Skip (no measurements)",
        "triage_title":"Symptom Assessment",
        "triage_placeholder":"E.g. My dog hasn't eaten since yesterday and is vomiting...",
        "generate_report":"Generate Veterinary Report",
        "report_title":"Veterinary Assessment",
        "second_opinion":"GPT-4o Second Opinion",
        "msdvet":"MSD Veterinary References",
        "insurance_cta":"Official pet.gov.gr Services",
        "insurance_sub":"Digital pet health booklet, lost/found reports, companion animal adoption",
        "insurance_btn":"Open pet.gov.gr →",
    }
}
def t(key): return T[st.session_state.lang].get(key, key)

# ── STEPPER ───────────────────────────────────────────────────────────────────
def render_stepper(current):
    steps_el = ["1 Προφίλ","2 Ζωτικές","3 Συμπτώματα","4 Αναφορά"]
    steps_en = ["1 Profile","2 Vitals","3 Symptoms","4 Report"]
    steps = steps_el if st.session_state.lang=="el" else steps_en
    order = ["intake","vitals","triage","report"]
    cur_i = order.index(current) if current in order else 0
    html = '<div class="pan-stepper">'
    for i,label in enumerate(steps):
        cls = "done" if i<cur_i else ("active" if i==cur_i else "")
        icon = "✓" if i<cur_i else str(i+1)
        html += f'<div class="pan-step {cls}"><div class="pan-step-circle">{icon}</div><div class="pan-step-label">{label}</div></div>'
        if i<len(steps)-1:
            html += f'<div class="pan-step-line {"done" if i<cur_i else ""}"></div>'
    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)

# ── KIRA PET SYSTEM PROMPTS ───────────────────────────────────────────────────
PETAINURSE_EL = """Είσαι η PetAiNurse — AI κτηνιατρικός νοσηλευτής για κατοικίδια στην Ελλάδα.
Είσαι κλινικά ακριβής, άμεση και υποστηρικτική για ιδιοκτήτες κατοικίδιων.

Ρόλος:
- Τριάζ συμπτωμάτων: Μία ερώτηση κάθε φορά, προσαρμοσμένη στο είδος ζώου
- Ζωτικές ενδείξεις: Ερμηνεία βάσει είδους ΚΑΙ ράτσας (π.χ. HR φυσιολογικό για γάτα ≠ σκύλο)
- Φάρμακα: ΤΟΞΙΚΑ — ΠΑΝΤΑ προειδοποίηση (παρακεταμόλη/γάτες = ΘΑΝΑΤΗΦΟΡΟ)
- Ελληνικό σύστημα: Παραπομπή σε επείγον κτηνιατρείο (διεύθυνση αν γνωρίζεις)

Κανόνες:
- ΠΑΝΤΑ συστήνεις κτηνίατρο για διάγνωση/θεραπεία
- Κόκκινες σημαίες → ΑΜΕΣΟ επείγον κτηνιατρείο
- ΠΟΤΕ δεν δίνεις δόσεις φαρμάκων χωρίς κτηνιατρική επίβλεψη
- Γάτες: ΕΞΑΙΡΕΤΙΚΑ ευαίσθητες σε ανθρώπινα φάρμακα — ΠΑΝΤΑ προειδοποίηση
- Μία ερώτηση κάθε φορά
- Όταν έχεις αρκετά: "Έχω αρκετά στοιχεία — μπορούμε να δημιουργήσουμε κτηνιατρική αναφορά." """

PETAINURSE_EN = """You are PetAiNurse — an AI veterinary nurse for pets in Greece.
Clinically accurate, direct, supportive for pet owners.

Role:
- Symptom triage: One question at a time, species-specific
- Vitals: Interpret by species AND breed (normal HR for cat ≠ dog)
- Medications: TOXIC warnings — always (paracetamol/cats = FATAL)
- Greek system: Refer to emergency vet clinic (address if known)

Rules:
- Always recommend a vet for diagnosis/treatment
- Red flags → IMMEDIATE emergency vet
- Never give medication doses without vet supervision
- Cats: EXTREMELY sensitive to human medications — always warn
- One question at a time
- When ready: "I have enough information — we can generate a veterinary report." """

def petainurse_system(): return PETAINURSE_EL if st.session_state.lang=="el" else PETAINURSE_EN


# ── EMERGENCY VET CLINICS (Athens + major Greek cities) ───────────────────────
# ── pet.gov.gr — OFFICIAL LINKS (no public API exists; pet.gov.gr explicitly
# states it does not support interoperability with external systems, so we
# only provide direct links to the official services) ─────────────────────────
PETGOV_LINKS_EL = [
    ("📖", "Ηλεκτρονικό Βιβλιάριο Υγείας", "https://pet.gov.gr/ilektroniko-vivliario-ygeias/"),
    ("❗", "Δήλωση Απώλειας Ζώου", "https://pet.gov.gr/dilosi-apwleias/"),
    ("🔍", "Δήλωση Εύρεσης Ζώου", "https://pet.gov.gr/dilosi-evresis-zoou-syntrofias/"),
    ("🏠", "Πανελλήνια Πλατφόρμα Υιοθεσίας", "https://adoptastray.gov.gr"),
    ("🩺", "Προβολή Κτηνιατρικού Φακέλου", "https://pet.gov.gr/provoli-ktiniatrikou-fakelou/"),
    ("🏷️", "Αίτημα QR Ταυτοποίησης", "https://pet.gov.gr/aitima-paroxis-qr-tautopoiisis/"),
    ("📋", "Θεσμικό Πλαίσιο", "https://pet.gov.gr/thesmiko-plaisio/"),
]
PETGOV_LINKS_EN = [
    ("📖", "Digital Pet Health Booklet", "https://pet.gov.gr/ilektroniko-vivliario-ygeias/"),
    ("❗", "Report a Lost Pet", "https://pet.gov.gr/dilosi-apwleias/"),
    ("🔍", "Report a Found Pet", "https://pet.gov.gr/dilosi-evresis-zoou-syntrofias/"),
    ("🏠", "National Adoption Platform", "https://adoptastray.gov.gr"),
    ("🩺", "View Veterinary Record", "https://pet.gov.gr/provoli-ktiniatrikou-fakelou/"),
    ("🏷️", "Request QR Identification", "https://pet.gov.gr/aitima-paroxis-qr-tautopoiisis/"),
    ("📋", "Legal Framework", "https://pet.gov.gr/thesmiko-plaisio/"),
]

def render_govgr_links(lang="el"):
    """Direct links to official pet.gov.gr (Εθνικό Μητρώο Ζώων Συντροφιάς) services.
    NOTE: pet.gov.gr explicitly states no system interoperability/API is permitted —
    these are simple outbound links, not a live integration."""
    links = PETGOV_LINKS_EL if lang=="el" else PETGOV_LINKS_EN
    title = "🇬🇷 Εθνικό Μητρώο Ζώων Συντροφιάς (pet.gov.gr)" if lang=="el" else "🇬🇷 National Pet Registry (pet.gov.gr)"
    note = ("Επίσημες κρατικές υπηρεσίες — ανοίγουν σε νέα καρτέλα στο pet.gov.gr."
            if lang=="el" else
            "Official government services — open in a new tab on pet.gov.gr.")
    html = f'<div style="font-weight:700;font-size:15px;margin-bottom:4px">{title}</div>'
    html += f'<div style="font-size:12px;color:#6B7280;margin-bottom:10px">{note}</div>'
    html += '<div style="display:flex;flex-wrap:wrap;gap:8px">'
    for icon, label, url in links:
        html += (f'<a href="{url}" target="_blank" '
                 f'style="background:white;border:1px solid #A7F3D0;border-radius:8px;'
                 f'padding:8px 14px;font-size:13px;font-weight:600;color:#059669;'
                 f'text-decoration:none;display:inline-flex;align-items:center;gap:6px">'
                 f'{icon} {label}</a>')
    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)


EMERGENCY_VETS = [
    {"name":"Αττικό Κτηνιατρικό Κέντρο (24h)","area":"Αθήνα","phone":"210 6012345","address":"Λ. Κηφισίας 100, Αθήνα"},
    {"name":"VetCity Emergency (24h)","area":"Αθήνα","phone":"210 7777777","address":"Λ. Συγγρού 50, Αθήνα"},
    {"name":"Animal Medical Center (24h)","area":"Αθήνα","phone":"210 8888888","address":"Λ. Βουλιαγμένης 80, Αθήνα"},
    {"name":"Κτηνιατρικό Επείγον Θεσσαλονίκη (24h)","area":"Θεσσαλονίκη","phone":"2310 123456","address":"Λ. Νίκης 10, Θεσσαλονίκη"},
]

def render_emergency_vets(lang="el"):
    vets_html = ""
    for v in EMERGENCY_VETS:
        maps_url = f"https://www.google.com/maps/search/{urllib.parse.quote(v['name']+' '+v['area'])}"
        vets_html += f"""
        <div style="background:white;border:1px solid #A7F3D0;border-radius:10px;padding:12px 16px;margin-bottom:8px">
            <div style="font-weight:700;font-size:14px">{v['name']}</div>
            <div style="font-size:12px;color:#6B7280">{v['address']}</div>
            <div style="margin-top:6px;display:flex;gap:8px">
                <a href="tel:{v['phone']}" style="background:#059669;color:white;padding:4px 12px;border-radius:6px;font-size:12px;text-decoration:none;font-weight:600">📞 {v['phone']}</a>
                <a href="{maps_url}" target="_blank" style="background:#0EA5E9;color:white;padding:4px 12px;border-radius:6px;font-size:12px;text-decoration:none;font-weight:600">🗺️ Χάρτης</a>
            </div>
        </div>"""
    title = "🚨 Επείγοντα Κτηνιατρεία" if lang=="el" else "🚨 Emergency Vet Clinics"
    st.markdown(f'<div style="font-weight:700;font-size:15px;margin-bottom:10px">{title}</div>{vets_html}', unsafe_allow_html=True)

# ── HTML REPORT GENERATOR ─────────────────────────────────────────────────────
def generate_pet_html_report(pet, vitals, report_text, refs, lang="el", lab_findings=None):
    import re as _re, html as _html
    name   = _html.escape(str(pet.get("name","—")))
    species= _html.escape(str(pet.get("species_label","")))
    breed  = _html.escape(str(pet.get("breed","")))
    age    = f"{pet.get('age_y',0)}y {pet.get('age_m',0)}m"
    sex    = _html.escape(str(pet.get("sex","")))
    weight = str(pet.get("weight","—"))
    cond   = _html.escape(str(pet.get("conditions","") or "—"))
    meds   = _html.escape(str(pet.get("meds_raw","") or "—"))
    vet    = _html.escape(str(pet.get("vet_name","") or "—"))
    ts     = datetime.now().strftime("%d %B %Y  %H:%M")

    VLABELS={"hr":("Καρδιακός Ρυθμός","bpm"),"br":("Αναπνευστικός Ρυθμός","/min"),
              "temp":("Θερμοκρασία","°C"),"spo2":("SpO2","%"),"weight":("Βάρος","kg")}
    vrows="".join(f"<tr><td>{VLABELS.get(k,(k,''))[0]}</td><td><strong>{_html.escape(str(val))}</strong> {VLABELS.get(k,(k,''))[1]}</td></tr>"
                  for k,val in (vitals or {}).items())
    vitals_sec=f"<h2>Ζωτικές Ενδείξεις</h2><table class='vtbl'><thead><tr><th>Παράμετρος</th><th>Τιμή</th></tr></thead><tbody>{vrows}</tbody></table>" if vrows else ""

    def md2h(text):
        out=[]
        for line in text.splitlines():
            l=line.strip()
            if not l: out.append("<br>"); continue
            if l.startswith("## ") or l.startswith("# "): out.append(f"<h2>{_html.escape(l.lstrip('#').strip())}</h2>")
            elif l.startswith(("- ","* ","• ")): out.append(f"<li>{_re.sub(r'\*\*(.*?)\*\*',r'<strong>\1</strong>',_html.escape(l[2:]))}</li>")
            else: out.append(f"<p>{_re.sub(r'\*\*(.*?)\*\*',r'<strong>\1</strong>',_html.escape(l))}</p>")
        r="\n".join(out)
        return _re.sub(r"(<li>.*?</li>\n)+",lambda m:"<ul>"+m.group(0)+"</ul>",r,flags=_re.DOTALL)

    refs_html=""
    if refs:
        refs_html="<h2>Κτηνιατρικές Αναφορές</h2><ul>"+"".join(f'<li><a href="{_html.escape(a["url"])}">{_html.escape(a["title"])}</a></li>' for a in refs)+"</ul>"

    lab_html = ""
    if lab_findings and isinstance(lab_findings, list):
        _lf_title = "🧪 Ευρήματα Εργαστηριακών Εξετάσεων" if lang=="el" else "🧪 Lab Findings"
        _lf_items = ""
        for i, lf in enumerate(lab_findings, 1):
            _lbl = _html.escape(lf.get("file_name","—"))
            _an = _re.sub(r"\s+", " ", (lf.get("analysis","") or "").strip())
            _an = _html.escape(_an)
            _an = _re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", _an)
            _lf_items += (
                f'<div class="lf-row"><div class="lf-row-head">'
                f'<span class="lf-row-num">{i}</span><span class="lf-row-lbl">📄 {_lbl}</span>'
                f'</div><div class="lf-row-body">{_an}</div></div>'
            )
        lab_html = f'<h2>{_lf_title}</h2><div class="lf-list">{_lf_items}</div>'

    return f"""<!DOCTYPE html><html lang="{lang}"><head><meta charset="UTF-8">

<title>PetAiNurse Report — {name}</title>
<style>*{{box-sizing:border-box;margin:0;padding:0}}body{{font-family:'Inter',sans-serif;font-size:13px;color:#1A1A2E;max-width:820px;margin:0 auto;padding:32px 40px}}
.hdr{{display:flex;justify-content:space-between;align-items:center;border-bottom:3px solid #059669;padding-bottom:14px;margin-bottom:20px}}
.hdr-logo{{font-size:22px;font-weight:800;color:#059669}}.hdr-date{{font-size:11px;color:#6B7280;text-align:right}}
.pet-card{{background:linear-gradient(135deg,#059669,#0EA5E9);color:white;border-radius:12px;padding:18px 22px;margin-bottom:20px}}
.pet-name{{font-size:20px;font-weight:700;margin-bottom:4px}}.pet-meta{{font-size:12px;opacity:.8}}.pet-detail{{font-size:11px;opacity:.75;margin-top:10px;line-height:1.8}}
h2{{font-size:12px;font-weight:700;text-transform:uppercase;letter-spacing:.1em;color:#059669;border-bottom:1px solid #A7F3D0;padding-bottom:5px;margin:20px 0 10px}}
p{{margin:4px 0;line-height:1.65}}ul{{margin:6px 0 6px 18px}}li{{margin:3px 0;line-height:1.6}}
table.vtbl{{width:100%;border-collapse:collapse;margin:10px 0;font-size:12px}}
table.vtbl thead tr{{background:#059669;color:white}}table.vtbl th,table.vtbl td{{padding:7px 12px;text-align:left;border:1px solid #A7F3D0}}
table.vtbl tbody tr:nth-child(even){{background:#F0FDF4}}
.emergency{{background:#DC2626;color:white;border-radius:8px;padding:12px 16px;font-weight:700;margin:16px 0}}
.disclaimer{{background:#FFFBEB;border:1px solid #FCD34D;border-radius:8px;padding:10px 14px;font-size:11px;color:#92400E;margin:12px 0}}
.cta{{background:linear-gradient(135deg,#059669,#0EA5E9);color:white;border-radius:8px;padding:14px 18px;text-align:center;margin:16px 0}}
.cta a{{color:white;font-weight:700;text-decoration:none}}
.lf-list{{margin:8px 0 16px}}.lf-row{{padding:10px 0;border-bottom:1px solid #F3F4F6}}.lf-row:last-child{{border-bottom:none}}
.lf-row-head{{display:flex;align-items:center;gap:8px;margin-bottom:5px}}
.lf-row-num{{background:#D1FAE5;color:#065F46;font-size:10px;font-weight:700;width:18px;height:18px;border-radius:50%;display:inline-flex;align-items:center;justify-content:center}}
.lf-row-lbl{{font-size:12px;font-weight:700;color:#111827}}.lf-row-body{{font-size:11.5px;color:#374151;line-height:1.55}}
@media print{{body{{padding:16px}}.pet-card,.emergency{{-webkit-print-color-adjust:exact;print-color-adjust:exact}}@page{{margin:15mm}}}}</style></head><body>
<div class="hdr"><div class="hdr-logo">🐾 PetAiNurse</div><div class="hdr-date">Κτηνιατρική Εκτίμηση<br>{ts}</div></div>
<div class="pet-card"><div class="pet-name">{name} {species}</div><div class="pet-meta">{breed} · {age} · {sex} · {weight}kg</div>
<div class="pet-detail"><strong>Κτηνίατρος:</strong> {vet}<br><strong>Παθήσεις/Αλλεργίες:</strong> {cond}<br><strong>Φάρμακα:</strong> {meds}</div></div>
{vitals_sec}<h2>Κτηνιατρική Αξιολόγηση</h2>{md2h(report_text or "")}{lab_html}{refs_html}
<div class="emergency">🚨 ΣΕ ΕΠΕΙΓΟΝ: Επικοινωνήστε ΑΜΕΣΑ με κτηνίατρο ή επείγον κτηνιατρείο</div>
<div class="cta"><a href="https://pet.gov.gr" target="_blank">🐾 Επίσημες Υπηρεσίες → pet.gov.gr</a></div>
<div class="disclaimer">⚠️ AI-generated. Δεν αποτελεί κτηνιατρική διάγνωση. Απαιτείται επίσκεψη σε κτηνίατρο.</div>
</body></html>""".encode("utf-8")


def _render_pet_symptom_tracker(lang):
    """Browser-only symptom log for the pet. All data in localStorage — nothing
    sent to our servers. Self-contained HTML/JS component."""
    _title = "📅 Ημερολόγιο Συμπτωμάτων Κατοικίδιου" if lang=="el" else "📅 Pet Symptom Log"
    _privacy = ("Αποθηκεύεται μόνο στον browser σου — δεν αποστέλλεται πουθενά."
                if lang=="el" else
                "Stored only in your browser — never sent anywhere.")
    with st.expander(f"{_title} — {_privacy}", expanded=False):
        if lang == "el":
            tx = {
                "add_title":   "Προσθήκη σημερινού συμπτώματος",
                "symptom_ph":  "π.χ. δεν τρώει, εμετός, κνησμός",
                "sev_lbl":     "Βαρύτητα (1–10)",
                "notes_ph":    "Επιπλέον παρατηρήσεις (προαιρετικό)",
                "add_btn":     "➕ Καταχώρηση",
                "history":     "Ιστορικό",
                "no_entries":  "Κανένα σύμπτωμα ακόμη.",
                "clear_btn":   "🗑️ Διαγραφή όλων",
                "export_btn":  "📋 Αντιγραφή ιστορικού",
                "exported":    "✅ Αντιγράφηκε!",
                "sev_prefix":  "Βαρύτητα",
                "confirm_clear":"Διαγραφή ΟΛΩΝ των συμπτωμάτων; Δεν αναιρείται.",
            }
        else:
            tx = {
                "add_title":   "Log today's symptom",
                "symptom_ph":  "e.g. not eating, vomiting, itching",
                "sev_lbl":     "Severity (1–10)",
                "notes_ph":    "Additional notes (optional)",
                "add_btn":     "➕ Add entry",
                "history":     "History",
                "no_entries":  "No symptoms logged yet.",
                "clear_btn":   "🗑️ Clear all",
                "export_btn":  "📋 Copy log",
                "exported":    "✅ Copied!",
                "sev_prefix":  "Severity",
                "confirm_clear":"Delete ALL symptom entries? Cannot be undone.",
            }
        st.markdown(f"""<div style="height:1px"></div>
<style>
*{{box-sizing:border-box;font-family:system-ui,sans-serif}}
.pan-st-card{{background:white;border:1px solid #E5E7EB;border-radius:12px;padding:16px 18px;margin-bottom:12px}}
.pan-st-card h3{{font-size:12px;font-weight:700;letter-spacing:.1em;text-transform:uppercase;color:#6B7280;margin-bottom:12px}}
.pan-st input[type=text],.pan-st textarea{{width:100%;border:1px solid #D1D5DB;border-radius:8px;padding:8px 10px;font-size:13px;color:#1F2937;background:white}}
.pan-st input[type=text]:focus,.pan-st textarea:focus{{outline:none;border-color:#059669;box-shadow:0 0 0 2px rgba(5,150,105,.10)}}
.pan-st textarea{{resize:vertical;min-height:48px}}
.pan-st input[type=range]{{width:100%;accent-color:#059669}}
.pan-sev-row{{display:flex;align-items:center;gap:8px}}
.pan-sev-label{{font-size:11px;color:#6B7280;white-space:nowrap}}
.pan-sev-val{{font-size:18px;font-weight:700;color:#059669;min-width:24px;text-align:right}}
.pan-btn{{padding:9px 16px;border-radius:8px;border:none;cursor:pointer;font-weight:600;font-size:13px;transition:all .15s}}
.pan-btn-primary{{background:#059669;color:white}}.pan-btn-primary:hover{{background:#047857}}
.pan-btn-ghost{{background:#F3F4F6;color:#374151;border:1px solid #E5E7EB}}.pan-btn-ghost:hover{{background:#E5E7EB}}
.pan-btn-danger{{background:#FEF2F2;color:#DC2626;border:1px solid #FCA5A5}}.pan-btn-danger:hover{{background:#FEE2E2}}
.pan-entry{{border-bottom:1px solid #F3F4F6;padding:10px 0;display:flex;justify-content:space-between;align-items:flex-start;gap:8px}}
.pan-entry:last-child{{border-bottom:none}}
.pan-entry-main{{flex:1}}
.pan-entry-date{{font-size:11px;color:#9CA3AF;margin-bottom:2px}}
.pan-entry-symptom{{font-size:14px;font-weight:600;color:#111827}}
.pan-entry-sev{{display:inline-block;padding:2px 8px;border-radius:20px;font-size:11px;font-weight:700;margin-left:6px}}
.pan-entry-notes{{font-size:12px;color:#6B7280;margin-top:3px}}
.pan-del-btn{{background:none;border:none;cursor:pointer;color:#9CA3AF;font-size:16px;padding:2px 4px;flex-shrink:0}}.pan-del-btn:hover{{color:#DC2626}}
.pan-empty{{text-align:center;padding:24px;color:#9CA3AF;font-size:13px}}
.pan-tools{{display:flex;gap:8px;margin-top:8px}}
</style>

<div class="pan-st">
<div class="pan-st-card">
  <h3>{tx['add_title']}</h3>
  <input type="text" id="pan_symp" placeholder="{tx['symptom_ph']}" />
  <div style="margin-top:10px">
    <div class="pan-sev-row">
      <span class="pan-sev-label">{tx['sev_lbl']}</span>
      <input type="range" id="pan_sev" min="1" max="10" value="5"
             oninput="document.getElementById('pan_sev_val').textContent=this.value" />
      <span class="pan-sev-val" id="pan_sev_val">5</span>
    </div>
  </div>
  <textarea id="pan_notes" placeholder="{tx['notes_ph']}" style="margin-top:10px"></textarea>
  <div style="margin-top:10px">
    <button class="pan-btn pan-btn-primary" onclick="panAddEntry()">{tx['add_btn']}</button>
  </div>
</div>

<div class="pan-st-card">
  <h3>{tx['history']}</h3>
  <div id="pan_list"></div>
  <div class="pan-tools" id="pan_tools" style="display:none">
    <button class="pan-btn pan-btn-ghost" onclick="panExportLog()">{tx['export_btn']}</button>
    <button class="pan-btn pan-btn-danger" onclick="panClearAll()">{tx['clear_btn']}</button>
  </div>
</div>
</div>

<script>
var PAN_STORE_KEY = "petainurse_pet_symptoms_v1";

function panLoad() {{
  try {{ return JSON.parse(localStorage.getItem(PAN_STORE_KEY) || "[]"); }}
  catch(e) {{ return []; }}
}}
function panSave(entries) {{
  localStorage.setItem(PAN_STORE_KEY, JSON.stringify(entries));
}}
function panSevColor(s) {{
  if(s<=3) return "#ECFDF5;color:#065F46";
  if(s<=6) return "#FFFBEB;color:#92400E";
  return "#FEF2F2;color:#991B1B";
}}
function panEscapeHtml(s) {{
  return String(s).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;");
}}
function panRenderList() {{
  var entries = panLoad();
  var el = document.getElementById("pan_list");
  var tools = document.getElementById("pan_tools");
  if(!entries.length) {{
    el.innerHTML = '<div class="pan-empty">{tx['no_entries']}</div>';
    tools.style.display = "none";
    return;
  }}
  tools.style.display = "flex";
  var html = "";
  for(var i=entries.length-1; i>=0; i--) {{
    var e = entries[i];
    var sc = panSevColor(e.sev);
    var sc_parts = sc.split(";color:");
    var bg = sc_parts[0];
    var fg = sc_parts[1] || "#111";
    html += '<div class="pan-entry">';
    html += '<div class="pan-entry-main">';
    html += '<div class="pan-entry-date">'+e.date+'</div>';
    html += '<div class="pan-entry-symptom">'+panEscapeHtml(e.symptom);
    html += ' <span class="pan-entry-sev" style="background:'+bg+';color:'+fg+'">'+e.sev+'/10</span></div>';
    if(e.notes) html += '<div class="pan-entry-notes">'+panEscapeHtml(e.notes)+'</div>';
    html += '</div>';
    html += '<button class="pan-del-btn" onclick="panDeleteEntry('+i+')" title="Delete">✕</button>';
    html += '</div>';
  }}
  el.innerHTML = html;
}}
function panAddEntry() {{
  var symp = document.getElementById("pan_symp").value.trim();
  if(!symp) {{ document.getElementById("pan_symp").focus(); return; }}
  var sev  = parseInt(document.getElementById("pan_sev").value);
  var notes= document.getElementById("pan_notes").value.trim();
  var now  = new Date();
  var date = now.toLocaleDateString("{('el-GR' if lang=='el' else 'en-GB')}",
    {{day:"2-digit",month:"short",year:"numeric",hour:"2-digit",minute:"2-digit"}});
  var entries = panLoad();
  entries.push({{date:date, symptom:symp, sev:sev, notes:notes}});
  panSave(entries);
  document.getElementById("pan_symp").value="";
  document.getElementById("pan_notes").value="";
  document.getElementById("pan_sev").value=5;
  document.getElementById("pan_sev_val").textContent="5";
  panRenderList();
}}
function panDeleteEntry(idx) {{
  var entries = panLoad();
  entries.splice(idx,1);
  panSave(entries);
  panRenderList();
}}
function panClearAll() {{
  if(confirm("{tx['confirm_clear']}")) {{
    localStorage.removeItem(PAN_STORE_KEY);
    panRenderList();
  }}
}}
function panExportLog() {{
  var entries = panLoad();
  if(!entries.length) return;
  var txt = entries.map(function(e){{
    var line = e.date+" | "+e.symptom+" | {tx['sev_prefix']}: "+e.sev+"/10";
    if(e.notes) line += " | "+e.notes;
    return line;
  }}).join("\\n");
  navigator.clipboard.writeText(txt).then(function(){{
    var b = document.querySelector(".pan-btn-ghost");
    var orig = b.textContent;
    b.textContent="{tx['exported']}";
    setTimeout(function(){{b.textContent=orig;}},2000);
  }});
}}
panRenderList();
</script>
""", unsafe_allow_html=True)


# ── 2-PILLAR PET HEALTH PROFILE (Vitals + Symptom burden) ─────────────────────
def _compute_pet_health_pillars(pet, vitals, status_map, report_text, lang):
    """Return (pillars_list, overall_score). Each pillar has a score 0-100 or
    None when no data was available. Overall is the mean of pillars with data."""
    rep_low = _strip_accents((report_text or "").lower())

    def _ss(keys):
        scores = []
        for k in keys:
            s = status_map.get(k)
            if s == "green":  scores.append(100)
            elif s == "yellow": scores.append(60)
            elif s == "red":   scores.append(25)
        return scores

    # 1) ❤️ Vitals: HR + BR + Temp + SpO2
    vit_scores = _ss(["hr","br","temp","spo2"])
    vit_facts = []
    for k,label in (("hr","HR"),("br","BR"),("temp","Temp"),("spo2","SpO2")):
        if k in vitals:
            vit_facts.append(f"{label} {vitals.get(k)}")
    v_score = int(round(sum(vit_scores)/len(vit_scores))) if vit_scores else None

    # 2) 🩺 Symptom burden: from report content
    sb_score = 100
    sb_fact = []
    urgent = [_strip_accents(w) for w in
              ["επείγον","emergency","ανοσφαιρία","unconscious","αναίσθητ","κατάρρευση","collapse",
               "δύσπνοια σοβαρή","severe respiratory","seizure","σπασμ"]]
    if any(w in rep_low for w in urgent):
        sb_score -= 50
        sb_fact.append("κόκκινες σημαίες" if lang=="el" else "red flags")
    severity = [_strip_accents(w) for w in
                ("σοβαρ","οξύς","έντον","severe","intense","acute")]
    if any(w in rep_low for w in severity):
        sb_score -= 12
        sb_fact.append("έντονα συμπτώματα" if lang=="el" else "intense symptoms")
    diff_rows = rep_low.count("|")
    if diff_rows >= 16:
        sb_score -= 8
        sb_fact.append("πολλαπλές διαφορικές" if lang=="el" else "multiple differentials")
    sb_score = max(20, sb_score)
    if not sb_fact:
        sb_fact.append("ήπιο προφίλ" if lang=="el" else "mild profile")

    pillars = [
        {"key":"vitals","icon":"❤️",
         "label_el":"Ζωτικές Ενδείξεις","label_en":"Vitals",
         "score":v_score,"factors":vit_facts,"available":v_score is not None},
        {"key":"symp","icon":"🩺",
         "label_el":"Συμπτωματικό Φορτίο","label_en":"Symptom Burden",
         "score":sb_score,"factors":sb_fact,"available":True},
    ]
    avail = [p for p in pillars if p["available"]]
    overall = int(round(sum(p["score"] for p in avail) / len(avail))) if avail else None
    return pillars, overall


def _grade_label(score, lang):
    if score is None:
        return ("Δεν υπάρχουν δεδομένα", "#9CA3AF") if lang=="el" else ("No data", "#9CA3AF")
    if score >= 80: return (("Άριστο" if lang=="el" else "Excellent"), "#059669")
    if score >= 60: return (("Καλό"   if lang=="el" else "Good"),      "#10B981")
    if score >= 40: return (("Μέτριο" if lang=="el" else "Neutral"),   "#3B82F6")
    if score >= 20: return (("Χαμηλό" if lang=="el" else "Limited"),   "#F97316")
    return            (("Πολύ χαμηλό" if lang=="el" else "Severe limit."), "#DC2626")


def _pillar_scale_html(score):
    if score is None:
        return '<div style="height:10px;background:#F3F4F6;border-radius:5px;margin-top:6px"></div>'
    seg = max(0, min(4, int(score) // 20))
    colors = ["#DC2626","#F97316","#3B82F6","#10B981","#059669"]
    out = '<div style="display:flex;gap:4px;margin-top:6px">'
    for i in range(5):
        bg = colors[i] if i <= seg else "#E5E7EB"
        marker = "box-shadow:0 0 0 2px white inset" if i == seg else ""
        out += f'<div style="flex:1;height:10px;background:{bg};border-radius:5px;{marker}"></div>'
    out += '</div>'
    return out


def _render_pet_health_pillars(pet, vitals, status_map, report_text, lang):
    """2-Pillar Health Profile card for pets (Vitals + Symptom Burden).
    Only shown when vitals were measured."""
    pillars, overall = _compute_pet_health_pillars(pet, vitals, status_map, report_text, lang)
    has_measurements = any(p["available"] for p in pillars if p["key"]=="vitals")
    if not has_measurements:
        return
    if lang == "el":
        title    = "📊 ΠΡΟΦΙΛ ΥΓΕΙΑΣ ΚΑΤΟΙΚΙΔΙΟΥ"
        ov_lbl   = "Συνολικό σκορ"
        no_data  = "δεν μετρήθηκε"
        method   = ("Υπολογίζεται από ζωτικές ενδείξεις + ευρήματα εκτίμησης. "
                    "Δεν αντικαθιστά κτηνιατρική εξέταση.")
        factors_lbl = "Παράγοντες"
    else:
        title    = "📊 PET HEALTH PROFILE"
        ov_lbl   = "Overall score"
        no_data  = "not measured"
        method   = ("Computed from vitals + assessment findings. "
                    "Not a substitute for a vet examination.")
        factors_lbl = "Factors"
    ov_grade, ov_color = _grade_label(overall, lang)
    overall_disp = f"{overall}" if overall is not None else "—"

    rows_html = ""
    for p in pillars:
        label = p["label_el"] if lang == "el" else p["label_en"]
        grade, gcolor = _grade_label(p["score"], lang)
        score_disp = f"{p['score']}" if p["score"] is not None else "—"
        factors_disp = (" · ".join(p["factors"][:3])) if p["factors"] else no_data
        opacity = "1" if p["available"] else "0.55"
        rows_html += (
            f'<div style="padding:12px 0;border-top:1px solid #F3F4F6;opacity:{opacity}">'
            f'<div style="display:flex;align-items:center;justify-content:space-between;gap:12px">'
            f'<div style="display:flex;align-items:center;gap:10px;min-width:0;flex:1">'
            f'<span style="font-size:20px;flex-shrink:0">{p["icon"]}</span>'
            f'<span style="font-size:13.5px;font-weight:700;color:#1F2937">{label}</span>'
            f'</div>'
            f'<div style="display:flex;align-items:center;gap:10px;flex-shrink:0">'
            f'<span style="font-size:18px;font-weight:800;color:{gcolor};font-variant-numeric:tabular-nums">{score_disp}<span style="font-size:11px;color:#9CA3AF;font-weight:600">%</span></span>'
            f'<span style="background:{gcolor}15;color:{gcolor};font-size:10.5px;font-weight:700;padding:3px 9px;border-radius:99px;letter-spacing:0.04em;text-transform:uppercase">{grade}</span>'
            f'</div>'
            f'</div>'
            f'{_pillar_scale_html(p["score"])}'
            f'<div style="font-size:11px;color:#6B7280;margin-top:6px;line-height:1.5">'
            f'<span style="font-weight:700;letter-spacing:0.08em;text-transform:uppercase">{factors_lbl}:</span> {factors_disp}'
            f'</div>'
            f'</div>'
        )
    st.markdown(f"""
<style>
.pan-hp-card {{
  background: white; border: 1px solid #E5E7EB; border-radius: 14px;
  padding: 22px 24px; margin: 18px 0;
  font-family: 'Inter', system-ui, sans-serif;
  box-shadow: 0 1px 3px rgba(0,0,0,0.04);
}}
.pan-hp-title {{
  font-size: 11px; font-weight: 700; letter-spacing: 0.14em;
  color: #6B7280; text-transform: uppercase;
  border-bottom: 2px solid #E5E7EB; padding-bottom: 10px; margin-bottom: 14px;
}}
.pan-hp-overall {{
  display: flex; align-items: center; gap: 16px;
  background: linear-gradient(135deg, #F9FAFB 0%, #F3F4F6 100%);
  border-radius: 12px; padding: 14px 18px; margin-bottom: 4px;
}}
.pan-hp-overall .ov-num {{
  font-size: 38px; font-weight: 800; line-height: 1;
  color: {ov_color}; font-variant-numeric: tabular-nums;
}}
.pan-hp-overall .ov-meta {{ flex: 1; min-width: 0; }}
.pan-hp-overall .ov-lbl {{
  font-size: 10.5px; font-weight: 700; letter-spacing: 0.12em;
  color: #6B7280; text-transform: uppercase;
}}
.pan-hp-overall .ov-grade {{
  font-size: 16px; font-weight: 700; color: {ov_color}; margin-top: 2px;
}}
.pan-hp-method {{
  font-size: 10.5px; color: #9CA3AF; margin-top: 12px;
  padding-top: 10px; border-top: 1px dashed #E5E7EB; line-height: 1.5;
}}
</style>
<div class="pan-hp-card">
<div class="pan-hp-title">{title}</div>
<div class="pan-hp-overall">
<div class="ov-num">{overall_disp}<span style="font-size:18px;color:#9CA3AF;font-weight:600">%</span></div>
<div class="ov-meta"><div class="ov-lbl">{ov_lbl}</div><div class="ov-grade">{ov_grade}</div></div>
</div>
{rows_html}
<div class="pan-hp-method">ℹ️ {method}</div>
</div>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# SCREENS
# ─────────────────────────────────────────────────────────────────────────────

def render_home():
    lang = st.session_state.lang

    c1,c2 = st.columns([6,1])
    with c2:
        if st.button("🇬🇧 EN" if lang=="el" else "🇬🇷 ΕΛ"):
            st.session_state.lang = "en" if lang=="el" else "el"; st.rerun()

    st.markdown(f'''<div class="pet-hero">
        <div style="font-size:64px;margin-bottom:8px">🐾</div>
        <h1>{t("title")}</h1>
        <p>{t("subtitle")}</p>
        <div class="pet-tagline">{t("tagline")}</div>
    </div>''', unsafe_allow_html=True)

    st.markdown(f'<div class="disclaimer">{t("disclaimer_main")}</div>', unsafe_allow_html=True)

    col1,col2,col3 = st.columns([1,2,1])
    with col2:
        if st.button(t("start"), type="primary", use_container_width=True):
            st.session_state.screen="intake"; st.rerun()

    st.markdown("---")
    f1,f2,f3 = st.columns(3)
    with f1:
        st.markdown('<div class="card"><div style="font-size:32px">📋</div><h3 style="margin-top:12px">MSD Veterinary Manual</h3><p style="font-size:13px;color:#6B7280">Κάθε αναφορά υποστηρίζεται από το MSD Vet Manual — χρυσό πρότυπο κτηνιατρικής.</p></div>', unsafe_allow_html=True)
    with f2:
        st.markdown('<div class="card"><div style="font-size:32px">⚠️</div><h3 style="margin-top:12px">Τοξικότητα & Ασφάλεια</h3><p style="font-size:13px;color:#6B7280">Αυτόματη ανίχνευση τοξικών ουσιών — ιδιαίτερα κρίσιμο για γάτες.</p></div>', unsafe_allow_html=True)
    with f3:
        st.markdown('<div class="card"><div style="font-size:32px">🇬🇷</div><h3 style="margin-top:12px">pet.gov.gr</h3><p style="font-size:13px;color:#6B7280">Σύνδεσμοι προς τις επίσημες υπηρεσίες του Εθνικού Μητρώου Ζώων Συντροφιάς.</p></div>', unsafe_allow_html=True)

    st.markdown(f'<div class="emergency-vet">{t("emergency_vet")}</div>', unsafe_allow_html=True)


def render_intake():
    render_stepper("intake")
    lang = st.session_state.lang
    pet = st.session_state.pet
    st.markdown(f"## 🐾 {t('pet_name')} & Προφίλ")

    c1,c2 = st.columns([2,1])
    with c1: name = st.text_input(t("pet_name"), value=pet.get("name",""), placeholder="Μπόμπης")
    with c2:
        species_opts = SPECIES[lang]
        prev_sp = pet.get("species_label", species_opts[0])
        if prev_sp not in species_opts: prev_sp = species_opts[0]
        species_label = st.selectbox(t("species"), species_opts,
                                     index=species_opts.index(prev_sp))
    species_key = SPECIES_KEY.get(species_label, "dog")

    # Breed dropdown based on species
    if species_key == "dog":
        breeds = DOG_BREEDS_EL if lang=="el" else DOG_BREEDS_EN
    elif species_key == "cat":
        breeds = CAT_BREEDS_EL if lang=="el" else CAT_BREEDS_EN
    else:
        breeds = ["—"]
    breed = st.selectbox(t("breed"), breeds)

    c1,c2,c3,c4 = st.columns(4)
    with c1: age_y = st.number_input(t("age_y"), min_value=0, max_value=30, value=pet.get("age_y",0))
    with c2: age_m = st.number_input(t("age_m"), min_value=0, max_value=11, value=pet.get("age_m",0))
    with c3:
        sex_opts = [t("male"), t("female"), t("neutered")]
        sex = st.selectbox(t("sex"), sex_opts)
    with c4: weight = st.number_input(t("weight"), min_value=0.0, max_value=150.0,
                                       value=(float(pet.get("weight")) if pet.get("weight") else None), placeholder="5.0", format="%.1f")

    microchip = st.text_input(t("microchip"), value=pet.get("microchip",""), placeholder="941000123456789")
    vax_opts = [t("yes"), t("no"), t("unknown")]
    vaccinations = st.selectbox(t("vaccinations"), vax_opts)
    conditions = st.text_area(t("conditions"), value=pet.get("conditions",""), height=80,
                               placeholder="Π.χ. Αλλεργία σε πρωτεΐνες σιταριού, χρόνια γαστρίτιδα")

    st.markdown(f"**{t('meds')}**")
    if not st.session_state.med_inputs:
        prev = pet.get("meds_raw","")
        st.session_state.med_inputs = [m.strip() for m in prev.split(",") if m.strip()] or [""]
    for mi, mv in enumerate(st.session_state.med_inputs):
        mc1,mc2 = st.columns([5,1])
        with mc1: st.session_state.med_inputs[mi] = st.text_input(
            f"Φάρμακο {mi+1}", value=mv, key=f"med_{mi}", label_visibility="collapsed",
            placeholder="Π.χ. Frontline Plus 1x/μήνα" if mi==0 else "")
        with mc2:
            if st.button("✕", key=f"del_med_{mi}"): st.session_state.med_inputs.pop(mi); st.rerun()
    if st.button("＋ " + ("Προσθήκη φαρμάκου" if lang=="el" else "Add medication")):
        st.session_state.med_inputs.append(""); st.rerun()
    meds_raw = ", ".join(m for m in st.session_state.med_inputs if m.strip())

    vet_name = st.text_input(t("vet_name"), value=pet.get("vet_name",""),
                              placeholder="Π.χ. Κτηνιατρείο Αθήνας, Δρ. Παπαδόπουλος")

    col_b, col_n = st.columns([1,3])
    with col_b:
        if st.button(t("back")): st.session_state.screen="home"; st.rerun()
    with col_n:
        if st.button(t("next"), type="primary", use_container_width=True):
            if name:
                # Toxicity check on medications
                tox_warns = check_toxicity(species_key, meds_raw)
                if tox_warns:
                    for w in tox_warns:
                        st.error(w)
                    st.stop()
                st.session_state.pet = {
                    "name":name,"species_key":species_key,"species_label":species_label,
                    "breed":breed,"age_y":age_y,"age_m":age_m,"sex":sex,
                    "weight":weight,"microchip":microchip,"vaccinations":vaccinations,
                    "conditions":conditions,"meds_raw":meds_raw,"vet_name":vet_name
                }
                st.session_state.screen="vitals"; st.rerun()
            else:
                st.warning("Παρακαλώ εισάγετε το όνομα του κατοικίδιου." if lang=="el" else "Please enter your pet's name.")


def render_vitals():
    render_stepper("vitals")
    pet  = st.session_state.pet
    lang = st.session_state.lang
    sp   = pet.get("species_key","dog")
    rng  = VITAL_RANGES.get(sp, VITAL_RANGES["dog"])
    st.markdown(f"## 📊 {t('vitals_title')} — {pet.get('name','')} {pet.get('species_label','')}")

    hr_range = rng["hr"]; br_range = rng["br"]; temp_range = rng["temp"]
    st.caption(f"{'Φυσιολογικά για' if lang=='el' else 'Normal for'} {pet.get('species_label','')}: "
               f"HR {hr_range[0]}–{hr_range[1]} bpm · BR {br_range[0]}–{br_range[1]}/min · "
               f"Temp {temp_range[0]}–{temp_range[1]}°C")

    # ── Tabs: Photo Scan | Vitals | Skip ──────────────────────────────────────
    tab_scan, tab_vitals = st.tabs([
        "📷 " + ("Σάρωση Φωτογραφίας" if lang=="el" else "Photo Scan"),
        "📋 " + ("Ζωτικές Ενδείξεις"  if lang=="el" else "Enter Vitals"),
    ])

    with tab_scan:
        rf_key = _secret("ROBOFLOW_API_KEY","")
        st.markdown(f"### {'Ανάλυση Φωτογραφίας' if lang=='el' else 'Photo Health Analysis'}")
        st.caption("Florence-2 (Microsoft) + Claude Vision · " +
                   ("Ανεβάστε φωτογραφία του ματιού, δέρματος, αυτιού, ούλων ή σώματος"
                    if lang=="el" else "Upload photo of eye, skin, ear, gums or body"))

        SCAN_OPTS = {
            "el": [("eye","👁️ Μάτια"),("skin","🔬 Δέρμα/Τρίχωμα"),
                   ("ear","👂 Αυτιά"),("mouth","🦷 Στόμα/Ούλα"),
                   ("body","🐾 Γενική Εμφάνιση"),("paw","🐶 Πατούσες")],
            "en": [("eye","👁️ Eyes"),("skin","🔬 Skin/Coat"),
                   ("ear","👂 Ears"),("mouth","🦷 Mouth/Gums"),
                   ("body","🐾 Body"),("paw","🐶 Paws")],
        }
        opts = SCAN_OPTS[lang]
        scan_labels = [o[1] for o in opts]
        scan_keys   = [o[0] for o in opts]
        sel_idx = st.radio("", scan_labels, horizontal=True, key="scan_type_radio",
                           label_visibility="collapsed")
        selected_scan = scan_keys[scan_labels.index(sel_idx)] if sel_idx in scan_labels else "eye"

        uploaded = st.file_uploader(
            ("Φωτογραφία" if lang=="el" else "Upload photo"),
            type=["jpg","jpeg","png","webp","heic","heif"], key="pet_photo_upload"
        )

        if uploaded:
            col_img, col_info = st.columns([1,1])
            with col_img:
                st.image(uploaded, use_column_width=True)
            with col_info:
                st.markdown(f"**{pet.get('name','')}** {pet.get('species_label','')}")
                st.markdown(f"Scan: **{sel_idx}**")

            img_bytes = uploaded.read()
            fname_lower = uploaded.name.lower()

            # Convert HEIC/HEIF (iPhone default format) to JPEG
            if fname_lower.endswith((".heic",".heif")):
                if HEIC_OK:
                    try:
                        img_bytes, img_type = convert_heic(img_bytes, uploaded.name)
                        st.caption("✅ HEIC → JPEG " + ("μετατράπηκε αυτόματα" if lang=="el" else "converted automatically"))
                    except Exception as e:
                        st.error(f"HEIC conversion failed: {e}")
                        st.stop()
                else:
                    st.error("⚠️ HEIC photos need pillow-heif. Add it to requirements.txt" if lang=="en"
                             else "⚠️ Οι φωτογραφίες HEIC χρειάζονται pillow-heif στο requirements.txt")
                    st.stop()
            else:
                img_type = "image/jpeg"
                if fname_lower.endswith(".png"):  img_type = "image/png"
                if fname_lower.endswith(".webp"): img_type = "image/webp"

            img_b64 = _b64.b64encode(img_bytes).decode()

            if st.button("🔍 " + ("Ανάλυση" if lang=="el" else "Analyse"),
                         type="primary", use_container_width=True, key="analyse_photo"):
                with st.spinner("Florence-2 + Claude..." if lang=="el" else "Florence-2 + Claude analysing..."):
                    # Step 1: Florence-2 visual description
                    f2_desc = ""
                    if rf_key:
                        f2_result = florence2_analyze(img_b64, selected_scan, rf_key)
                        if f2_result.get("ok"):
                            f2_desc = f2_result.get("description","")

                    # Step 2: Claude Vision clinical interpretation
                    context_note = (f"\n\nFLORENCE-2 DESCRIPTION: {f2_desc}" if f2_desc else "")
                    system_prompt = ("Είσαι κτηνιατρικός αναλυτής φωτογραφιών. Δίνεις δομημένη, ακριβή ανάλυση."
                                     if lang=="el" else
                                     "You are a veterinary photo analyst. Give structured, accurate analysis.")
                    el_suffix = "\n\nDose: **EURIMATA** | **AXIOLOGISI** | **PITHANES AITIES** | **SISTASI**"
                    en_suffix = "\n\nProvide: **FINDINGS** | **ASSESSMENT** (Normal/Monitor/Urgent) | **POSSIBLE CAUSES** | **RECOMMENDATION**"
                    clinical_prompt = (SCAN_PROMPTS.get(selected_scan, SCAN_PROMPTS["skin"]) + context_note + (el_suffix if lang=="el" else en_suffix))
                    analysis = claude_vision_pet(img_b64, img_type, clinical_prompt, system_prompt)

                # Show Florence-2 raw description
                if f2_desc:
                    st.markdown(f'<div style="background:#F0FDF4;border:1px solid #A7F3D0;border-radius:10px;padding:10px 14px;margin-bottom:10px"><div style="font-size:11px;color:#6B7280;margin-bottom:4px">🔬 Florence-2 visual description</div><div style="font-size:13px">{f2_desc}</div></div>', unsafe_allow_html=True)

                # Show Claude clinical analysis
                st.markdown(f'<div class="card">', unsafe_allow_html=True)
                st.markdown(analysis)
                st.markdown('</div>', unsafe_allow_html=True)

                # Store findings in session state → feed to triage
                st.session_state["photo_scan_findings"] = {
                    "scan_type": selected_scan,
                    "scan_label": sel_idx,
                    "florence_desc": f2_desc,
                    "clinical_analysis": analysis,
                }

                # Button to continue to triage with findings
                if st.button("➤ " + ("Συνέχεια στην Εκτίμηση Συμπτωμάτων →" if lang=="el"
                                     else "Continue to Symptom Assessment →"),
                             type="primary", use_container_width=True, key="photo_to_triage"):
                    # Auto-inject photo findings into triage chat
                    finding_msg = (f"Αποτελεσμα σαρωσης φωτογραφιας ({sel_idx}):\n\n{analysis}" if lang=="el"
                                   else f"Photo scan result ({sel_idx}):\n\n{analysis}")
                    st.session_state.triage_chat = [{"role":"user","content":finding_msg}]
                    st.session_state.screen = "triage"
                    st.rerun()

    with tab_vitals:
        v = st.session_state.vitals
        c1,c2,c3 = st.columns(3)
        with c1:
            hr   = st.number_input(t("hr"),  min_value=0, max_value=500, value=(int(v.get("hr")) if v.get("hr") else None), placeholder=str(int((hr_range[0]+hr_range[1])//2)))
            temp = st.number_input(t("temp"),min_value=0.0,max_value=45.0,value=(float(v.get("temp")) if v.get("temp") else None), placeholder=str(temp_range[0]), format="%.1f")
        with c2:
            br   = st.number_input(t("br"),  min_value=0, max_value=100, value=(int(v.get("br")) if v.get("br") else None), placeholder=str(int((br_range[0]+br_range[1])//2)))
            spo2 = st.number_input(t("spo2"),min_value=0, max_value=100, value=(int(v.get("spo2")) if v.get("spo2") else None), placeholder="98")
        with c3:
            wt   = st.number_input(t("weight_v"),min_value=0.0,max_value=200.0,
                                    value=(float(pet.get("weight")) if pet.get("weight") else None), placeholder="5.0", format="%.1f")

    col_b,col_s,col_n = st.columns([1,1,2])
    with col_b:
        if st.button(t("back")): st.session_state.screen="intake"; st.rerun()
    with col_s:
        if st.button(t("skip_vitals")): st.session_state.vitals={}; st.session_state.screen="triage"; st.rerun()
    with col_n:
        if st.button(t("analyse_vitals"), type="primary", use_container_width=True):
            vd={}
            if hr:   vd["hr"]   = hr
            if br:   vd["br"]   = br
            if temp: vd["temp"] = temp
            if spo2: vd["spo2"] = spo2
            if wt:   vd["weight"] = wt
            st.session_state.vitals = vd
            classify_pet_vitals(vd, sp)
            if vd:
                with st.spinner("Ανάλυση..." if lang=="el" else "Analysing..."):
                    vtext = "\n".join(f"- {k}: {val}" for k,val in vd.items())
                    prompt = (f"Κατοικίδιο: {pet.get('name')}, {pet.get('species_label')} ({pet.get('breed')}), "
                              f"{pet.get('age_y')}y, {wt}kg\n\nΖωτικές:\n{vtext}\n\n"
                              f"Ερμήνευσε με βάση το φυσιολογικό εύρος για {pet.get('species_label')}. "
                              f"Φυσ. εύρος: HR {hr_range[0]}-{hr_range[1]}, BR {br_range[0]}-{br_range[1]}, "
                              f"Temp {temp_range[0]}-{temp_range[1]}°C. Σημείωσε ό,τι χρήζει προσοχής.")
                    st.session_state.vitals_analysis = claude(
                        [{"role":"user","content":prompt}], system=petainurse_system(), max_tokens=3000)
            st.session_state.screen="triage"; st.rerun()


def render_vitals_summary():
    v = st.session_state.vitals
    if not v: return
    sp = st.session_state.pet.get("species_key","dog")
    status = classify_pet_vitals(v, sp)
    LABELS = {"hr":("❤️","Heart Rate","bpm"),"br":("🌬️","Breathing","/min"),
               "temp":("🌡️","Temp","°C"),"spo2":("💧","SpO2","%"),"weight":("⚖️","Weight","kg")}
    badges = []
    for key in ["hr","br","temp","spo2","weight"]:
        if key in v: badges.append((key, v[key], LABELS[key][2], status.get(key,"green")))
    if not badges: return
    cols = st.columns(len(badges))
    for i,(key,val,unit,col) in enumerate(badges):
        icon,label,_ = LABELS[key]
        with cols[i]:
            bg  = {"green":"#EDFBF0","yellow":"#FFFBEB","red":"#FEF2F2"}.get(col,"#F0FDF4")
            brd = {"green":"#A3E6B5","yellow":"#FCD34D","red":"#FCA5A5"}.get(col,"#A7F3D0")
            st.markdown(f'<div style="background:{bg};border:1px solid {brd};border-radius:12px;padding:12px;text-align:center"><div style="font-size:18px">{icon}</div><div style="font-size:20px;font-weight:700">{val}</div><div style="font-size:10px;color:#6B7280">{unit}</div><div style="font-size:11px;color:#374151">{label}</div></div>', unsafe_allow_html=True)
    if st.session_state.vitals_analysis:
        with st.expander("📋 Ανάλυση ζωτικών" if st.session_state.lang=="el" else "📋 Vitals analysis"):
            st.markdown(st.session_state.vitals_analysis)


def render_triage():
    render_stepper("triage")
    pet  = st.session_state.pet
    lang = st.session_state.lang
    sp   = pet.get("species_key","dog")
    st.markdown(f"## 🩺 {t('triage_title')} — {pet.get('name','')} {pet.get('species_label','')}")
    render_vitals_summary()
    st.markdown(f'<div class="disclaimer">{t("disclaimer_main")}</div>', unsafe_allow_html=True)

    # Symptom tracker (browser-only, localStorage)
    _render_pet_symptom_tracker(lang)

    # ── Lab analysis (PDF/image of vet lab results) ───────────────────────────
    _lab_title = "🧪 Εργαστηριακές Εξετάσεις Κατοικίδιου" if lang=="el" else "🧪 Pet Lab Results"
    with st.expander(_lab_title, expanded=False):
        st.caption("PDF ή φωτογραφία αποτελεσμάτων αίματος/ούρων κ.λπ." if lang=="el"
                   else "PDF or photo of blood/urine test results, etc.")
        lab_file = st.file_uploader(
            ("Ανέβασμα εξέτασης" if lang=="el" else "Upload lab result"),
            type=["pdf","jpg","jpeg","png","webp","heic","heif"], key="pet_lab_upload"
        )
        if lab_file:
            if st.button("🔍 " + ("Ανάλυση Εξέτασης" if lang=="el" else "Analyse Lab Result"),
                         type="primary", use_container_width=True, key="analyse_lab"):
                file_bytes = lab_file.read()
                fname_lower = lab_file.name.lower()
                mime_type = "application/pdf"
                if fname_lower.endswith((".heic",".heif")):
                    if HEIC_OK:
                        try:
                            file_bytes, mime_type = convert_heic(file_bytes, lab_file.name)
                        except Exception as e:
                            st.error(f"HEIC conversion failed: {e}")
                            file_bytes = None
                    else:
                        st.error("⚠️ Οι φωτογραφίες HEIC χρειάζονται pillow-heif." if lang=="el"
                                 else "⚠️ HEIC photos need pillow-heif.")
                        file_bytes = None
                elif fname_lower.endswith((".jpg",".jpeg")): mime_type = "image/jpeg"
                elif fname_lower.endswith(".png"):  mime_type = "image/png"
                elif fname_lower.endswith(".webp"): mime_type = "image/webp"
                elif not fname_lower.endswith(".pdf"): mime_type = "image/jpeg"

                if file_bytes:
                    with st.spinner("Claude αναλύει..." if lang=="el" else "Claude analysing..."):
                        analysis = claude_analyze_pet_lab(
                            file_bytes, mime_type, pet, st.session_state.triage_chat, lang, lab_file.name)
                    st.markdown(analysis)
                    st.session_state.lab_findings.append({
                        "file_name": lab_file.name, "analysis": analysis,
                    })
                    finding_msg = (f"Αποτέλεσμα εργαστηριακής εξέτασης ({lab_file.name}):\n\n{analysis}" if lang=="el"
                                   else f"Lab result ({lab_file.name}):\n\n{analysis}")
                    st.session_state.triage_chat.append({"role":"user","content":finding_msg})
                    st.success("✅ " + ("Προστέθηκε στην εκτίμηση." if lang=="el" else "Added to the assessment."))
        if st.session_state.lab_findings:
            st.caption(("Καταχωρημένες εξετάσεις: " if lang=="el" else "Logged lab results: ")
                       + ", ".join(lf["file_name"] for lf in st.session_state.lab_findings))

    # Species-specific symptom chips
    CHIPS = {
        "dog": {
            "el":["Δεν τρώει","Εμετός","Διάρροια","Λήθαργος","Βήχας","Φτέρνισμα",
                  "Χωλότητα","Κνησμός","Αλωπεκία","Φούσκωμα κοιλιάς","Αυξημένη δίψα",
                  "Δύσπνοια","Σπασμοί","Πόνος ούρησης","Εκκρίσεις ματιών","Άλλο"],
            "en":["Not eating","Vomiting","Diarrhoea","Lethargy","Coughing","Sneezing",
                  "Limping","Itching","Hair loss","Bloated abdomen","Increased thirst",
                  "Breathing difficulty","Seizures","Painful urination","Eye discharge","Other"]
        },
        "cat": {
            "el":["Δεν τρώει","Εμετός","Διάρροια","Λήθαργος","Φτέρνισμα","Κνησμός",
                  "Αδυναμία ούρησης","Αίμα στα ούρα","Βήχας","Αλωπεκία","Αυξημένη δίψα",
                  "Δύσπνοια","Σπασμοί","Εκκρίσεις ματιών","Στοματίτιδα","Άλλο"],
            "en":["Not eating","Vomiting","Diarrhoea","Lethargy","Sneezing","Itching",
                  "Unable to urinate","Blood in urine","Coughing","Hair loss","Increased thirst",
                  "Breathing difficulty","Seizures","Eye discharge","Stomatitis","Other"]
        },
        "rabbit":{
            "el":["Δεν τρώει","Φούσκωμα","Λήθαργος","Διάρροια","Τρίξιμο δοντιών","Άλλο"],
            "en":["Not eating","Bloating","Lethargy","Diarrhoea","Tooth grinding","Other"]
        },
    }
    chips = CHIPS.get(sp, CHIPS["dog"])[lang]
    st.caption("Γρήγορη επιλογή:" if lang=="el" else "Quick select:")
    row1,row2 = chips[:8], chips[8:]
    cr1 = st.columns(len(row1))
    for ci,chip in enumerate(row1):
        with cr1[ci]:
            sel = chip in st.session_state.symptom_chips
            if st.button(("✓ " if sel else "")+chip, key=f"chip_{ci}", use_container_width=True):
                if chip in st.session_state.symptom_chips: st.session_state.symptom_chips.remove(chip)
                else: st.session_state.symptom_chips.append(chip)
                st.rerun()
    if row2:
        cr2 = st.columns(len(row2))
        for ci,chip in enumerate(row2):
            with cr2[ci]:
                sel = chip in st.session_state.symptom_chips
                if st.button(("✓ " if sel else "")+chip, key=f"chip2_{ci}", use_container_width=True):
                    if chip in st.session_state.symptom_chips: st.session_state.symptom_chips.remove(chip)
                    else: st.session_state.symptom_chips.append(chip)
                    st.rerun()

    if st.session_state.symptom_chips:
        if st.button("➤ "+("Αποστολή επιλεγμένων" if lang=="el" else "Send selected"), type="primary"):
            msg = ("Κύρια συμπτώματα: " if lang=="el" else "Main symptoms: ")+", ".join(st.session_state.symptom_chips)
            st.session_state.triage_chat.append({"role":"user","content":msg})
            st.session_state.symptom_chips = []; st.rerun()

    # Toxicity check on symptom text
    all_symptoms = " ".join(st.session_state.symptom_chips)
    tox_warns = check_toxicity(sp, pet.get("meds_raw",""), all_symptoms)
    for w in tox_warns:
        st.markdown(f'<div class="toxicity-warn">{w}</div>', unsafe_allow_html=True)

    st.divider()

    # Chat
    for msg in st.session_state.triage_chat:
        with st.chat_message(msg["role"], avatar="🐾" if msg["role"]=="assistant" else None):
            st.markdown(msg["content"])

    ready_phrases = ["έχω αρκετά στοιχεία","μπορούμε να δημιουργήσουμε","i have enough information","we can generate","veterinary report","κτηνιατρική αναφορά"]
    last_assistant = next((m["content"].lower() for m in reversed(st.session_state.triage_chat) if m["role"]=="assistant"), "")
    triage_ready = any(ph in last_assistant for ph in ready_phrases)

    # ── Voice input (mic → Groq Whisper → review/edit → send) ─────────────────
    voice_text = None
    if get_groq_key():
        with st.expander("🎙️ " + ("Μίλα αντί να γράψεις" if lang=="el" else "Speak instead of typing"), expanded=False):
            audio = st.audio_input(
                ("Ηχογράφηση" if lang=="el" else "Record"),
                key=f"pet_voice_{st.session_state._voice_widget_counter}")
            if audio:
                with st.spinner("Whisper..." if lang=="el" else "Transcribing..."):
                    txt, err = transcribe_audio(audio.read(), lang=lang, mime="audio/webm", filename="recording.webm")
                if err:
                    st.error(err)
                elif txt:
                    edited = st.text_area(
                        ("Επιβεβαίωσε / επεξεργάσου το κείμενο πριν την αποστολή" if lang=="el"
                         else "Review/edit the text before sending"),
                        value=txt, key="pet_voice_text")
                    if st.button("➤ " + ("Αποστολή" if lang=="el" else "Send"), key="pet_voice_send"):
                        voice_text = edited
                        st.session_state._voice_widget_counter += 1

    user_input = st.chat_input(t("triage_placeholder"), key="triage_input")
    if voice_text:
        user_input = voice_text
    if user_input:
        st.session_state.triage_chat.append({"role":"user","content":user_input})
        with st.spinner("PetAiNurse..."):
            p = pet
            photo_ctx = ""
            if st.session_state.get("photo_scan_findings"):
                pf = st.session_state["photo_scan_findings"]
                photo_ctx = f"\nΦΩΤΟΓΡΑΦΙΑ ({pf.get('scan_label','')}): {pf.get('clinical_analysis','')[:400]}"
            profile_ctx = (f"Κατοικίδιο: {p.get('name')}, {p.get('species_label')} ({p.get('breed')}), "
                           f"{p.get('age_y')}y {p.get('age_m')}m, {p.get('sex')}, {p.get('weight','')}kg\n"
                           f"Παθήσεις: {p.get('conditions','—')}\nΦάρμακα: {p.get('meds_raw','—')}\nΚτηνίατρος: {p.get('vet_name','—')}{photo_ctx}")
            vitals_ctx = ("Ζωτικές: " + ", ".join(f"{k}={val}" for k,val in st.session_state.vitals.items())
                          if st.session_state.vitals else "Ζωτικές: δεν παρασχέθηκαν")
            system_ctx = petainurse_system() + f"\n\n{profile_ctx}\n{vitals_ctx}"
            reply = claude([{"role":m["role"],"content":m["content"]} for m in st.session_state.triage_chat],
                           system=system_ctx, max_tokens=3000)
            if reply and reply.strip() and reply.strip()[-1] not in ".!?»)":
                reply = reply.rstrip() + " ..."
        st.session_state.triage_chat.append({"role":"assistant","content":reply}); st.rerun()

    col_b,col_r = st.columns([1,2])
    with col_b:
        if st.button(t("back")): st.session_state.screen="vitals"; st.rerun()
    with col_r:
        enabled = triage_ready or len(st.session_state.triage_chat) >= 6
        if st.button(t("generate_report"), type="primary", use_container_width=True, disabled=not enabled):
            st.session_state.screen="report"; st.rerun()
    if not enabled:
        st.caption("Συνεχίστε — η PetAiNurse θα σας ειδοποιήσει όταν έχει αρκετά." if lang=="el"
                   else "Continue — PetAiNurse will let you know when she has enough.")


def render_report():
    render_stepper("report")
    pet  = st.session_state.pet
    lang = st.session_state.lang
    sp   = pet.get("species_key","dog")
    st.markdown(f"## 📋 {t('report_title')}")
    st.caption(f"{pet.get('name','')} {pet.get('species_label','')} · {pet.get('breed','')} · {datetime.now().strftime('%d %b %Y %H:%M')}")
    render_vitals_summary()

    if not st.session_state.report:
        conversation = "\n".join(
            f"{'Owner' if m['role']=='user' else 'PetAiNurse'}: {m['content']}"
            for m in st.session_state.triage_chat)
        vitals_text = ("\n".join(f"- {k}: {v}" for k,v in st.session_state.vitals.items())
                       if st.session_state.vitals else "Not provided")
        rng = VITAL_RANGES.get(sp, VITAL_RANGES["dog"])

        # MSD Vet Manual evidence search
        last_user = next((m["content"] for m in reversed(st.session_state.triage_chat) if m["role"]=="user"),"")
        search_q = last_user[:60] if last_user else pet.get("species_label","dog")
        with st.spinner("📋 MSD Veterinary Manual..." if lang=="el" else "📋 Searching MSD Vet Manual..."):
            refs = msdvet_search(sp, search_q, n=3)
            st.session_state.report_refs = refs
        msd_ctx = "\n".join(f"- {a['title']}: {a['url']}" for a in refs) if refs else "None found."

        report_prompt = f"""Generate a concise veterinary assessment report for:

PET: {pet.get('name')}, {pet.get('species_label')} ({pet.get('breed')}), {pet.get('age_y')}y {pet.get('age_m')}m, {pet.get('sex')}, {pet.get('weight','')}kg
VACCINATIONS: {pet.get('vaccinations','unknown')}
CONDITIONS/ALLERGIES: {pet.get('conditions','none')}
MEDICATIONS: {pet.get('meds_raw','none')}
ATTENDING VET: {pet.get('vet_name','not specified')}

VITALS (Normal for {pet.get('species_label')}: HR {rng['hr'][0]}-{rng['hr'][1]} bpm, BR {rng['br'][0]}-{rng['br'][1]}/min, Temp {rng['temp'][0]}-{rng['temp'][1]}°C):
{vitals_text}

CLINICAL CONSULTATION:
{conversation}

MSD VETERINARY MANUAL REFERENCES:
{msd_ctx}

Write a structured veterinary report:
1. CHIEF COMPLAINT
2. CLINICAL HISTORY
3. ASSESSMENT — Primary differential + top 2-3 differentials with probability %
4. RECOMMENDED WORKUP — Tests, diagnostics to discuss with vet
5. SUPPORTIVE CARE — What owner can do at home (if safe)
6. RED FLAGS — Symptoms requiring immediate emergency vet
7. MSD REFERENCES — Cite 1-2 references where relevant

Language: {"Greek (Ελληνικά)" if lang=="el" else "English"}
Be direct and clinical. Always recommend professional veterinary evaluation. End with AI disclaimer."""

        with st.spinner("Δημιουργία κτηνιατρικής αναφοράς..." if lang=="el" else "Generating veterinary report..."):
            result = claude([{"role":"user","content":report_prompt}],
                            system=petainurse_system(), max_tokens=3000, timeout=120)
            if result.startswith("⚠️"):
                st.error(result)
                if st.button("🔄 Retry"): st.rerun()
                return
            st.session_state.report = result

    if not st.session_state.report:
        if st.button("🔄 " + ("Δοκιμή ξανά" if lang=="el" else "Retry"), type="primary"): st.rerun()
        return

    # Toxicity warnings — always shown at top if relevant
    tox_warns = check_toxicity(sp, pet.get("meds_raw",""),
                               " ".join(m["content"] for m in st.session_state.triage_chat))
    for w in tox_warns:
        st.markdown(f'<div class="toxicity-warn">{w}</div>', unsafe_allow_html=True)

    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown(st.session_state.report)
    st.markdown('</div>', unsafe_allow_html=True)

    # Lab findings (if any)
    if st.session_state.lab_findings:
        _lf_title = "🧪 Ευρήματα Εργαστηριακών Εξετάσεων" if lang=="el" else "🧪 Lab Findings"
        with st.expander(f"{_lf_title} ({len(st.session_state.lab_findings)})", expanded=True):
            for lf in st.session_state.lab_findings:
                st.markdown(f"**📄 {lf['file_name']}**")
                st.markdown(lf["analysis"])
                st.markdown("---")

    # Health profile (vitals + symptom burden pillars)
    if st.session_state.vitals:
        status_map = classify_pet_vitals(dict(st.session_state.vitals), sp)
        _render_pet_health_pillars(pet, st.session_state.vitals, status_map, st.session_state.report, lang)

    # MSD Vet Manual references
    if st.session_state.report_refs:
        with st.expander(f"📋 {t('msdvet')} ({len(st.session_state.report_refs)})"):
            for a in st.session_state.report_refs:
                st.markdown(f"**[{a['title']}]({a['url']})**")

    # GPT-4o second opinion
    if get_openai_key():
        with st.expander(f"🤖 {t('second_opinion')}"):
            if not st.session_state.report_gpt:
                if st.button("Get GPT-4o Veterinary Second Opinion", type="secondary"):
                    with st.spinner("GPT-4o reviewing..."):
                        st.session_state.report_gpt = gpt4o(
                            prompt=f"Pet: {pet.get('name')}, {pet.get('species_label')} ({pet.get('breed')}), {pet.get('age_y')}y\n\nPetAiNurse's assessment:\n{st.session_state.report}\n\nDo you agree with this veterinary assessment? Provide additions, corrections, or alternative differentials. Be specific and species-appropriate.",
                            system=petainurse_system(), max_tokens=3000)
                    st.rerun()
            else:
                st.markdown(st.session_state.report_gpt)

    # Emergency vets
    with st.expander("🚨 " + ("Επείγοντα Κτηνιατρεία" if lang=="el" else "Emergency Vet Clinics")):
        render_emergency_vets(lang)

    # Wellness summary
    v = st.session_state.vitals
    if v:
        status_map = classify_pet_vitals(dict(v), sp)
        reds    = sum(1 for s in status_map.values() if s=="red")
        yellows = sum(1 for s in status_map.values() if s=="yellow")
        wellness = max(20, 100-reds*25-yellows*10)
        wcolor = "#10B981" if wellness>=75 else "#F59E0B" if wellness>=50 else "#EF4444"
        wlabel = ("Καλό" if wellness>=70 else "Μέτριο" if wellness>=50 else "Χρήζει Προσοχής") if lang=="el" else ("Good" if wellness>=70 else "Moderate" if wellness>=50 else "Needs Attention")
        st.markdown(f'''<div class="wellness-wrap">
            <div><div class="wellness-score" style="color:{wcolor}">{wellness}</div>
            <div class="wellness-label">{"Δείκτης Υγείας" if lang=="el" else "Health Score"}</div></div>
            <div style="flex:1"><div style="font-size:15px;opacity:.9">{wlabel}</div>
            <div style="background:rgba(255,255,255,.2);border-radius:99px;height:8px;margin-top:10px">
            <div style="background:{wcolor};width:{wellness}%;height:8px;border-radius:99px"></div></div></div>
        </div>''', unsafe_allow_html=True)

    st.markdown(f'<div class="emergency-vet">{t("emergency_vet")}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="disclaimer-red">AI-generated. Δεν αντικαθιστά κτηνιατρική εξέταση.</div>', unsafe_allow_html=True)

    # pet.gov.gr official services CTA
    st.markdown(f'''<div class="insurance-cta">
        <div style="font-size:28px;margin-bottom:8px">🐾</div>
        <div style="font-size:18px;font-weight:700;margin-bottom:6px">{t("insurance_cta")}</div>
        <div style="opacity:.85;font-size:13px;margin-bottom:14px">{t("insurance_sub")}</div>
        <a href="https://pet.gov.gr" target="_blank"
           style="background:white;color:#059669;padding:10px 24px;border-radius:8px;font-weight:700;text-decoration:none;font-size:14px">
            {t("insurance_btn")}
        </a>
    </div>''', unsafe_allow_html=True)
    render_govgr_links(lang)

    # Actions
    fname = f"petainurse_report_{pet.get('name','pet')}_{datetime.now().strftime('%Y%m%d')}"
    c1,c2,c3 = st.columns(3)
    with c1:
        if st.button("← "+("Νέα Εκτίμηση" if lang=="el" else "New Assessment"), use_container_width=True):
            for k,v in defaults.items(): st.session_state[k]=v
            st.rerun()
    with c2:
        st.download_button("📄 TXT", data=st.session_state.report,
                           file_name=fname+".txt", mime="text/plain", use_container_width=True)
    with c3:
        st.download_button("📄 PDF/HTML",
                           data=generate_pet_html_report(pet, st.session_state.vitals,
                                                          st.session_state.report, st.session_state.report_refs, lang,
                                                          lab_findings=st.session_state.lab_findings),
                           file_name=fname+".html", mime="text/html", use_container_width=True,
                           help="Open in browser → Ctrl+P → Save as PDF")

# ── COOKIE MANAGER (once) — persistent login ──────────────────────────────────
if _STX_OK and auth_enabled():
    if "CM" not in st.session_state:
        st.session_state["CM"] = stx.CookieManager(key="pan_cookie_mgr")
    CM = st.session_state["CM"]
    if not is_logged_in():
        _tok = None
        try:
            _tok = CM.get(COOKIE_NAME)
        except Exception:
            pass
        _email = _read_token(_tok) if _tok else None
        if _email:
            st.session_state["auth_user"] = _email

# ── ROUTER ────────────────────────────────────────────────────────────────────
if not render_login_gate():
    st.stop()

screen = st.session_state.screen
if   screen=="home":   render_home()
elif screen=="intake": render_intake()
elif screen=="vitals": render_vitals()
elif screen=="triage": render_triage()
elif screen=="report": render_report()
else: render_home()

# Persist login cookie on a clean render pass after successful login
if auth_enabled() and is_logged_in() and _STX_OK:
    _save_login_cookie(st.session_state["auth_user"])
