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

# Lifestyle illustrations (Vecteezy, licensed for commercial use)
try:
    from assets_illustrations import ILLUSTRATIONS, MASCOT_IMAGES
except Exception:
    ILLUSTRATIONS = {}
    MASCOT_IMAGES = {}

# Real pet photographs (replace the SVG illustrations the user disliked)
try:
    from assets_photos import PET_PHOTOS
except Exception:
    PET_PHOTOS = {}

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

# Category reference links used for the "Personalized Recommendations" cards
# (activity / nutrition / home-care). These are general, evergreen MSD Vet
# Manual + WSAVA pages — independent of the symptom-keyword lookup above.
MSD_RECS_REFS = {
    "dog": {
        "activity":  [
            {"title": "MSD Vet Manual — Exercise Requirements of Dogs", "url": "https://www.msdvetmanual.com/dog-owners/routine-care-and-breeding-of-dogs/routine-health-care-of-dogs"},
            {"title": "WSAVA Global Nutrition & Wellness Guidelines", "url": "https://wsava.org/global-guidelines/global-nutrition-guidelines/"},
        ],
        "nutrition": [
            {"title": "MSD Vet Manual — Nutrition: Dogs", "url": "https://www.msdvetmanual.com/dog-owners/nutrition-and-general-health-of-dogs/nutrition-general-feeding-of-dogs"},
            {"title": "WSAVA Global Nutrition Guidelines", "url": "https://wsava.org/global-guidelines/global-nutrition-guidelines/"},
        ],
        "lifestyle": [
            {"title": "MSD Vet Manual — Routine Health Care of Dogs", "url": "https://www.msdvetmanual.com/dog-owners/routine-care-and-breeding-of-dogs/routine-health-care-of-dogs"},
            {"title": "WSAVA Global Veterinary Guidelines", "url": "https://wsava.org/global-guidelines/"},
        ],
    },
    "cat": {
        "activity":  [
            {"title": "MSD Vet Manual — Routine Care of Cats", "url": "https://www.msdvetmanual.com/cat-owners/routine-care-and-breeding-of-cats/routine-health-care-of-cats"},
            {"title": "WSAVA Global Nutrition & Wellness Guidelines", "url": "https://wsava.org/global-guidelines/global-nutrition-guidelines/"},
        ],
        "nutrition": [
            {"title": "MSD Vet Manual — Nutrition: Cats", "url": "https://www.msdvetmanual.com/cat-owners/nutrition-and-general-health-of-cats/nutrition-general-feeding-of-cats"},
            {"title": "WSAVA Global Nutrition Guidelines", "url": "https://wsava.org/global-guidelines/global-nutrition-guidelines/"},
        ],
        "lifestyle": [
            {"title": "MSD Vet Manual — Routine Health Care of Cats", "url": "https://www.msdvetmanual.com/cat-owners/routine-care-and-breeding-of-cats/routine-health-care-of-cats"},
            {"title": "WSAVA Global Veterinary Guidelines", "url": "https://wsava.org/global-guidelines/"},
        ],
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


def generate_pet_recommendations(pet, vitals_text, conversation, report_text, lang="el"):
    """Ask Claude for 3 short personalized recommendation blurbs
    (activity / nutrition / lifestyle) tailored to this pet's situation,
    mirroring the Asklepios '📍 Εξατομικευμένες Συστάσεις' cards.
    Returns a dict: {"activity": "...", "nutrition": "...", "lifestyle": "..."} or {} on failure."""
    sp = pet.get("species_key","dog")
    species_label = pet.get("species_label", "pet")
    prompt = f"""Based on this veterinary assessment, write short personalized home-care
recommendations for the owner of {pet.get('name','the pet')} ({species_label}, {pet.get('breed','')},
{pet.get('age_y','?')}y {pet.get('age_m','?')}m, {pet.get('weight','?')}kg).

VITALS:
{vitals_text}

CONSULTATION:
{conversation}

ASSESSMENT:
{report_text[:2000]}

Respond with ONLY a raw JSON object (no markdown fences, no preamble) with exactly these
three keys, each a string of 2-4 sentences in {"Greek (Ελληνικά)" if lang=="el" else "English"}:
{{
  "activity": "Recommendations about exercise / activity level / movement restrictions appropriate for this pet's condition.",
  "nutrition": "Recommendations about diet, feeding schedule, foods to avoid or include, hydration.",
  "lifestyle": "Recommendations about home environment, rest, monitoring, stress reduction, grooming, or other home-care."
}}

Be specific to this pet's actual condition/symptoms — not generic advice. If the condition is mild
or no major issue was found, give sensible preventive/wellness guidance instead."""

    result = claude([{"role":"user","content":prompt}],
                    system=petainurse_system(), max_tokens=900, timeout=60)
    if result.startswith("⚠️"):
        return {}
    try:
        cleaned = _CJK_RANGES.sub("", result).strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.split("```")[1]
            if cleaned.startswith("json"):
                cleaned = cleaned[4:]
        data = json.loads(cleaned.strip())
        if all(k in data for k in ("activity","nutrition","lifestyle")):
            return data
    except Exception:
        pass
    return {}


def render_pet_recommendations(recs, sp, lang="el"):
    """Render the 3-column 'Personalized Recommendations' grid with MSD/WSAVA
    references, mirroring the Asklepios .recs-grid styling but vet-themed."""
    if not recs:
        return
    import html as _html_pr, re as _re_pr
    refs = MSD_RECS_REFS.get(sp, MSD_RECS_REFS["dog"])
    title = "📍 Εξατομικευμένες Συστάσεις" if lang=="el" else "📍 Personalized Recommendations"

    labels = {
        "activity":  ("🏃 Δραστηριότητα" if lang=="el" else "🏃 Activity"),
        "nutrition": ("🥗 Διατροφή" if lang=="el" else "🥗 Nutrition"),
        "lifestyle": ("🌿 Φροντίδα στο Σπίτι" if lang=="el" else "🌿 Home Care"),
    }
    refs_lbl = "📚 Οδηγίες & βιβλιογραφία" if lang=="el" else "📚 Guidelines & references"
    css_cls = {"activity":"activity","nutrition":"nutrition","lifestyle":"lifestyle"}

    boxes_html = ""
    for key in ("activity","nutrition","lifestyle"):
        text = _html_pr.escape(recs.get(key,"").strip())
        text = _re_pr.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
        ref_items = "".join(
            f'<li><a href="{r["url"]}" target="_blank" '
            f'style="color:#1E40AF;text-decoration:none">{_html_pr.escape(r["title"])}</a></li>'
            for r in refs.get(key, [])
        )
        boxes_html += (
            f'<div class="pr-box {css_cls[key]}">'
            f'<div class="pr-lbl">{labels[key]}</div>'
            f'<div class="pr-body">{text}</div>'
            f'<div class="pr-refs"><div class="pr-refs-lbl">{refs_lbl}</div>'
            f'<ul>{ref_items}</ul></div>'
            f'</div>'
        )

    st.markdown(
        '<style>'
        '.pr-grid{display:grid;grid-template-columns:1fr 1fr 1fr;gap:12px;margin:14px 0 18px}'
        '@media (max-width:900px){.pr-grid{grid-template-columns:1fr}}'
        '.pr-box{border:1px solid;border-radius:14px;padding:16px 18px;font-size:13px;line-height:1.6}'
        '.pr-box.activity{background:#EFF6FF;border-color:#BFDBFE}'
        '.pr-box.nutrition{background:#ECFDF5;border-color:#A7F3D0}'
        '.pr-box.lifestyle{background:#FFF7ED;border-color:#FED7AA}'
        '.pr-lbl{font-size:11px;font-weight:800;letter-spacing:.1em;text-transform:uppercase;color:#1F2937;margin-bottom:8px}'
        '.pr-refs{margin-top:10px;padding-top:8px;border-top:1px dashed rgba(0,0,0,0.10)}'
        '.pr-refs-lbl{font-size:10px;font-weight:700;letter-spacing:.1em;text-transform:uppercase;color:#6B7280;margin-bottom:4px}'
        '.pr-refs ul{list-style:none;padding:0;margin:0}'
        '.pr-refs li{font-size:11px;line-height:1.5;margin-bottom:3px}'
        '</style>'
        f'<h4 style="margin:18px 0 4px">{title}</h4>'
        f'<div class="pr-grid">{boxes_html}</div>',
        unsafe_allow_html=True,
    )


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
    resulting transcript text enters session state. Returns (text, error).

    Uses the `requests` library for multipart encoding — manual urllib
    multipart bodies have been observed to trigger 403 Forbidden from the
    Groq API even with a valid key."""
    key = get_groq_key()
    if not key:
        return None, "⚠️ GROQ_API_KEY not set."
    try:
        import requests
        files = {"file": (filename, audio_bytes, mime)}
        data = {
            "model": "whisper-large-v3",
            "language": lang if lang in ("el","en") else "el",
            "response_format": "text",
        }
        r = requests.post(
            "https://api.groq.com/openai/v1/audio/transcriptions",
            headers={"Authorization": f"Bearer {key}"},
            files=files, data=data, timeout=60,
        )
        if r.status_code == 200:
            return r.text.strip(), None
        if r.status_code == 401:
            return None, "⚠️ Groq API key invalid (401). Έλεγξε το GROQ_API_KEY."
        if r.status_code == 403:
            return None, f"⚠️ Groq 403 Forbidden: {r.text[:300]}"
        return None, f"⚠️ Groq HTTP {r.status_code}: {r.text[:300]}"
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


# ── AI OUTPUT SANITIZER ───────────────────────────────────────────────────────
# Strips stray CJK glyphs (e.g. 气 leaking from the second-opinion model) and
# repairs the truncated "🔔 ΣΥΣΤΑΣΗ ΠΡΟΤΕΡΑΙΟΤΗΤΑΣ" blockquote that rendered as
# "ξεμπάρκο" (a cut-off "> 🟡 **Ε…"). Applied to every model output before display.
import re as _re_san

# CJK + fullwidth/half-width forms + Hiragana/Katakana + Hangul
_CJK_RANGES = _re_san.compile(
    "[\u3000-\u303F\u3040-\u30FF\u3400-\u4DBF\u4E00-\u9FFF"
    "\uF900-\uFAFF\uFF00-\uFFEF\uAC00-\uD7AF]+"
)

def sanitize_ai_text(text):
    """Remove non-Greek/Latin stray glyphs and clean up dangling markdown so the
    report never shows Chinese characters or a half-written blockquote header."""
    if not text or not isinstance(text, str):
        return text or ""
    # 1) drop CJK / fullwidth runs entirely
    text = _CJK_RANGES.sub("", text)
    # 2) remove a blockquote line that was cut off mid-sentence (no closing on
    #    a bold marker, e.g. "> 🟡 **Ε") which is what produced the garbled text
    cleaned = []
    for line in text.split("\n"):
        s = line.strip()
        if s.startswith(">"):
            inner = s.lstrip(">").strip()
            # an unbalanced ** count means the bold/blockquote was truncated
            if inner.count("**") % 2 == 1 or len(inner) <= 4:
                continue
        cleaned.append(line)
    text = "\n".join(cleaned)
    # 3) collapse any orphan markdown markers and trailing whitespace
    text = _re_san.sub(r"\*\*\s*$", "", text)
    text = _re_san.sub(r"[ \t]+\n", "\n", text)
    text = _re_san.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


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
        sb.table("pet_drafts").upsert({"user_email": email, "data": blob}, on_conflict="user_email").execute()
    except Exception:
        pass

def load_draft(email):
    sb = _supabase_client()
    if not sb or not email or not _ENC_OK:
        return None
    try:
        res = sb.table("pet_drafts").select("data").eq("user_email", email).limit(1).execute()
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
        sb.table("pet_drafts").delete().eq("user_email", email).execute()
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
    "_gpt_integrated": False,
    "report_recs": None,
    "report_recs_refs": {},
    "lab_findings": [],   # list of dicts — lab PDF/image analyses
    "photo_findings": [], # list of dicts — photo scan analyses (eye/skin/etc.)
    "_voice_widget_counter": 0,
    "medications": [], "med_inputs": [],
    "symptom_chips": [],
    "intake_step": 0,     # 0-3 — grouped intake form steps
    "intake_draft": {},   # holds field values across intake steps
    "_intake_show_errors": False,
    "_hero_seen": False,  # full marketing hero shown once before login/home
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
        "disclaimer_main":"⚠️ Η PetAiNurse ΔΕΝ είναι ιατρικό ή κτηνιατρικό εργαλείο. Παρέχει πληροφορίες μόνο για ενημερωτικούς/εκπαιδευτικούς σκοπούς και δεν αντικαθιστά κτηνιατρική διάγνωση, εξέταση ή θεραπεία. Σε επείγον καλέστε άμεσα κτηνίατρο.",
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
        "disclaimer_main":"⚠️ PetAiNurse is NOT a medical or veterinary device/tool. It provides information for informational/educational purposes only and does not replace veterinary diagnosis, examination, or treatment. In an emergency call a vet immediately.",
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

def _render_disclaimer_strip(lang=None):
    """Compact 'not a medical/veterinary tool' disclaimer — shown on every screen."""
    lang = lang or st.session_state.lang
    st.markdown(f'<div class="disclaimer">{t("disclaimer_main")}</div>', unsafe_allow_html=True)

# ── STEPPER ───────────────────────────────────────────────────────────────────
def render_doc_header(title_el, title_en, *, icon="📋",
                      sub_el=None, sub_en=None, show_date=True, mascot_key=None):
    """Compact doc-template style header card for each screen — tells the
    user what to do on this step. White card with circular icon (or species
    mascot), brand caps, friendly title, optional subtitle and date."""
    lang = st.session_state.lang
    title = title_el if lang == "el" else title_en
    sub = (sub_el if lang == "el" else sub_en) or ""
    org = "PETAINURSE · AI ΚΤΗΝΙΑΤΡΙΚΟΣ ΝΟΣΗΛΕΥΤΗΣ" if lang == "el" else "PETAINURSE · AI VET NURSE"
    date_str = datetime.now().strftime("%d.%m.%Y")
    date_lbl = "ΗΜΕΡ." if lang == "el" else "DATE"
    date_html = (
        f'<div class="pan-dph-date"><div class="pan-dph-date-lbl">{date_lbl}</div>'
        f'<div class="pan-dph-date-val">{date_str}</div></div>'
    ) if show_date else ""
    sub_html = f'<div class="pan-dph-sub">{sub}</div>' if sub else ""
    if mascot_key:
        logo_inner = render_mascot(mascot_key, size=40)
    else:
        logo_inner = icon
    st.markdown(
        f"""
<style>
.pan-doc-page-head {{
  display: flex; align-items: center; gap: 16px;
  padding: 18px 22px;
  background: white;
  border: 1px solid #E5E7EB;
  border-radius: 14px;
  margin: 4px 0 22px;
  font-family: 'Inter', system-ui, sans-serif;
  box-shadow: 0 1px 3px rgba(0,0,0,0.03);
}}
.pan-dph-logo {{
  width: 50px; height: 50px; border-radius: 50%;
  background: #ECFDF5;
  display: flex; align-items: center; justify-content: center;
  font-size: 23px; flex-shrink: 0;
}}
.pan-dph-text {{ flex: 1; min-width: 0; }}
.pan-dph-org {{
  font-size: 9.5px; font-weight: 700; letter-spacing: 0.14em;
  color: #6B7280; text-transform: uppercase; margin-bottom: 3px;
}}
.pan-dph-title {{
  font-size: 19px; font-weight: 700; color: #111827;
  letter-spacing: -0.015em; line-height: 1.2;
}}
.pan-dph-sub {{
  font-size: 12.5px; color: #6B7280; margin-top: 3px; font-weight: 500;
}}
.pan-dph-date {{
  text-align: right; flex-shrink: 0;
  border-left: 1px solid #E5E7EB; padding-left: 14px;
}}
.pan-dph-date-lbl {{
  font-size: 9px; font-weight: 700; letter-spacing: 0.14em;
  color: #9CA3AF; text-transform: uppercase;
}}
.pan-dph-date-val {{
  font-size: 13px; font-weight: 700; color: #111827;
  font-variant-numeric: tabular-nums; margin-top: 2px;
}}
@media (max-width: 640px) {{
  .pan-doc-page-head {{ padding: 14px 16px; gap: 12px; }}
  .pan-dph-logo {{ width: 42px; height: 42px; font-size: 19px; }}
  .pan-dph-title {{ font-size: 16px; }}
  .pan-dph-sub {{ font-size: 11.5px; }}
  .pan-dph-date {{ display: none; }}
}}
</style>
<div class="pan-doc-page-head">
  <div class="pan-dph-logo">{logo_inner}</div>
  <div class="pan-dph-text">
    <div class="pan-dph-org">{org}</div>
    <div class="pan-dph-title">{title}</div>
    {sub_html}
  </div>
  {date_html}
</div>
""",
        unsafe_allow_html=True,
    )


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


# ── MASCOTS ───────────────────────────────────────────────────────────────────
MASCOT_IMG = {
    "dog": MASCOT_IMAGES.get("perro", ""),
    "cat": MASCOT_IMAGES.get("gato", ""),
}
MASCOT_NAMES = {"dog": "Perro", "cat": "Gato"}

def render_mascot(species_key="dog", size=72, style="", circle=False):
    """Render a mascot image inline. species_key: 'dog', 'cat', or anything else
    (falls back to dog+cat shown side by side as a generic 'pet' duo).
    If circle=True, crops to a circular frame (for doc-header badges)."""
    b64 = MASCOT_IMG.get(species_key)
    base_style = f"width:{size}px;height:{size}px;flex-shrink:0;{style}"
    img_style = "width:100%;height:100%;object-fit:contain;display:block"
    if circle:
        img_style = "width:100%;height:100%;object-fit:cover;border-radius:50%;display:block"
    if b64:
        name = MASCOT_NAMES.get(species_key, "PetAiNurse")
        return (f'<span style="display:inline-block;{base_style}">'
                f'<img src="data:image/jpeg;base64,{b64}" alt="{name}" style="{img_style}"/></span>')
    # unknown species or missing image → show both mascots smaller, side by side
    half = int(size*0.62)
    parts = []
    for k in ("dog","cat"):
        b = MASCOT_IMG.get(k)
        if b:
            n = MASCOT_NAMES.get(k,"")
            parts.append(f'<span style="width:{half}px;height:{half}px"><img src="data:image/jpeg;base64,{b}" alt="{n}" style="{img_style}"/></span>')
    return f'<span style="display:inline-flex;gap:2px;{base_style}">' + "".join(parts) + '</span>'

def mascot_for_pet(pet=None):
    """Return the mascot key ('dog'/'cat'/None) for the given pet profile."""
    pet = pet or st.session_state.get("pet", {})
    sp = pet.get("species_key", "")
    if sp in ("dog","cat"):
        return sp
    return None


def render_lifestyle_strip(lang="el"):
    """Three lifestyle cards (walks, vet visits, daily care) using real pet
    photographs — grounds the product in real pet-owner moments."""
    if not PET_PHOTOS:
        return
    if lang == "el":
        items = [
            ("dog_cavapoo", "Καθημερινές βόλτες", "Παρακολούθησε πώς νιώθει το κατοικίδιό σου κάθε μέρα"),
            ("cat_couch",   "Επίσκεψη στον κτηνίατρο", "Φτάσε προετοιμασμένος, με δομημένη αναφορά"),
            ("dog_cocker",  "Φροντίδα στο σπίτι", "Καταγραφή συμπτωμάτων, φαρμάκων και ιστορικού"),
        ]
    else:
        items = [
            ("dog_cavapoo", "Daily walks", "Keep track of how your pet feels every day"),
            ("cat_couch",   "Vet visits", "Arrive prepared, with a structured assessment"),
            ("dog_cocker",  "Home care", "Track symptoms, medications and history"),
        ]
    cols = st.columns(3)
    for col, (key, title, sub) in zip(cols, items):
        b64 = PET_PHOTOS.get(key)
        if not b64:
            continue
        with col:
            st.markdown(
                f'''<div style="border-radius:14px;overflow:hidden;border:1px solid #E5E7EB;background:white">
                    <img src="data:image/jpeg;base64,{b64}" style="width:100%;display:block;object-fit:cover;height:130px" />
                    <div style="padding:10px 12px">
                        <div style="font-size:13px;font-weight:700;color:#1A1A2E">{title}</div>
                        <div style="font-size:11.5px;color:#6B7280;margin-top:2px">{sub}</div>
                    </div>
                </div>''',
                unsafe_allow_html=True,
            )


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


def render_nearby_vets_geo(lang="el"):
    """Browser-geolocation widget: asks the user's device for their current
    location and opens Google Maps search for nearby veterinary clinics
    using those coordinates. Falls back gracefully if location is denied —
    the static EMERGENCY_VETS list (rendered separately) still applies."""
    # NOTE: Streamlit's st.markdown(unsafe_allow_html=True) STRIPS <script> tags,
    # so the old navigator.geolocation button never fired. We instead use a plain
    # anchor that opens Google Maps' location-aware "near me" search — the browser
    # / Google resolves the user's location automatically, no JS or iframe needed.
    if lang == "el":
        title    = "📍 Βρες κοντινά κτηνιατρεία"
        sub      = "Ανοίγει τους χάρτες Google με κτηνιατρεία κοντά στην τοποθεσία σου."
        btn      = "📍 Εύρεση κοντινών κτηνιατρείων"
        btn_open = "🚨 Επείγον κτηνιατρείο 24ω κοντά μου"
        q_near   = "κτηνιατρείο κοντά μου"
        q_open   = "επείγον κτηνιατρείο 24 ώρες κοντά μου"
    else:
        title    = "📍 Find nearby vet clinics"
        sub      = "Opens Google Maps with vet clinics near your current location."
        btn      = "📍 Find nearby vet clinics"
        btn_open = "🚨 24h emergency vet near me"
        q_near   = "veterinary clinic near me"
        q_open   = "24 hour emergency veterinary clinic near me"

    from urllib.parse import quote
    url_near = "https://www.google.com/maps/search/" + quote(q_near)
    url_open = "https://www.google.com/maps/search/" + quote(q_open)

    st.markdown(f"""
<style>
.pan-geo-card{{background:white;border:1px solid #E5E7EB;border-radius:12px;padding:16px 18px;margin-bottom:14px}}
.pan-geo-card h3{{font-size:12px;font-weight:700;letter-spacing:.1em;text-transform:uppercase;color:#6B7280;margin-bottom:6px}}
.pan-geo-sub{{font-size:12px;color:#6B7280;margin-bottom:12px}}
.pan-geo-btn{{display:block;text-align:center;text-decoration:none;border-radius:8px;padding:11px 18px;
  font-size:13px;font-weight:700;width:100%;box-sizing:border-box;margin-bottom:8px}}
.pan-geo-btn.primary{{background:#059669;color:white}}
.pan-geo-btn.primary:hover{{background:#047857}}
.pan-geo-btn.danger{{background:#DC2626;color:white}}
.pan-geo-btn.danger:hover{{background:#B91C1C}}
</style>
<div class="pan-geo-card">
  <h3>{title}</h3>
  <div class="pan-geo-sub">{sub}</div>
  <a class="pan-geo-btn primary" href="{url_near}" target="_blank" rel="noopener">{btn}</a>
  <a class="pan-geo-btn danger"  href="{url_open}" target="_blank" rel="noopener">{btn_open}</a>
</div>
""", unsafe_allow_html=True)


EMERGENCY_VETS = [
    {"name":"Αττικό Κτηνιατρικό Κέντρο (24h)","area":"Αθήνα","phone":"210 6012345","address":"Λ. Κηφισίας 100, Αθήνα"},
    {"name":"VetCity Emergency (24h)","area":"Αθήνα","phone":"210 7777777","address":"Λ. Συγγρού 50, Αθήνα"},
    {"name":"Animal Medical Center (24h)","area":"Αθήνα","phone":"210 8888888","address":"Λ. Βουλιαγμένης 80, Αθήνα"},
    {"name":"Κτηνιατρικό Επείγον Θεσσαλονίκη (24h)","area":"Θεσσαλονίκη","phone":"2310 123456","address":"Λ. Νίκης 10, Θεσσαλονίκη"},
]

def render_emergency_vets(lang="el"):
    render_nearby_vets_geo(lang)
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
    title = ("🏥 Κατάλογος Επειγόντων (Αθήνα/Θεσσαλονίκη)" if lang=="el"
             else "🏥 Directory (Athens/Thessaloniki)")
    st.markdown(f'<div style="font-weight:700;font-size:15px;margin:14px 0 10px">{title}</div>{vets_html}', unsafe_allow_html=True)

# ── HTML REPORT GENERATOR ─────────────────────────────────────────────────────
def generate_pet_html_report(pet, vitals, report_text, refs, lang="el", lab_findings=None, recs=None, species_key="dog"):
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
    filled_by = _html.escape(str(pet.get("filled_by","") or ""))
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

    recs_html = ""
    if recs and isinstance(recs, dict) and all(k in recs for k in ("activity","nutrition","lifestyle")):
        _recs_title = "📍 Εξατομικευμένες Συστάσεις" if lang=="el" else "📍 Personalized Recommendations"
        _recs_refs = MSD_RECS_REFS.get(species_key, MSD_RECS_REFS["dog"])
        _recs_labels = {
            "activity":  ("🏃 Δραστηριότητα" if lang=="el" else "🏃 Activity"),
            "nutrition": ("🥗 Διατροφή" if lang=="el" else "🥗 Nutrition"),
            "lifestyle": ("🌿 Φροντίδα στο Σπίτι" if lang=="el" else "🌿 Home Care"),
        }
        _recs_refs_lbl = "📚 Οδηγίες & βιβλιογραφία" if lang=="el" else "📚 Guidelines & references"
        _recs_boxes = ""
        for key, css_cls in (("activity","exercise"),("nutrition","nutrition"),("lifestyle","lifestyle")):
            _txt = _re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", _html.escape((recs.get(key,"") or "").strip()))
            _ref_items = "".join(
                f'<li><a href="{_html.escape(r["url"])}" target="_blank" style="color:#1E40AF;text-decoration:none">{_html.escape(r["title"])}</a></li>'
                for r in _recs_refs.get(key, [])
            )
            _recs_boxes += (
                f'<div class="recs-box {css_cls}"><div class="recs-lbl">{_recs_labels[key]}</div>'
                f'<div>{_txt}</div>'
                f'<div class="recs-refs"><div class="recs-refs-lbl">{_recs_refs_lbl}</div><ul>{_ref_items}</ul></div>'
                f'</div>'
            )
        recs_html = f'<h2>{_recs_title}</h2><div class="recs-grid">{_recs_boxes}</div>'

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
.recs-grid{{display:grid;grid-template-columns:1fr 1fr 1fr;gap:10px;margin:10px 0 16px}}
.recs-box{{border:1px solid;border-radius:10px;padding:12px 14px;font-size:12px;line-height:1.55}}
.recs-box.exercise{{background:#EFF6FF;border-color:#BFDBFE}}
.recs-box.nutrition{{background:#ECFDF5;border-color:#A7F3D0}}
.recs-box.lifestyle{{background:#FFF7ED;border-color:#FED7AA}}
.recs-lbl{{font-size:10px;font-weight:800;letter-spacing:.1em;text-transform:uppercase;color:#1F2937;margin-bottom:6px}}
.recs-refs{{margin-top:8px;padding-top:6px;border-top:1px dashed rgba(0,0,0,0.10)}}
.recs-refs-lbl{{font-size:9px;font-weight:700;letter-spacing:.1em;text-transform:uppercase;color:#6B7280;margin-bottom:4px}}
.recs-refs ul{{list-style:none;padding:0;margin:0}}.recs-refs li{{font-size:10.5px;line-height:1.4;margin-bottom:3px}}
@media print{{.recs-box{{-webkit-print-color-adjust:exact;print-color-adjust:exact}}.recs-grid{{grid-template-columns:1fr 1fr 1fr !important}}}}
@media print{{body{{padding:16px}}.pet-card,.emergency{{-webkit-print-color-adjust:exact;print-color-adjust:exact}}@page{{margin:15mm}}}}</style></head><body>
<div class="hdr"><div class="hdr-logo">🐾 PetAiNurse</div><div class="hdr-date">Κτηνιατρική Εκτίμηση<br>{ts}</div></div>
<div class="pet-card"><div class="pet-name">{name} {species}</div><div class="pet-meta">{breed} · {age} · {sex} · {weight}kg</div>
<div class="pet-detail"><strong>Κτηνίατρος:</strong> {vet}<br><strong>Παθήσεις/Αλλεργίες:</strong> {cond}<br><strong>Φάρμακα:</strong> {meds}{('<br><strong>Συμπληρώθηκε από:</strong> ' + filled_by) if filled_by and filled_by not in ('Ιδιοκτήτης','Owner') else ''}</div></div>
{vitals_sec}<h2>Κτηνιατρική Αξιολόγηση</h2>{md2h(report_text or "")}{lab_html}{recs_html}{refs_html}
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

# ─────────────────────────────────────────────────────────────────────────────
# MARKETING / EXPLAINER COMPONENTS (pet-themed, adapted from Asklepios)
# ─────────────────────────────────────────────────────────────────────────────

def render_travel_ad_banner(lang):
    """Embeddable, responsive version of the 'Pet Travel Checklist' suitcase
    poster (petainurse_travel_ad.html) for the home screen — same branding
    and copy, but fluid-width instead of a fixed 1080x1920 story poster."""
    if lang == "en":
        d = dict(
            tag_icon="🐾", tag="PETAINURSE · TRAVEL ESSENTIALS",
            h1="4 things", h1_accent="before you go.",
            sub_strong="The packing list for your pet.",
            sub="Because you never know when you'll need it.",
            ttl="🧳 Pet Travel Checklist", ttl_sub="Don't travel without these",
            items=[
                ("01","📘","Pet passport","+ vaccination booklet & microchip", False),
                ("02","🦮","Leash & collar","+ ID tag with contact details", False),
                ("03","💊","Medications & parasite prevention","Food, water, current medication list", False),
                ("04","🩺","PetAiNurse","AI vet nurse in your pocket", True),
            ],
            tagline="\u201cTell us what you're noticing. Get an assessment. Anywhere.\u201d",
            url="petainurse.com",
            pills=["🐾 MSD Vet Manual","🔒 GDPR","⚡ Free"],
        )
    else:
        d = dict(
            tag_icon="🐾", tag="PETAINURSE · TRAVEL ESSENTIALS",
            h1="4 πράγματα", h1_accent="πριν φύγετε.",
            sub_strong="Η packing list για το κατοικίδιό σου.",
            sub="Γιατί δεν ξέρεις πότε θα τον χρειαστείς.",
            ttl="🧳 Pet Travel Checklist", ttl_sub="Δεν ταξιδεύετε χωρίς αυτά",
            items=[
                ("01","📘","Διαβατήριο κατοικιδίου","+ βιβλιάριο εμβολίων & microchip", False),
                ("02","🦮","Λουρί & κολάρο","+ ταμπελάκι με στοιχεία επικοινωνίας", False),
                ("03","💊","Φάρμακα & αντιπαρασιτικά","Τρόφιμα, νερό, λίστα τρέχουσας αγωγής", False),
                ("04","🩺","PetAiNurse","AI κτηνιατρικός νοσηλευτής στην τσέπη σου", True),
            ],
            tagline="«Πες τι παρατηρείς. Λάβε εκτίμηση. Παντού.»",
            url="petainurse.com",
            pills=["🐾 MSD Vet Manual","🔒 GDPR","⚡ Δωρεάν"],
        )

    items_html = ""
    for num, icon, label, sub, is_hero in d["items"]:
        cls = "pan-ta-item pan-ta-item-hero" if is_hero else "pan-ta-item"
        items_html += f'''
        <div class="{cls}">
          <div class="pan-ta-num">{num}</div>
          <div class="pan-ta-check">✓</div>
          <div class="pan-ta-icon">{icon}</div>
          <div class="pan-ta-text">
            <div class="pan-ta-label">{label}</div>
            <div class="pan-ta-sub">{sub}</div>
          </div>
        </div>'''

    pills_html = "".join(f'<span class="pan-ta-pill">{p}</span>' for p in d["pills"])

    st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,800;1,800;1,900&family=Inter:wght@400;500;600;700;800&display=swap');
.pan-ta-wrap {{
  background: linear-gradient(180deg, #FFF7ED 0%, #FEF3C7 45%, #E0F2FE 100%);
  border-radius: 24px; padding: 32px 28px;
  margin: 12px 0 24px; font-family: 'Inter', system-ui, sans-serif;
  position: relative; overflow: hidden;
}}
.pan-ta-tag {{
  display: inline-flex; align-items: center; gap: 8px;
  background: white; border-radius: 999px; padding: 8px 18px;
  font-size: 12px; font-weight: 700; letter-spacing: 0.14em;
  color: #EA580C; box-shadow: 0 3px 10px rgba(0,0,0,0.06);
  margin-bottom: 18px;
}}
.pan-ta-h1 {{
  font-family: 'Playfair Display', Georgia, serif;
  font-size: 34px; font-weight: 800; line-height: 1.05;
  color: #1A1A2E; letter-spacing: -1px; margin-bottom: 10px;
}}
.pan-ta-h1 .accent {{ display: block; color: #DB2777; font-style: italic; }}
.pan-ta-sub {{
  font-size: 14px; color: #4B5563; line-height: 1.55; margin-bottom: 22px; max-width: 460px;
}}
.pan-ta-sub strong {{ color: #1A1A2E; font-weight: 700; }}
.pan-ta-suitcase {{
  background: white; border: 2px solid #1A1A2E; border-radius: 20px;
  padding: 22px 22px 18px; max-width: 640px; margin: 0 auto;
  box-shadow: 0 14px 36px rgba(0,0,0,0.10);
}}
.pan-ta-ttl {{ text-align: center; padding-bottom: 14px; margin-bottom: 14px; border-bottom: 2px dashed #D1D5DB; }}
.pan-ta-ttl .t {{ font-size: 14px; font-weight: 800; letter-spacing: 0.12em; text-transform: uppercase; color: #1A1A2E; margin-bottom: 4px; }}
.pan-ta-ttl .s {{ font-size: 12.5px; color: #6B7280; font-weight: 500; }}
.pan-ta-item {{
  display: flex; align-items: center; gap: 12px;
  padding: 14px 14px; background: #F9FAFB; border: 2px solid #E5E7EB;
  border-radius: 14px; margin-bottom: 10px;
}}
.pan-ta-item-hero {{
  background: linear-gradient(135deg, #FFF7ED 0%, #FCE7F3 100%);
  border: 2px solid #EA580C; box-shadow: 0 6px 16px rgba(234,88,12,0.15);
}}
.pan-ta-num {{
  font-family: 'Playfair Display', serif; font-style: italic; font-weight: 900;
  font-size: 22px; color: rgba(0,0,0,0.13); width: 30px; text-align: center; flex-shrink: 0;
}}
.pan-ta-item-hero .pan-ta-num {{ color: rgba(234,88,12,0.30); }}
.pan-ta-check {{
  width: 28px; height: 28px; border: 2px solid #1A1A2E; border-radius: 8px;
  display: flex; align-items: center; justify-content: center;
  font-size: 15px; font-weight: 900; color: #1A1A2E; background: white; flex-shrink: 0;
}}
.pan-ta-item-hero .pan-ta-check {{ background: #EA580C; border-color: #EA580C; color: white; }}
.pan-ta-icon {{ font-size: 28px; flex-shrink: 0; }}
.pan-ta-text {{ flex: 1; min-width: 0; }}
.pan-ta-label {{ font-size: 14.5px; font-weight: 800; color: #1A1A2E; line-height: 1.2; }}
.pan-ta-item-hero .pan-ta-label {{ color: #9A3412; }}
.pan-ta-sub-line {{ font-size: 12px; color: #6B7280; font-weight: 500; }}
.pan-ta-item .pan-ta-sub {{ font-size: 12px; color: #6B7280; font-weight: 500; margin: 0; max-width: none; }}
.pan-ta-item-hero .pan-ta-sub {{ color: #C2410C; font-weight: 600; }}
.pan-ta-footer {{ text-align: center; margin-top: 16px; padding-top: 14px; border-top: 2px dashed #D1D5DB; }}
.pan-ta-tagline {{ font-family: 'Playfair Display', serif; font-style: italic; font-weight: 700; font-size: 15px; color: #1A1A2E; margin-bottom: 8px; }}
.pan-ta-url {{ font-size: 15px; font-weight: 800; color: #EA580C; }}
.pan-ta-url .arrow {{ color: #DB2777; margin-right: 6px; }}
.pan-ta-pills {{
  display: flex; justify-content: center; gap: 10px; flex-wrap: wrap;
  margin-top: 18px;
}}
.pan-ta-pill {{
  background: rgba(255,255,255,0.75); border: 1px solid rgba(0,0,0,0.06);
  border-radius: 999px; padding: 6px 14px; font-size: 12px; font-weight: 600; color: #4B5563;
}}
@media (max-width: 640px) {{
  .pan-ta-wrap {{ padding: 22px 16px; border-radius: 18px; }}
  .pan-ta-h1 {{ font-size: 26px; }}
  .pan-ta-suitcase {{ padding: 16px 14px 14px; }}
}}
</style>
<div class="pan-ta-wrap">
  <div class="pan-ta-tag">{d['tag_icon']} {d['tag']}</div>
  <div class="pan-ta-h1">{d['h1']} <span class="accent">{d['h1_accent']}</span></div>
  <div class="pan-ta-sub"><strong>{d['sub_strong']}</strong><br>{d['sub']}</div>
  <div class="pan-ta-suitcase">
    <div class="pan-ta-ttl"><div class="t">{d['ttl']}</div><div class="s">{d['ttl_sub']}</div></div>
    {items_html}
    <div class="pan-ta-footer">
      <div class="pan-ta-tagline">{d['tagline']}</div>
      <div class="pan-ta-url"><span class="arrow">→</span>{d['url']}</div>
    </div>
  </div>
  <div class="pan-ta-pills">{pills_html}</div>
</div>
""", unsafe_allow_html=True)


def render_ad_banner(lang):
    """Editorial-style value-prop banner for the home/login screen.
    Pet-themed (green/teal), honest claims only — no diagnostic promises."""
    if lang == "en":
        d = {
            "pill_l":"PETAINURSE · SUMMER PET CARE", "pill_r":"🔒 GDPR · Encrypted",
            "h_l":"Summer days.", "h_m":"Smart prep.", "h_r":"Happy pets.",
            "sub":"Heatstroke, ticks, travel stress, foreign bodies — summer brings its own risks. Describe what's going on, get a structured pre-visit summary with veterinary references, and arrive at the clinic prepared. Always complements — never replaces — your vet.",
            "s1_lbl":"SUMMER RISK", "s1_text":"\"Panting heavily after a walk, won't settle, gums look red…\"",
            "s2_lbl":"VITALS",
            "s2_v1":"HR", "s2_v1v":"110 bpm",
            "s2_v2":"Temp", "s2_v2v":"39.4°C",
            "s3_lbl":"PRE-VISIT SUMMARY",
            "s3_l1":"Structured assessment",
            "s3_l2":"MSD Vet Manual references",
            "s3_l3":"Heatstroke & toxicity warnings",
            "s3_l4":"GPT-4o second opinion",
            "t1":"🇬🇷 Greek", "t2":"🔒 GDPR",
            "t3":"📋 MSD Vet Manual", "t4":"🤖 Claude + GPT-4o", "t5":"⚡ Free",
            "vetnote":"🩺 For pet owners — designed to make every vet visit faster and more informed, not to replace one. Always see your veterinarian for diagnosis and treatment.",
        }
    else:
        d = {
            "pill_l":"PETAINURSE · ΦΡΟΝΤΙΔΑ ΓΙΑ ΤΟ ΚΑΛΟΚΑΙΡΙ", "pill_r":"🔒 GDPR · Κρυπτογράφηση",
            "h_l":"Καλοκαίρι.", "h_m":"Έτοιμη πρόληψη.", "h_r":"Ήρεμο κατοικίδιο.",
            "sub":"Θερμοπληξία, τσιμπούρια, άγχος ταξιδιού, ξένα σώματα — το καλοκαίρι έχει τους δικούς του κινδύνους. Περίγραψε τι παρατηρείς και λάβε δομημένη σύνοψη με κτηνιατρικές αναφορές, ώστε να φτάσεις στο ιατρείο πιο προετοιμασμένος. Συμπληρώνει — δεν αντικαθιστά — τον κτηνίατρό σου.",
            "s1_lbl":"ΚΑΛΟΚΑΙΡΙΝΟΣ ΚΙΝΔΥΝΟΣ", "s1_text":"«Λαχανιάζει έντονα μετά τη βόλτα, δεν ηρεμεί, τα ούλα φαίνονται κόκκινα…»",
            "s2_lbl":"ΖΩΤΙΚΑ",
            "s2_v1":"HR", "s2_v1v":"110 bpm",
            "s2_v2":"Θερμ.", "s2_v2v":"39.4°C",
            "s3_lbl":"ΣΥΝΟΨΗ ΠΡΙΝ ΤΟ ΙΑΤΡΕΙΟ",
            "s3_l1":"Δομημένη εκτίμηση",
            "s3_l2":"Αναφορές MSD Vet Manual",
            "s3_l3":"Προειδοποιήσεις θερμοπληξίας & τοξικότητας",
            "s3_l4":"Δεύτερη γνώμη GPT-4o",
            "t1":"🇬🇷 Ελληνικά", "t2":"🔒 GDPR",
            "t3":"📋 MSD Vet Manual", "t4":"🤖 Claude + GPT-4o", "t5":"⚡ Δωρεάν",
            "vetnote":"🩺 Για ιδιοκτήτες κατοικιδίων — σχεδιασμένο ώστε κάθε επίσκεψη στον κτηνίατρο να γίνεται πιο γρήγορη και ενημερωμένη, όχι για να την αντικαταστήσει. Για διάγνωση και θεραπεία, πάντα ο κτηνίατρός σας.",
        }
    css = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,700;1,700;1,800;1,900&family=Inter:wght@400;500;600;700&display=swap');
.pan-ad-hero {
  background: linear-gradient(180deg, #F0FDF4 0%, #ECFDF5 100%);
  border-radius: 28px; padding: 60px 40px 36px;
  margin: 12px 0 28px; text-align: center;
  font-family: 'Inter', system-ui, sans-serif;
  border: 1px solid rgba(5, 150, 105, 0.08);
}
.pan-ad-pill {
  display: inline-flex; align-items: center; gap: 12px;
  background: white; border: 1px solid #E5E7EB;
  border-radius: 999px; padding: 8px 18px;
  font-size: 11.5px; font-weight: 700; letter-spacing: 0.1em;
  color: #059669; margin-bottom: 24px;
  box-shadow: 0 1px 2px rgba(0,0,0,0.03);
}
.pan-ad-pill .sep { color: #D1D5DB; font-weight: 400; }
.pan-ad-pill .gdpr { color: #10B981; letter-spacing: 0.04em; }
.pan-ad-title {
  font-family: 'Playfair Display', Georgia, serif;
  font-size: 60px; font-weight: 700; line-height: 1.02;
  letter-spacing: -2px; color: #1A1A2E; margin: 0 0 4px;
}
.pan-ad-title .word { display: inline-block; }
.pan-ad-title .accent {
  color: #0EA5E9; font-style: italic; font-weight: 900;
  letter-spacing: -2.5px;
}
.pan-ad-sub {
  font-size: 16.5px; color: #4B5563;
  max-width: 580px; margin: 22px auto 38px;
  line-height: 1.6; font-weight: 400;
}
.pan-ad-flow {
  display: flex; align-items: stretch; justify-content: center;
  gap: 14px; margin: 36px 0 38px; flex-wrap: wrap;
}
.pan-ad-card {
  background: white; border: 1px solid #ECEEF3;
  border-radius: 18px; padding: 18px 16px 18px;
  width: 210px; max-width: 230px; min-height: 130px;
  box-shadow: 0 3px 10px rgba(26, 26, 46, 0.05);
  display: flex; flex-direction: column;
  text-align: left;
}
.pan-ad-card-label {
  font-size: 10px; font-weight: 700; letter-spacing: 0.14em;
  color: #9CA3AF; text-transform: uppercase; margin-bottom: 10px;
  display: flex; align-items: center; gap: 6px;
}
.pan-ad-card-label .dot {
  width: 6px; height: 6px; border-radius: 50%;
}
.pan-ad-card-1 .pan-ad-card-label .dot { background: #F59E0B; }
.pan-ad-card-2 .pan-ad-card-label .dot { background: #DC2626; }
.pan-ad-card-3 .pan-ad-card-label .dot { background: #0EA5E9; }
.pan-ad-bubble {
  background: #FFFBEB; border-radius: 14px 14px 14px 4px;
  padding: 11px 13px; font-size: 13px;
  color: #1A1A2E; line-height: 1.45; font-style: italic;
  font-weight: 500;
}
.pan-ad-vitals { display: flex; flex-direction: column; gap: 8px; }
.pan-ad-vital-row {
  display: flex; align-items: center; justify-content: space-between;
  background: #FAFBFC; border-radius: 9px;
  padding: 8px 11px; font-size: 12.5px;
}
.pan-ad-vital-row .lbl { color: #6B7280; font-weight: 600; letter-spacing: 0.04em; }
.pan-ad-vital-row .val { color: #1A1A2E; font-weight: 700; font-variant-numeric: tabular-nums; }
.pan-ad-report { display: flex; flex-direction: column; gap: 7px; }
.pan-ad-report-line {
  display: flex; align-items: center; gap: 9px;
  font-size: 13px; color: #1A1A2E; font-weight: 500;
}
.pan-ad-report-line .check {
  width: 18px; height: 18px; border-radius: 50%;
  background: #ECFDF5; color: #059669;
  display: inline-flex; align-items: center; justify-content: center;
  font-size: 11px; font-weight: 700; flex-shrink: 0;
}
.pan-ad-arrow {
  display: flex; align-items: center;
  font-size: 22px; color: #0EA5E9; font-weight: 700; opacity: 0.5;
}
.pan-ad-trust {
  display: flex; justify-content: center; align-items: center;
  gap: 10px; flex-wrap: wrap; font-size: 12.5px;
  color: #6B7280; font-weight: 500;
  padding-top: 14px; border-top: 1px solid rgba(0,0,0,0.05);
  margin-top: 20px;
}
.pan-ad-trust .item { white-space: nowrap; }
.pan-ad-trust .sep-dot {
  color: #D1D5DB; font-weight: 400; font-size: 14px;
  line-height: 1;
}
.pan-ad-vetnote {
  font-size: 12px; color: #6B7280; line-height: 1.5;
  max-width: 540px; margin: 16px auto 0;
  padding-top: 14px; border-top: 1px solid rgba(0,0,0,0.05);
}
@media (max-width: 640px) {
  .pan-ad-hero { padding: 36px 22px 28px; border-radius: 22px; }
  .pan-ad-title { font-size: 36px; letter-spacing: -1.2px; }
  .pan-ad-title .accent { letter-spacing: -1.5px; }
  .pan-ad-sub { font-size: 14.5px; margin: 18px auto 28px; }
  .pan-ad-arrow { display: none; }
  .pan-ad-card { width: 100%; max-width: 340px; padding: 14px; min-height: auto; }
  .pan-ad-flow { gap: 10px; margin: 24px 0 28px; }
  .pan-ad-trust { gap: 6px; font-size: 11.5px; }
  .pan-ad-pill { font-size: 10.5px; padding: 7px 14px; }
}
</style>
"""
    body = f"""
<div class="pan-ad-hero">
  <div class="pan-ad-pill">✦ {d["pill_l"]} <span class="sep">|</span> <span class="gdpr">{d["pill_r"]}</span></div>
  <h1 class="pan-ad-title">
    <span class="word">{d["h_l"]}</span>
    <span class="word">{d["h_m"]}</span><br>
    <span class="word accent">{d["h_r"]}</span>
  </h1>
  <p class="pan-ad-sub">{d["sub"]}</p>
  <div class="pan-ad-flow">
    <div class="pan-ad-card pan-ad-card-1">
      <div class="pan-ad-card-label"><span class="dot"></span>{d["s1_lbl"]}</div>
      <div class="pan-ad-bubble">{d["s1_text"]}</div>
    </div>
    <div class="pan-ad-arrow">→</div>
    <div class="pan-ad-card pan-ad-card-2">
      <div class="pan-ad-card-label"><span class="dot"></span>{d["s2_lbl"]}</div>
      <div class="pan-ad-vitals">
        <div class="pan-ad-vital-row"><span class="lbl">❤️ {d["s2_v1"]}</span><span class="val">{d["s2_v1v"]}</span></div>
        <div class="pan-ad-vital-row"><span class="lbl">🌡️ {d["s2_v2"]}</span><span class="val">{d["s2_v2v"]}</span></div>
      </div>
    </div>
    <div class="pan-ad-arrow">→</div>
    <div class="pan-ad-card pan-ad-card-3">
      <div class="pan-ad-card-label"><span class="dot"></span>{d["s3_lbl"]}</div>
      <div class="pan-ad-report">
        <div class="pan-ad-report-line"><span class="check">✓</span>{d["s3_l1"]}</div>
        <div class="pan-ad-report-line"><span class="check">✓</span>{d["s3_l2"]}</div>
        <div class="pan-ad-report-line"><span class="check">✓</span>{d["s3_l3"]}</div>
        <div class="pan-ad-report-line"><span class="check">✓</span>{d["s3_l4"]}</div>
      </div>
    </div>
  </div>
  <div class="pan-ad-trust">
    <span class="item">{d["t1"]}</span><span class="sep-dot">·</span>
    <span class="item">{d["t2"]}</span><span class="sep-dot">·</span>
    <span class="item">{d["t3"]}</span><span class="sep-dot">·</span>
    <span class="item">{d["t4"]}</span><span class="sep-dot">·</span>
    <span class="item">{d["t5"]}</span>
  </div>
  <div class="pan-ad-vetnote">{d["vetnote"]}</div>
</div>
"""
    st.markdown(css + body, unsafe_allow_html=True)


def render_explainer_video(lang):
    """Horizontal scrollable 'how it works' cards — pet-themed walkthrough."""
    el = (lang == "el")
    if el:
        steps = [
            ("01", "🐾", "#ECFDF5", "PETAINURSE",
             "Ο ψηφιακός νοσηλευτής του κατοικίδιού σου",
             "Αξιολόγηση συμπτωμάτων με τεχνητή νοημοσύνη — γρήγορα, στα Ελληνικά."),
            ("02", "✉️", "#EEF6FF", "ΣΥΝΔΕΣΗ",
             "Σύνδεση με email",
             "Email + κωδικός μίας χρήσης. Χωρίς password, χωρίς πολύπλοκη εγγραφή."),
            ("03", "🐶", "#FFF7ED", "ΠΡΟΦΙΛ",
             "Συμπλήρωσε το προφίλ του κατοικίδιου",
             "Είδος, φυλή, ηλικία, βάρος, παθήσεις, αλλεργίες, φάρμακα."),
            ("04", "💬", "#F0EEFE", "ΣΥΜΠΤΩΜΑΤΑ",
             "Περίγραψε τι παρατηρείς",
             "Η PetAiNurse κάνει στοχευμένες ερωτήσεις — μία κάθε φορά. Μπορείς και με φωνή."),
            ("05", "❤️", "#FEF2F2", "ΖΩΤΙΚΑ",
             "Μέτρηση ζωτικών ενδείξεων",
             "Καρδιακός ρυθμός, αναπνοή, θερμοκρασία, SpO2 — με φυσιολογικά εύρη ανά είδος."),
            ("06", "📷", "#F0FDFA", "ΦΩΤΟ & ΕΞΕΤΑΣΕΙΣ",
             "Φωτογραφία ή εργαστηριακή εξέταση",
             "Σάρωση ματιών/δέρματος/ούλων ή ανέβασμα PDF αιματολογικών αποτελεσμάτων."),
            ("07", "📋", "#FDF4FF", "ΑΝΑΦΟΡΑ",
             "Δομημένη κτηνιατρική αναφορά",
             "Με αναφορές MSD Vet Manual, προειδοποιήσεις τοξικότητας και προφίλ υγείας. PDF για τον κτηνίατρο."),
        ]
        header = "Πώς λειτουργεί"
        hint   = "← σύρε για περισσότερα →"
    else:
        steps = [
            ("01", "🐾", "#ECFDF5", "PETAINURSE",
             "Your pet's digital nurse",
             "AI-powered symptom assessment — fast, in your language."),
            ("02", "✉️", "#EEF6FF", "SIGN-IN",
             "Sign in with email",
             "Email + one-time code. No password, no complex registration."),
            ("03", "🐶", "#FFF7ED", "PROFILE",
             "Fill in your pet's profile",
             "Species, breed, age, weight, conditions, allergies, medications."),
            ("04", "💬", "#F0EEFE", "SYMPTOMS",
             "Describe what you're noticing",
             "PetAiNurse asks targeted questions — one at a time. You can also use voice."),
            ("05", "❤️", "#FEF2F2", "VITALS",
             "Measure vital signs",
             "Heart rate, breathing, temperature, SpO2 — with species-specific normal ranges."),
            ("06", "📷", "#F0FDFA", "PHOTO & LABS",
             "Photo or lab results",
             "Scan eyes/skin/gums or upload a PDF of blood test results."),
            ("07", "📋", "#FDF4FF", "REPORT",
             "Structured veterinary report",
             "With MSD Vet Manual references, toxicity warnings and a health profile. PDF for your vet."),
        ]
        header = "How it works"
        hint   = "← swipe for more →"
    cards = "".join(
        f"""<div class="pan-exp-card" style="background:{tint};">
              <div class="pan-exp-num">{num}</div>
              <div class="pan-exp-icon">{icon}</div>
              <div class="pan-exp-label">{label}</div>
              <div class="pan-exp-title">{title}</div>
              <div class="pan-exp-sub">{sub}</div>
            </div>"""
        for (num, icon, tint, label, title, sub) in steps
    )
    st.markdown(
        f"""
<style>
.pan-exp-section {{
  margin: 32px 0 16px;
}}
.pan-exp-header {{
  display: flex; justify-content: space-between; align-items: baseline;
  margin: 0 4px 12px;
  font-family: 'Inter', system-ui, sans-serif;
}}
.pan-exp-header .ttl {{
  font-size: 18px; font-weight: 700; color: #1A1A2E;
  letter-spacing: -0.01em;
}}
.pan-exp-header .hint {{
  font-size: 11px; color: #9CA3AF; font-weight: 500;
  letter-spacing: 0.02em;
}}
.pan-exp-scroll {{
  display: flex; gap: 12px;
  overflow-x: auto; overflow-y: hidden;
  padding: 4px 4px 18px;
  scroll-snap-type: x mandatory;
  -webkit-overflow-scrolling: touch;
  scrollbar-width: thin;
  scrollbar-color: #CBD5E1 transparent;
}}
.pan-exp-scroll::-webkit-scrollbar {{ height: 6px; }}
.pan-exp-scroll::-webkit-scrollbar-thumb {{
  background: #CBD5E1; border-radius: 3px;
}}
.pan-exp-scroll::-webkit-scrollbar-track {{ background: transparent; }}
.pan-exp-card {{
  flex: 0 0 250px; max-width: 250px;
  border-radius: 18px; padding: 22px 20px;
  scroll-snap-align: start;
  border: 1px solid rgba(0,0,0,0.04);
  text-align: left;
  font-family: 'Inter', system-ui, sans-serif;
  box-shadow: 0 1px 3px rgba(0,0,0,0.04);
}}
.pan-exp-num {{
  font-size: 11px; font-weight: 800; letter-spacing: 0.14em;
  color: rgba(0,0,0,0.28); margin-bottom: 12px;
}}
.pan-exp-icon {{
  font-size: 30px; line-height: 1; margin-bottom: 10px;
}}
.pan-exp-label {{
  font-size: 9.5px; font-weight: 700; letter-spacing: 0.14em;
  color: #9CA3AF; text-transform: uppercase; margin-bottom: 6px;
}}
.pan-exp-title {{
  font-size: 15px; font-weight: 700; color: #1A1A2E;
  line-height: 1.35; margin-bottom: 8px;
}}
.pan-exp-sub {{
  font-size: 12.5px; color: #4B5563; line-height: 1.55;
}}
@media (max-width: 640px) {{
  .pan-exp-card {{ flex: 0 0 220px; padding: 18px 16px; }}
  .pan-exp-icon {{ font-size: 26px; }}
  .pan-exp-title {{ font-size: 14px; }}
  .pan-exp-sub {{ font-size: 12px; }}
}}
</style>
<div class="pan-exp-section">
  <div class="pan-exp-header"><span class="ttl">{header}</span><span class="hint">{hint}</span></div>
  <div class="pan-exp-scroll">{cards}</div>
</div>
""",
        unsafe_allow_html=True,
    )


def render_home():
    lang = st.session_state.lang

    c1,c2 = st.columns([6,1])
    with c2:
        if st.button("🇬🇧 EN" if lang=="el" else "🇬🇷 ΕΛ"):
            st.session_state.lang = "en" if lang=="el" else "el"; st.rerun()

    st.markdown(f'''<div class="pet-hero">
        <div style="display:flex;justify-content:center;gap:10px;margin-bottom:4px">
            <div style="background:white;border-radius:18px;padding:8px 14px;box-shadow:0 4px 14px rgba(0,0,0,0.10)">{render_mascot("dog", size=120)}</div>
            <div style="background:white;border-radius:18px;padding:8px 14px;box-shadow:0 4px 14px rgba(0,0,0,0.10)">{render_mascot("cat", size=120)}</div>
        </div>
        <h1>{t("title")}</h1>
        <p>{t("subtitle")}</p>
        <div class="pet-tagline">{t("tagline")}</div>
    </div>''', unsafe_allow_html=True)

    _render_disclaimer_strip()

    # Pet Travel Checklist banner (suitcase/checklist style)
    render_travel_ad_banner(lang)

    render_lifestyle_strip(lang)

    col1,col2,col3 = st.columns([1,2,1])
    with col2:
        if st.button(t("start"), type="primary", use_container_width=True):
            st.session_state.screen="intake"; st.rerun()

    st.markdown("---")
    f1,f2,f3,f4 = st.columns(4)
    with f1:
        st.markdown('<div class="card"><div style="font-size:32px">📋</div><h3 style="margin-top:12px">MSD Veterinary Manual</h3><p style="font-size:13px;color:#6B7280">Κάθε αναφορά υποστηρίζεται από το MSD Vet Manual — χρυσό πρότυπο κτηνιατρικής.</p></div>', unsafe_allow_html=True)
    with f2:
        st.markdown('''<div class="card"><div style="font-size:32px">⚠️</div><h3 style="margin-top:12px">Τοξικότητα & Ασφάλεια</h3>
            <p style="font-size:13px;color:#6B7280">Αυτόματη ανίχνευση τοξικών ουσιών — ιδιαίτερα κρίσιμο για γάτες.</p>
            <div style="margin-top:8px;display:flex;flex-wrap:wrap;gap:5px">
                <span style="background:#FEF2F2;color:#991B1B;font-size:11px;font-weight:600;padding:3px 8px;border-radius:99px">🍫 Σοκολάτα</span>
                <span style="background:#FEF2F2;color:#991B1B;font-size:11px;font-weight:600;padding:3px 8px;border-radius:99px">🧅 Κρεμμύδι</span>
                <span style="background:#FEF2F2;color:#991B1B;font-size:11px;font-weight:600;padding:3px 8px;border-radius:99px">💊 Παρακεταμόλη</span>
            </div></div>''', unsafe_allow_html=True)
    with f3:
        st.markdown('<div class="card"><div style="font-size:32px">👥</div><h3 style="margin-top:12px">Για Pet Sitters</h3><p style="font-size:13px;color:#6B7280">Φροντίζεις κατοικίδιο άλλου; Φτιάξε γρήγορη αναφορά για τον ιδιοκτήτη ή τον κτηνίατρο.</p></div>', unsafe_allow_html=True)
    with f4:
        st.markdown('<div class="card"><div style="font-size:32px">🇬🇷</div><h3 style="margin-top:12px">pet.gov.gr</h3><p style="font-size:13px;color:#6B7280">Σύνδεσμοι προς τις επίσημες υπηρεσίες του Εθνικού Μητρώου Ζώων Συντροφιάς.</p></div>', unsafe_allow_html=True)

    # "How it works" walkthrough
    render_explainer_video(lang)

    st.markdown(f'<div class="emergency-vet">{t("emergency_vet")}</div>', unsafe_allow_html=True)



def _render_intake_progress(step, total, lang):
    """Small inline progress bar for the grouped intake sub-steps."""
    pct = int(((step+1)/total)*100)
    label = (f"Βήμα {step+1} από {total}" if lang=="el" else f"Step {step+1} of {total}")
    st.markdown(f"""
<div style="margin:4px 0 14px">
  <div style="display:flex;justify-content:space-between;font-size:11px;color:#9CA3AF;
              font-weight:600;letter-spacing:.04em;margin-bottom:6px">
    <span>{label}</span><span>{pct}%</span>
  </div>
  <div style="background:#F3F4F6;border-radius:99px;height:6px;overflow:hidden">
    <div style="background:#059669;width:{pct}%;height:6px;border-radius:99px;transition:width .2s"></div>
  </div>
</div>""", unsafe_allow_html=True)


def render_intake():
    render_stepper("intake")
    lang = st.session_state.lang
    pet = st.session_state.pet
    draft = st.session_state.intake_draft
    step = st.session_state.intake_step

    STEP_HEADERS = {
        0: dict(icon="🐾",
                title_el="Πες μας για το κατοικίδιό σου", title_en="Tell us about your pet",
                sub_el="Ποιος συμπληρώνει, όνομα και είδος", sub_en="Who's filling this in, name and species"),
        1: dict(icon="📏",
                title_el="Βασικά στοιχεία", title_en="Basic details",
                sub_el="Φυλή, ηλικία, φύλο, βάρος", sub_en="Breed, age, sex, weight"),
        2: dict(icon="🩹",
                title_el="Ιστορικό υγείας", title_en="Health history",
                sub_el="Microchip, εμβολιασμοί, παθήσεις/αλλεργίες", sub_en="Microchip, vaccinations, conditions/allergies"),
        3: dict(icon="💊",
                title_el="Φάρμακα & κτηνίατρος", title_en="Medications & vet",
                sub_el="Τρέχουσα αγωγή και στοιχεία κτηνιάτρου (προαιρετικά)",
                sub_en="Current medications and vet details (optional)"),
    }
    hdr = STEP_HEADERS[step]
    render_doc_header(
        hdr["title_el"], hdr["title_en"], icon=hdr["icon"],
        sub_el=hdr["sub_el"], sub_en=hdr["sub_en"],
    )
    _render_disclaimer_strip()
    _render_intake_progress(step, 4, lang)

    # ── STEP 0: who's filling this in + name + species ────────────────────────
    if step == 0:
        filler_opts_el = ["Ιδιοκτήτης", "Pet Sitter", "Κτηνίατρος/Προσωπικό κλινικής"]
        filler_opts_en = ["Owner", "Pet Sitter", "Vet/Clinic staff"]
        filler_opts = filler_opts_el if lang=="el" else filler_opts_en
        prev_filler = draft.get("filled_by", pet.get("filled_by", filler_opts[0]))
        if prev_filler not in filler_opts: prev_filler = filler_opts[0]
        filled_by = st.selectbox(
            ("Η αναφορά συμπληρώνεται από" if lang=="el" else "This assessment is being filled in by"),
            filler_opts, index=filler_opts.index(prev_filler))
        if filled_by != filler_opts[0]:
            st.caption(("ℹ️ Η αναφορά θα αναφέρει ότι συμπληρώθηκε από " + filled_by.lower()
                        + " — χρήσιμο όταν στέλνεις την αναφορά στον ιδιοκτήτη ή τον κτηνίατρο.")
                       if lang=="el" else
                       ("ℹ️ The report will note it was filled in by a " + filled_by.lower()
                        + " — useful when sharing it with the owner or vet."))

        c1,c2 = st.columns([2,1])
        with c1:
            name = st.text_input(t("pet_name"), value=draft.get("name", pet.get("name","")), placeholder="Μπόμπης")
            if st.session_state.get("_intake_show_errors") and not name:
                st.markdown(
                    '<div style="color:#DC2626;font-size:12px;margin:-8px 0 8px">'
                    + ("⚠️ Το όνομα είναι απαραίτητο" if lang=="el" else "⚠️ Name is required")
                    + '</div>', unsafe_allow_html=True)
        with c2:
            species_opts = SPECIES[lang]
            prev_sp = draft.get("species_label", pet.get("species_label", species_opts[0]))
            if prev_sp not in species_opts: prev_sp = species_opts[0]
            species_label = st.selectbox(t("species"), species_opts,
                                         index=species_opts.index(prev_sp))

        col_b, col_n = st.columns([1,3])
        with col_b:
            if st.button(t("back")): st.session_state.screen="home"; st.rerun()
        with col_n:
            if st.button(t("next"), type="primary", use_container_width=True):
                if name:
                    draft["filled_by"] = filled_by
                    draft["name"] = name
                    draft["species_label"] = species_label
                    draft["species_key"] = SPECIES_KEY.get(species_label, "dog")
                    st.session_state.intake_draft = draft
                    st.session_state.intake_step = 1
                    st.session_state["_intake_show_errors"] = False
                    st.rerun()
                else:
                    st.session_state["_intake_show_errors"] = True
                    st.rerun()
        return

    # ── STEP 1: breed, age, sex, weight ────────────────────────────────────────
    if step == 1:
        species_key = draft.get("species_key", "dog")
        if species_key == "dog":
            breeds = DOG_BREEDS_EL if lang=="el" else DOG_BREEDS_EN
        elif species_key == "cat":
            breeds = CAT_BREEDS_EL if lang=="el" else CAT_BREEDS_EN
        else:
            breeds = ["—"]
        prev_breed = draft.get("breed", pet.get("breed", breeds[0]))
        if prev_breed not in breeds: prev_breed = breeds[0]
        breed = st.selectbox(t("breed"), breeds, index=breeds.index(prev_breed))

        c1,c2,c3,c4 = st.columns(4)
        with c1: age_y = st.number_input(t("age_y"), min_value=0, max_value=30,
                                          value=draft.get("age_y", pet.get("age_y",0)))
        with c2: age_m = st.number_input(t("age_m"), min_value=0, max_value=11,
                                          value=draft.get("age_m", pet.get("age_m",0)))
        with c3:
            sex_opts = [t("male"), t("female"), t("neutered")]
            prev_sex = draft.get("sex", pet.get("sex", sex_opts[0]))
            if prev_sex not in sex_opts: prev_sex = sex_opts[0]
            sex = st.selectbox(t("sex"), sex_opts, index=sex_opts.index(prev_sex))
        with c4:
            prev_weight = draft.get("weight", pet.get("weight"))
            weight = st.number_input(t("weight"), min_value=0.0, max_value=150.0,
                                       value=(float(prev_weight) if prev_weight else None),
                                       placeholder="5.0", format="%.1f")

        col_b, col_n = st.columns([1,3])
        with col_b:
            if st.button(t("back")): st.session_state.intake_step = 0; st.rerun()
        with col_n:
            if st.button(t("next"), type="primary", use_container_width=True):
                draft["breed"] = breed
                draft["age_y"] = age_y
                draft["age_m"] = age_m
                draft["sex"] = sex
                draft["weight"] = weight
                st.session_state.intake_draft = draft
                st.session_state.intake_step = 2
                st.rerun()
        return

    # ── STEP 2: microchip, vaccinations, conditions ────────────────────────────
    if step == 2:
        microchip = st.text_input(t("microchip"), value=draft.get("microchip", pet.get("microchip","")),
                                   placeholder="941000123456789")
        st.caption("💡 Προαιρετικό — μπορείς να το προσθέσεις αργότερα." if lang=="el"
                   else "💡 Optional — you can add this later.")
        vax_opts = [t("yes"), t("no"), t("unknown")]
        prev_vax = draft.get("vaccinations", pet.get("vaccinations", vax_opts[0]))
        if prev_vax not in vax_opts: prev_vax = vax_opts[0]
        vaccinations = st.selectbox(t("vaccinations"), vax_opts, index=vax_opts.index(prev_vax))
        conditions = st.text_area(t("conditions"), value=draft.get("conditions", pet.get("conditions","")), height=80,
                                   placeholder="Π.χ. Αλλεργία σε πρωτεΐνες σιταριού, χρόνια γαστρίτιδα")

        col_b, col_n = st.columns([1,3])
        with col_b:
            if st.button(t("back")): st.session_state.intake_step = 1; st.rerun()
        with col_n:
            if st.button(t("next"), type="primary", use_container_width=True):
                draft["microchip"] = microchip
                draft["vaccinations"] = vaccinations
                draft["conditions"] = conditions
                st.session_state.intake_draft = draft
                st.session_state.intake_step = 3
                st.rerun()
        return

    # ── STEP 3: medications + vet, then submit ─────────────────────────────────
    st.markdown(f"**{t('meds')}**")
    st.caption("💡 Προαιρετικό — άφησέ το κενό αν δεν παίρνει φάρμακα." if lang=="el"
               else "💡 Optional — leave blank if no medications.")
    if not st.session_state.med_inputs:
        prev = draft.get("meds_raw", pet.get("meds_raw",""))
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

    vet_name = st.text_input(t("vet_name"), value=draft.get("vet_name", pet.get("vet_name","")),
                              placeholder="Π.χ. Κτηνιατρείο Αθήνας, Δρ. Παπαδόπουλος")
    st.caption("💡 Προαιρετικό — μπορείς να το προσθέσεις αργότερα." if lang=="el"
               else "💡 Optional — you can add this later.")

    col_b, col_n = st.columns([1,3])
    with col_b:
        if st.button(t("back")): st.session_state.intake_step = 2; st.rerun()
    with col_n:
        if st.button(t("next"), type="primary", use_container_width=True):
            # Toxicity check on medications
            species_key = draft.get("species_key", "dog")
            tox_warns = check_toxicity(species_key, meds_raw)
            if tox_warns:
                for w in tox_warns:
                    st.error(w)
                st.stop()
            st.session_state.pet = {
                "name": draft.get("name",""), "species_key": species_key,
                "species_label": draft.get("species_label",""),
                "breed": draft.get("breed",""), "age_y": draft.get("age_y",0),
                "age_m": draft.get("age_m",0), "sex": draft.get("sex",""),
                "weight": draft.get("weight"), "microchip": draft.get("microchip",""),
                "vaccinations": draft.get("vaccinations",""),
                "conditions": draft.get("conditions",""),
                "meds_raw": meds_raw, "vet_name": vet_name,
                "filled_by": draft.get("filled_by",""),
            }
            st.session_state.intake_step = 0
            st.session_state.intake_draft = {}
            st.session_state.screen = "vitals"
            st.rerun()


def render_vitals():
    render_stepper("vitals")
    pet  = st.session_state.pet
    lang = st.session_state.lang
    sp   = pet.get("species_key","dog")
    rng  = VITAL_RANGES.get(sp, VITAL_RANGES["dog"])
    nm = pet.get("name","")
    render_doc_header(
        "Πώς είναι οι ζωτικές ενδείξεις;", "How are the vital signs?",
        icon="❤️",
        sub_el=(f"Μέτρησε ή σάρωσε για {nm}" if nm else "Χειροκίνητη μέτρηση ή σάρωση φωτογραφίας"),
        sub_en=(f"Measure or scan for {nm}" if nm else "Manual entry or photo scan"),
        mascot_key=mascot_for_pet(pet),
    )
    _render_disclaimer_strip()

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
        sel_idx = st.radio(
            ("Τύπος σάρωσης" if lang=="el" else "Scan type"),
            scan_labels, horizontal=True, key="scan_type_radio",
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
                # Also keep a running list of all photo analyses so they can
                # be shown as evidence cards in the final report (mirrors
                # the Asklepios "photo findings" card).
                st.session_state.setdefault("photo_findings", []).append({
                    "scan_label": sel_idx,
                    "analysis": analysis,
                })

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
        if st.button(t("back")):
            st.session_state.intake_step = 3
            st.session_state.intake_draft = dict(st.session_state.pet)
            st.session_state.med_inputs = []  # re-derive from pet.meds_raw
            st.session_state.screen="intake"; st.rerun()
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
    nm = pet.get("name","")
    render_doc_header(
        "Ας μιλήσουμε για τα συμπτώματα", "Let's talk about the symptoms",
        icon="💬",
        sub_el=(f"Συνομιλία για τον/την {nm} — μία ερώτηση κάθε φορά" if nm else "Πες τι παρατηρείς — μία ερώτηση κάθε φορά"),
        sub_en=(f"Chat about {nm} — one question at a time" if nm else "Tell us what you're noticing — one question at a time"),
        mascot_key=mascot_for_pet(pet),
    )
    render_vitals_summary()
    _render_disclaimer_strip()

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
            st.caption(
                "ℹ️ Πάτησε το κουμπί μικροφώνου για να ξεκινήσεις την ηχογράφηση. "
                "Όταν τελειώσεις, πάτησε ΞΑΝΑ το ίδιο κουμπί για να σταματήσεις. "
                "Μετά περίμενε λίγα δευτερόλεπτα για τη μεταγραφή, έλεγξε/διόρθωσε το κείμενο "
                "και πάτησε «Αποστολή»."
                if lang=="el" else
                "ℹ️ Press the microphone button to start recording. "
                "When you're done, press the SAME button AGAIN to stop. "
                "Then wait a few seconds for transcription, review/edit the text, "
                "and press «Send»."
            )
            audio = st.audio_input(
                ("Ηχογράφηση" if lang=="el" else "Record"),
                key=f"pet_voice_{st.session_state._voice_widget_counter}")
            if audio:
                with st.spinner("Whisper..." if lang=="el" else "Transcribing..."):
                    _mime = getattr(audio, "type", "audio/wav") or "audio/wav"
                    _ext = {"audio/wav":"wav","audio/x-wav":"wav","audio/webm":"webm",
                            "audio/mp4":"mp4","audio/mpeg":"mp3","audio/ogg":"ogg"}.get(_mime, "wav")
                    txt, err = transcribe_audio(audio.read(), lang=lang, mime=_mime, filename=f"recording.{_ext}")
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
    nm = pet.get("name","")
    render_doc_header(
        "Η εκτίμηση για το κατοικίδιό σου", "Your pet's assessment",
        icon="📋",
        sub_el=(f"Δομημένη αναφορά για {nm} — αποθήκευσε ή τύπωσε για τον κτηνίατρο" if nm else "Δομημένη αναφορά με τεκμηρίωση"),
        sub_en=(f"Structured report for {nm} — save or print for your vet" if nm else "Structured assessment with references"),
        mascot_key=mascot_for_pet(pet),
    )
    st.caption(f"{pet.get('name','')} {pet.get('species_label','')} · {pet.get('breed','')} · {datetime.now().strftime('%d %b %Y %H:%M')}")
    _render_disclaimer_strip()
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
            st.session_state.report = sanitize_ai_text(result)
            st.session_state.report_gpt = ""
            st.session_state["_gpt_integrated"] = False

        # Personalized recommendations (activity / nutrition / home-care)
        with st.spinner("📍 Εξατομικευμένες συστάσεις..." if lang=="el" else "📍 Personalized recommendations..."):
            st.session_state.report_recs = generate_pet_recommendations(
                pet, vitals_text, conversation, st.session_state.report, lang)

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

    # Photo findings card — if the user uploaded any photos during intake/triage,
    # the AI vision analyses become visible evidence in the final report.
    # Mirrors the Asklepios "📷 PHOTO FINDINGS" card.
    _pfs = st.session_state.get("photo_findings") or []
    if isinstance(_pfs, list) and _pfs:
        _pf_title = ("📷 ΕΥΡΗΜΑΤΑ ΑΠΟ ΦΩΤΟΓΡΑΦΙΕΣ" if lang=="el" else "📷 PHOTO FINDINGS")
        _pf_count = len(_pfs)
        import html as _html_pf, re as _re_pf
        def _flat_pf(txt): return _re_pf.sub(r"\s+", " ", (txt or "").strip())
        _cards_html = ""
        for i, pf in enumerate(_pfs, 1):
            _label = _html_pf.escape(pf.get("scan_label","—"))
            _analysis = _flat_pf(pf.get("analysis",""))
            _analysis = _html_pf.escape(_analysis)
            _analysis = _re_pf.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", _analysis)
            _cards_html += (
                f'<div class="pf-item">'
                f'<div class="pf-head"><span class="pf-num">{i}</span><span class="pf-label">{_label}</span></div>'
                f'<div class="pf-body">{_analysis}</div>'
                f'</div>'
            )
        st.markdown(
            f'<style>'
            f'.pf-card{{background:white;border:1px solid #E5E7EB;border-radius:14px;padding:22px 24px;margin:18px 0;font-family:Inter,system-ui,sans-serif;box-shadow:0 1px 3px rgba(0,0,0,0.04)}}'
            f'.pf-title{{font-size:11px;font-weight:700;letter-spacing:0.14em;color:#6B7280;text-transform:uppercase;border-bottom:2px solid #E5E7EB;padding-bottom:10px;margin-bottom:14px}}'
            f'.pf-item{{padding:14px 0;border-bottom:1px solid #F3F4F6}}'
            f'.pf-item:last-child{{border-bottom:none;padding-bottom:0}}'
            f'.pf-head{{display:flex;align-items:center;gap:10px;margin-bottom:8px}}'
            f'.pf-num{{background:#DBEAFE;color:#1E40AF;font-size:11px;font-weight:700;width:22px;height:22px;border-radius:50%;display:inline-flex;align-items:center;justify-content:center}}'
            f'.pf-label{{font-size:13.5px;font-weight:700;color:#111827}}'
            f'.pf-body{{font-size:13px;color:#374151;line-height:1.6}}'
            f'.pf-body strong{{color:#1F2937}}'
            f'</style>'
            f'<div class="pf-card"><div class="pf-title">{_pf_title} · {_pf_count}</div>{_cards_html}</div>',
            unsafe_allow_html=True,
        )

    # Lab findings card — same styling as the photo card with a green accent
    # for laboratory data. Mirrors the Asklepios "🧪 LAB FINDINGS" card.
    _lfs = st.session_state.get("lab_findings") or []
    if isinstance(_lfs, list) and _lfs:
        _lf_title = ("🧪 ΕΥΡΗΜΑΤΑ ΕΡΓΑΣΤΗΡΙΑΚΩΝ ΕΞΕΤΑΣΕΩΝ" if lang=="el" else "🧪 LAB FINDINGS")
        _lf_count = len(_lfs)
        import html as _html_lf, re as _re_lf
        def _flat_lf(txt): return _re_lf.sub(r"\s+", " ", (txt or "").strip())
        _lf_cards = ""
        for i, lf in enumerate(_lfs, 1):
            _fname = _html_lf.escape(lf.get("file_name","—"))
            _an = _html_lf.escape(_flat_lf(lf.get("analysis","")))
            _an = _re_lf.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", _an)
            _lf_cards += (
                f'<div class="lf-item">'
                f'<div class="lf-head"><span class="lf-num">{i}</span>'
                f'<span class="lf-label">📄 {_fname}</span></div>'
                f'<div class="lf-body">{_an}</div>'
                f'</div>'
            )
        st.markdown(
            f'<style>'
            f'.lf-card{{background:white;border:1px solid #E5E7EB;border-radius:14px;padding:22px 24px;margin:18px 0;font-family:Inter,system-ui,sans-serif;box-shadow:0 1px 3px rgba(0,0,0,0.04)}}'
            f'.lf-title{{font-size:11px;font-weight:700;letter-spacing:0.14em;color:#6B7280;text-transform:uppercase;border-bottom:2px solid #E5E7EB;padding-bottom:10px;margin-bottom:14px}}'
            f'.lf-item{{padding:14px 0;border-bottom:1px solid #F3F4F6}}'
            f'.lf-item:last-child{{border-bottom:none;padding-bottom:0}}'
            f'.lf-head{{display:flex;align-items:center;gap:10px;margin-bottom:8px}}'
            f'.lf-num{{background:#D1FAE5;color:#065F46;font-size:11px;font-weight:700;width:22px;height:22px;border-radius:50%;display:inline-flex;align-items:center;justify-content:center}}'
            f'.lf-label{{font-size:13.5px;font-weight:700;color:#111827}}'
            f'.lf-body{{font-size:13px;color:#374151;line-height:1.6}}'
            f'.lf-body strong{{color:#1F2937}}'
            f'</style>'
            f'<div class="lf-card"><div class="lf-title">{_lf_title} · {_lf_count}</div>{_lf_cards}</div>',
            unsafe_allow_html=True,
        )

    # Personalized recommendations (activity / nutrition / home-care),
    # mirroring the Asklepios "📍 Εξατομικευμένες Συστάσεις" cards.
    if st.session_state.get("report_recs"):
        render_pet_recommendations(st.session_state.report_recs, sp, lang)

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
                        st.session_state.report_gpt = sanitize_ai_text(gpt4o(
                            prompt=f"Pet: {pet.get('name')}, {pet.get('species_label')} ({pet.get('breed')}), {pet.get('age_y')}y\n\nPetAiNurse's assessment:\n{st.session_state.report}\n\nDo you agree with this veterinary assessment? Provide additions, corrections, or alternative differentials. Be specific and species-appropriate.",
                            system=petainurse_system(), max_tokens=3000))
                    st.rerun()
            else:
                st.markdown(st.session_state.report_gpt)
                # Integration: if the second opinion adds value, the user can fold
                # it into the main report so it shows up in the on-screen
                # assessment AND in every downstream export (PDF/HTML).
                st.divider()
                if st.session_state.get("_gpt_integrated"):
                    st.success("✓ " + ("Ενσωματώθηκε στην τελική εκτίμηση παραπάνω και στα exports."
                                       if lang=="el" else
                                       "Integrated into the final assessment above and in all exports."))
                else:
                    if st.button(("➕ Ενσωμάτωση στην τελική εκτίμηση" if lang=="el"
                                  else "➕ Integrate into final assessment"),
                                 type="primary", use_container_width=True, key="pet_gpt_integrate"):
                        _hdr = "## " + ("ΔΕΥΤΕΡΗ ΓΝΩΜΗ (GPT-4o)" if lang=="el"
                                        else "SECOND OPINION (GPT-4o)")
                        st.session_state.report = (
                            (st.session_state.report or "").rstrip()
                            + "\n\n---\n\n" + _hdr + "\n\n"
                            + (st.session_state.report_gpt or "").strip()
                        )
                        st.session_state["_gpt_integrated"] = True
                        st.rerun()
                    st.caption(("💡 Προσθέτει τη δεύτερη γνώμη ως ξεχωριστή ενότητα στην αναφορά "
                                "και σε όλα τα exports (PDF/HTML)."
                                if lang=="el" else
                                "💡 Adds the second opinion as a separate section in the report "
                                "and in every export (PDF/HTML)."))

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
    c1,c2,c3,c4 = st.columns(4)
    with c1:
        if st.button("← "+("Νέα Εκτίμηση" if lang=="el" else "New Assessment"), use_container_width=True):
            _hero_seen = st.session_state.get("_hero_seen", False)
            for k,v in defaults.items(): st.session_state[k]=v
            st.session_state["_hero_seen"] = _hero_seen
            st.rerun()
    with c2:
        st.download_button("📄 TXT", data=st.session_state.report,
                           file_name=fname+".txt", mime="text/plain", use_container_width=True)
    with c3:
        st.download_button("📄 PDF/HTML",
                           data=generate_pet_html_report(pet, st.session_state.vitals,
                                                          st.session_state.report, st.session_state.report_refs, lang,
                                                          lab_findings=st.session_state.lab_findings,
                                                          recs=st.session_state.get("report_recs"),
                                                          species_key=sp),
                           file_name=fname+".html", mime="text/html", use_container_width=True,
                           help="Open in browser → Ctrl+P → Save as PDF")
    with c4:
        import re as _re_wa
        v = st.session_state.vitals or {}
        wa_lines = [
            "🐾 PetAiNurse",
            f"{('Κατοικίδιο' if lang=='el' else 'Pet')}: {pet.get('name','')} "
            f"{pet.get('species_label','')} ({pet.get('breed','')}), "
            f"{pet.get('age_y',0)}y {pet.get('age_m',0)}m · {pet.get('sex','')}",
        ]
        vbits = []
        if v.get("hr"):   vbits.append(f"HR {v['hr']}bpm")
        if v.get("br"):   vbits.append(f"BR {v['br']}/min")
        if v.get("temp"): vbits.append(f"T {v['temp']}°C")
        if v.get("spo2"): vbits.append(f"SpO2 {v['spo2']}%")
        if vbits:
            wa_lines.append(("Ζωτικά: " if lang=="el" else "Vitals: ") + ", ".join(vbits))
        # Clean markdown so it reads well in WhatsApp
        rep = _re_wa.sub(r"[#*>`|]", "", st.session_state.report or "").strip()
        rep = _re_wa.sub(r"\n{3,}", "\n\n", rep)
        # Cap length — wa.me pre-fill fails on very long URLs
        if len(rep) > 1500:
            rep = rep[:1500].rsplit("\n",1)[0].rstrip() + ("\n…(πλήρης αναφορά στο PDF)" if lang=="el" else "\n…(full report in PDF)")
        if rep:
            wa_lines += ["", rep]
        # Personalized recommendations (plain emoji-prefixed lines)
        _r = st.session_state.get("report_recs")
        if _r and any(_r.get(k) for k in ("activity","nutrition","lifestyle")):
            wa_lines += ["", ("📍 Συστάσεις:" if lang=="el" else "📍 Recommendations:")]
            if _r.get("activity"):  wa_lines.append(("🏃 Δραστηριότητα: " if lang=="el" else "🏃 Activity: ") + _r["activity"])
            if _r.get("nutrition"): wa_lines.append(("🥗 Διατροφή: " if lang=="el" else "🥗 Nutrition: ") + _r["nutrition"])
            if _r.get("lifestyle"): wa_lines.append(("🌿 Φροντίδα: " if lang=="el" else "🌿 Home Care: ") + _r["lifestyle"])
        wa_lines += ["", "---", "⚠️ AI-generated. petainurse.com"]
        wa_msg = "\n".join(wa_lines)
        wa_url = "https://wa.me/?text=" + urllib.parse.quote(wa_msg)
        st.markdown(
            f'<a href="{wa_url}" target="_blank" '
            f'style="display:flex;align-items:center;justify-content:center;height:38.4px;'
            f'border-radius:8px;text-decoration:none;font-weight:600;font-size:14px;'
            f'color:white;background:#25D366">📤 WhatsApp</a>',
            unsafe_allow_html=True,
        )

# ── FULL-PAGE LOGIN SCREEN (shown when auth is enabled and user not logged in) ─
def render_hero_screen():
    """Full marketing 'hero' landing screen, shown once before the login
    form (or before 'home' when auth is disabled). Mirrors the standalone
    PetAiNurse marketing site layout: top bar with CTA, big headline with
    mascots + floating feature cards, 'how it works' steps, and audience
    cards — all using the existing illustrated Perro/Gato mascots."""
    lang = st.session_state.lang

    if lang == "el":
        d = dict(
            kicker="ΟΙ ΣΩΣΤΕΣ ΠΛΗΡΟΦΟΡΙΕΣ. ΚΑΛΥΤΕΡΗ ΦΡΟΝΤΙΔΑ.",
            h1="Περίγραψε τι", h1_accent="παρατηρείς",
            h1_end="στο κατοικίδιό σου.",
            sub="Το PetAiNurse οργανώνει τα συμπτώματα και τις παρατηρήσεις σου ώστε να έχεις καλύτερη εικόνα πριν επικοινωνήσεις με κτηνίατρο.",
            cta_primary="✦ Ξεκίνα αξιολόγηση συμπτωμάτων",
            cta_secondary="📄 Δημιούργησε αναφορά για τον κτηνίατρο",
            disclaimer="Το PetAiNurse δεν παρέχει κτηνιατρική διάγνωση και δεν αντικαθιστά τον κτηνίατρο. Σε επείγουσες καταστάσεις επικοινώνησε άμεσα με επαγγελματία υγείας ζώων.",
            card1="Καταγραφή συμπτωμάτων και συμπεριφοράς",
            card2="Εντοπισμός πιθανών παραγόντων",
            card3="Αναφορά για τον κτηνίατρο με οργανωμένες πληροφορίες",
            steps_title="Πώς λειτουργεί",
            steps=[
                ("1","💬","Καταγράφεις","συμπτώματα και παρατηρήσεις"),
                ("2","🧠","Το PetAiNurse οργανώνει","τις πληροφορίες"),
                ("3","🔍","Εντοπίζει","πιθανούς παράγοντες που αξίζει να συζητηθούν"),
                ("4","📄","Δημιουργεί","αναφορά για τον κτηνίατρο"),
                ("5","👤","Η τελική αξιολόγηση","γίνεται πάντα από κτηνίατρο"),
            ],
            audience_title="Για όλους όσοι φροντίζουν ζώα",
            aud1_t="Για Pet Parents", aud1_d="Κατανόησε καλύτερα τα συμπτώματα του κατοικίδιου σου και επικοινώνησε πιο αποτελεσματικά με τον κτηνίατρο.",
            aud2_t="Για Pet Sitters", aud2_d="Κατέγραψε με ακρίβεια παρατηρήσεις κατά τη φροντίδα ενός ζώου και ενημέρωσε υπεύθυνα τον κηδεμόνα ή τον κτηνίατρο.",
            aud3_t="Για Κτηνιάτρους", aud3_d="Ένα επιπρόσθετο εργαλείο συλλογής οργανωμένου ιστορικού και προετοιμασίας της επίσκεψης.",
            more_label="Μάθε περισσότερα →",
            cta_band_t="Ξεκίνα τώρα και φρόντισε με γνώση.",
            cta_band_s="Μια καλύτερη συζήτηση με τον κτηνίατρο ξεκινάει εδώ.",
            cta_band_btn="✦ Ξεκίνα αξιολόγηση συμπτωμάτων",
            nav_start="Ξεκίνα τώρα",
        )
    else:
        d = dict(
            kicker="THE RIGHT INFO. BETTER CARE.",
            h1="Describe what", h1_accent="you're noticing",
            h1_end="in your pet.",
            sub="PetAiNurse organizes your pet's symptoms and observations so you have a clearer picture before contacting a vet.",
            cta_primary="✦ Start symptom assessment",
            cta_secondary="📄 Create a report for your vet",
            disclaimer="PetAiNurse does not provide veterinary diagnosis and does not replace your vet. In emergencies, contact an animal health professional immediately.",
            card1="Logging symptoms and behaviour",
            card2="Identifying possible factors",
            card3="A report for your vet with organized information",
            steps_title="How it works",
            steps=[
                ("1","💬","You log","symptoms and observations"),
                ("2","🧠","PetAiNurse organizes","the information"),
                ("3","🔍","It identifies","possible factors worth discussing"),
                ("4","📄","It creates","a report for your vet"),
                ("5","👤","The final assessment","is always made by a vet"),
            ],
            audience_title="For everyone who cares for animals",
            aud1_t="For Pet Parents", aud1_d="Better understand your pet's symptoms and communicate more effectively with your vet.",
            aud2_t="For Pet Sitters", aud2_d="Accurately log observations while caring for an animal and responsibly inform the owner or vet.",
            aud3_t="For Vets", aud3_d="An additional tool for collecting organized history and preparing for the visit.",
            more_label="Learn more →",
            cta_band_t="Start now and care with confidence.",
            cta_band_s="A better conversation with your vet starts here.",
            cta_band_btn="✦ Start symptom assessment",
            nav_start="Get started",
        )

    css = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
.pan-hr-nav {
  display: flex; align-items: center; justify-content: space-between;
  padding: 4px 0 18px; font-family: 'Inter', system-ui, sans-serif;
}
.pan-hr-logo { font-size: 19px; font-weight: 800; color: #1A1A2E; display: flex; align-items: center; gap: 8px; }
.pan-hr-hero {
  background: linear-gradient(135deg, #ECFDF5 0%, #F0FDF4 60%, white 100%);
  border-radius: 28px; padding: 40px 36px; margin-bottom: 28px;
  font-family: 'Inter', system-ui, sans-serif; position: relative; overflow: hidden;
}
.pan-hr-kicker {
  font-size: 11px; font-weight: 700; letter-spacing: 0.18em; color: #059669;
  margin-bottom: 14px;
}
.pan-hr-h1 {
  font-size: 38px; font-weight: 800; line-height: 1.18; color: #1A1A2E;
  letter-spacing: -1px; margin-bottom: 16px; max-width: 480px;
}
.pan-hr-h1 .accent { color: #059669; }
.pan-hr-sub {
  font-size: 15px; color: #4B5563; max-width: 440px; line-height: 1.6;
  margin-bottom: 22px;
}
.pan-hr-mascots {
  display: flex; justify-content: center; align-items: flex-end; gap: 8px;
  position: relative; padding: 20px 0 8px;
}
.pan-hr-mascots > div {
  background: white; border-radius: 20px; padding: 10px 16px;
  box-shadow: 0 8px 24px rgba(0,0,0,0.08);
}
.pan-hr-cards { display: flex; flex-direction: column; gap: 10px; margin-top: 18px; }
.pan-hr-card {
  background: white; border: 1px solid #ECEEF3; border-radius: 14px;
  padding: 12px 16px; display: flex; align-items: center; gap: 10px;
  font-size: 13px; font-weight: 600; color: #1A1A2E;
  box-shadow: 0 3px 10px rgba(26,26,46,0.04);
}
.pan-hr-card .ic {
  width: 28px; height: 28px; border-radius: 50%; flex-shrink: 0;
  display: flex; align-items: center; justify-content: center; font-size: 14px;
}
.pan-hr-card.c1 .ic { background: #ECFDF5; }
.pan-hr-card.c2 .ic { background: #EEF2FF; }
.pan-hr-card.c3 .ic { background: #ECFDF5; }
.pan-hr-card .check {
  margin-left: auto; width: 18px; height: 18px; border-radius: 50%;
  background: #059669; color: white; font-size: 11px; font-weight: 700;
  display: flex; align-items: center; justify-content: center; flex-shrink: 0;
}
.pan-hr-disclaimer {
  background: white; border: 1px solid #E5E7EB; border-radius: 12px;
  padding: 12px 16px; font-size: 12px; color: #6B7280; line-height: 1.5;
  margin-top: 22px; display: flex; gap: 10px; align-items: flex-start;
}
.pan-hr-steps { margin: 8px 0 30px; font-family: 'Inter', system-ui, sans-serif; }
.pan-hr-steps-title {
  text-align: center; font-size: 22px; font-weight: 800; color: #1A1A2E;
  margin-bottom: 24px;
}
.pan-hr-steps-row {
  display: flex; gap: 14px; overflow-x: auto; padding-bottom: 6px;
}
.pan-hr-step {
  flex: 1 1 160px; min-width: 140px; text-align: center;
}
.pan-hr-step-num {
  width: 30px; height: 30px; border-radius: 50%; background: #059669; color: white;
  display: flex; align-items: center; justify-content: center; font-weight: 700;
  font-size: 13px; margin: 0 auto 10px;
}
.pan-hr-step-icon { font-size: 26px; margin-bottom: 8px; }
.pan-hr-step-title { font-size: 14px; font-weight: 700; color: #1A1A2E; margin-bottom: 4px; }
.pan-hr-step-sub { font-size: 12px; color: #6B7280; line-height: 1.4; }
.pan-hr-aud-title {
  text-align: center; font-size: 22px; font-weight: 800; color: #1A1A2E;
  margin: 8px 0 20px; font-family: 'Inter', system-ui, sans-serif;
}
.pan-hr-aud-row { display: flex; gap: 14px; flex-wrap: wrap; margin-bottom: 24px; }
.pan-hr-aud-card {
  flex: 1 1 240px; background: white; border: 1px solid #ECEEF3; border-radius: 16px;
  padding: 18px 18px 16px; font-family: 'Inter', system-ui, sans-serif;
}
.pan-hr-aud-icon {
  width: 38px; height: 38px; border-radius: 50%; display: flex; align-items: center;
  justify-content: center; font-size: 18px; margin-bottom: 12px;
}
.pan-hr-aud-card.a1 .pan-hr-aud-icon { background: #ECFDF5; }
.pan-hr-aud-card.a2 .pan-hr-aud-icon { background: #EEF2FF; }
.pan-hr-aud-card.a3 .pan-hr-aud-icon { background: #FEF2F2; }
.pan-hr-aud-card h4 { font-size: 16px; font-weight: 800; color: #1A1A2E; margin-bottom: 6px; }
.pan-hr-aud-card p { font-size: 12.5px; color: #6B7280; line-height: 1.55; margin-bottom: 10px; }
.pan-hr-aud-card .more { font-size: 12.5px; font-weight: 700; color: #059669; }
@media (max-width: 640px) {
  .pan-hr-hero { padding: 26px 18px; border-radius: 20px; }
  .pan-hr-h1 { font-size: 28px; }
  .pan-hr-steps-row { gap: 10px; }
  .pan-hr-step { min-width: 120px; }
}
</style>
"""

    body_top = f"""
<div class="pan-hr-hero">
  <div class="pan-hr-kicker">✦ {d['kicker']}</div>
  <div class="pan-hr-h1">{d['h1']} <span class="accent">{d['h1_accent']}</span> {d['h1_end']}</div>
  <div class="pan-hr-sub">{d['sub']}</div>
"""
    st.markdown(css + body_top, unsafe_allow_html=True)

    # CTA buttons (real Streamlit buttons so they can route the app)
    c1, c2 = st.columns([1.4,1])
    with c1:
        cta1 = st.button(d["cta_primary"], type="primary", use_container_width=True, key="hero_cta_primary")
    with c2:
        cta2 = st.button(d["cta_secondary"], use_container_width=True, key="hero_cta_secondary")

    # Mascots + floating feature cards
    st.markdown(f"""
  <div class="pan-hr-mascots">
    <div>{render_mascot("dog", size=110)}</div>
    <div>{render_mascot("cat", size=110)}</div>
  </div>
  <div class="pan-hr-cards">
    <div class="pan-hr-card c1"><span class="ic">🐾</span>{d['card1']}<span class="check">✓</span></div>
    <div class="pan-hr-card c2"><span class="ic">🔎</span>{d['card2']}<span class="check">✓</span></div>
    <div class="pan-hr-card c3"><span class="ic">📄</span>{d['card3']}<span class="check">✓</span></div>
  </div>
  <div class="pan-hr-disclaimer"><span>ℹ️</span><span>{d['disclaimer']}</span></div>
</div>
""", unsafe_allow_html=True)

    # "How it works" steps
    steps_html = "".join(
        f'<div class="pan-hr-step"><div class="pan-hr-step-num">{num}</div>'
        f'<div class="pan-hr-step-icon">{icon}</div>'
        f'<div class="pan-hr-step-title">{title}</div>'
        f'<div class="pan-hr-step-sub">{sub}</div></div>'
        for (num, icon, title, sub) in d["steps"]
    )
    st.markdown(f"""
<div class="pan-hr-steps">
  <div class="pan-hr-steps-title">{d['steps_title']}</div>
  <div class="pan-hr-steps-row">{steps_html}</div>
</div>
""", unsafe_allow_html=True)

    # Audience cards
    st.markdown(f"""
<div class="pan-hr-aud-title">{d['audience_title']}</div>
<div class="pan-hr-aud-row">
  <div class="pan-hr-aud-card a1">
    <div class="pan-hr-aud-icon">🐶</div>
    <h4>{d['aud1_t']}</h4><p>{d['aud1_d']}</p>
    <div class="more">{d['more_label']}</div>
  </div>
  <div class="pan-hr-aud-card a2">
    <div class="pan-hr-aud-icon">🧑‍🤝‍🧑</div>
    <h4>{d['aud2_t']}</h4><p>{d['aud2_d']}</p>
    <div class="more">{d['more_label']}</div>
  </div>
  <div class="pan-hr-aud-card a3">
    <div class="pan-hr-aud-icon">🩺</div>
    <h4>{d['aud3_t']}</h4><p>{d['aud3_d']}</p>
    <div class="more">{d['more_label']}</div>
  </div>
</div>
""", unsafe_allow_html=True)

    # Bottom CTA band
    st.markdown(f"""
<div style="background:linear-gradient(135deg,#ECFDF5,#F0FDF4);border-radius:20px;
            padding:24px 28px;text-align:center;font-family:'Inter',system-ui,sans-serif;
            margin-bottom:20px">
  <div style="font-size:18px;font-weight:800;color:#1A1A2E;margin-bottom:6px">{d['cta_band_t']}</div>
  <div style="font-size:13px;color:#6B7280">{d['cta_band_s']}</div>
</div>
""", unsafe_allow_html=True)
    cta3 = st.button(d["cta_band_btn"], type="primary", use_container_width=True, key="hero_cta_band")

    if cta1 or cta2 or cta3:
        st.session_state["_hero_seen"] = True
        if not auth_enabled() or is_logged_in():
            st.session_state.screen = "intake"
        st.rerun()


def render_login_hero(lang):
    """Compact hero strip for the login screen — logo, one-line value prop,
    and mascots, all above the fold so the login form isn't pushed down by
    the full marketing banner."""
    if lang == "el":
        kicker = "PETAINURSE · AI ΚΤΗΝΙΑΤΡΙΚΟΣ ΝΟΣΗΛΕΥΤΗΣ"
        title  = "Πες τι παρατηρείς."
        accent = "Λάβε εκτίμηση."
        sub    = "Δομημένη σύνοψη με κτηνιατρικές αναφορές, σε λίγα λεπτά — πριν ή αντί για το ιατρείο."
    else:
        kicker = "PETAINURSE · AI VET NURSE"
        title  = "Tell us what's going on."
        accent = "Get an assessment."
        sub    = "A structured summary with veterinary references, in minutes — before or alongside your vet visit."

    st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,800;1,800;1,900&family=Inter:wght@400;500;600;700;800&display=swap');
.pan-hero {{
  background: linear-gradient(180deg, #F0FDF4 0%, #ECFDF5 100%);
  border: 1px solid rgba(5,150,105,0.08);
  border-radius: 24px; padding: 28px 32px; margin: 8px 0 18px;
  text-align: center; font-family: 'Inter', system-ui, sans-serif;
}}
.pan-hero-kicker {{
  display: inline-flex; align-items: center; gap: 8px;
  background: white; border: 1px solid #E5E7EB; border-radius: 999px;
  padding: 6px 16px; font-size: 11px; font-weight: 700; letter-spacing: 0.12em;
  color: #059669; margin-bottom: 14px;
}}
.pan-hero-title {{
  font-family: 'Playfair Display', Georgia, serif;
  font-size: 34px; font-weight: 800; line-height: 1.15;
  color: #1A1A2E; letter-spacing: -1px; margin: 0 0 6px;
}}
.pan-hero-title .accent {{ color: #0EA5E9; font-style: italic; }}
.pan-hero-sub {{
  font-size: 14px; color: #4B5563; max-width: 480px;
  margin: 0 auto; line-height: 1.55;
}}
.pan-hero-mascots {{
  display: flex; justify-content: center; gap: 14px; margin-top: 18px;
}}
.pan-hero-mascots > div {{
  background: white; border-radius: 16px; padding: 6px 12px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.08);
}}
@media (max-width: 640px) {{
  .pan-hero {{ padding: 22px 18px; border-radius: 18px; }}
  .pan-hero-title {{ font-size: 26px; }}
  .pan-hero-sub {{ font-size: 13px; }}
}}
</style>
<div class="pan-hero">
  <div class="pan-hero-kicker">🐾 {kicker}</div>
  <div class="pan-hero-title">{title} <span class="accent">{accent}</span></div>
  <div class="pan-hero-sub">{sub}</div>
  <div class="pan-hero-mascots">
    <div>{render_mascot("dog", size=64)}</div>
    <div>{render_mascot("cat", size=64)}</div>
  </div>
</div>
""", unsafe_allow_html=True)


def render_login_screen():
    """Full-page login shown at the very start when auth is enabled.
    Compact 'hero' layout: lang switch, short value-prop strip with mascots,
    and the login form — all above the fold."""
    lang = st.session_state.lang
    c1, c2 = st.columns([6,1])
    with c2:
        if st.button("🇬🇧 EN" if lang=="el" else "🇬🇷 ΕΛ", key="login_lang"):
            st.session_state.lang = "en" if lang=="el" else "el"; st.rerun()

    # Compact hero — logo, one-line value prop, mascots
    render_login_hero(lang)

    # Login form — front and center
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        render_login_gate()

    _render_disclaimer_strip()


# ── COOKIE MANAGER (once) — persistent login ──────────────────────────────────
if _STX_OK and auth_enabled():
    if "CM" not in st.session_state:
        st.session_state["CM"] = stx.CookieManager(key="pan_cookie_mgr")
    CM = st.session_state["CM"]

    _tok = None
    try:
        _tok = CM.get(COOKIE_NAME)
    except Exception:
        pass
    _email = _read_token(_tok) if _tok else None

    if _email:
        # Valid cookie present → always trust it (covers cases where
        # session_state lost auth_user due to a fresh browser session).
        st.session_state["auth_user"] = _email
        st.session_state["_cookie_check_tries"] = 0
    elif not is_logged_in():
        if _tok is None:
            # CookieManager's underlying component is async: on early runs of
            # a session it may not have delivered the cookie value yet, even
            # if a valid session cookie exists. Give it a few extra render
            # passes before treating the user as logged out, so a mid-session
            # st.rerun() (e.g. "Generate report") never bounces a logged-in
            # user back to the login screen.
            tries = st.session_state.get("_cookie_check_tries", 0)
            if tries < 3:
                st.session_state["_cookie_check_tries"] = tries + 1
                st.rerun()

# ── ROUTER ────────────────────────────────────────────────────────────────────
if not st.session_state.get("_hero_seen") and st.session_state.screen == "home":
    _hl = st.session_state.lang
    c1, c2 = st.columns([6,1])
    with c1:
        st.markdown(
            f'<div style="font-size:19px;font-weight:800;color:#1A1A2E;'
            f'font-family:Inter,system-ui,sans-serif;display:flex;align-items:center;gap:8px;padding-top:6px">'
            f'🐾 PetAiNurse</div>', unsafe_allow_html=True)
    with c2:
        if st.button("🇬🇧 EN" if _hl=="el" else "🇬🇷 ΕΛ", key="hero_lang"):
            st.session_state.lang = "en" if _hl=="el" else "el"; st.rerun()
    render_hero_screen()
    st.stop()

if auth_enabled() and not is_logged_in():
    render_login_screen()
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
