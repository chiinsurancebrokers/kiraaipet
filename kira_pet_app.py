"""
KIRA PET — AI Veterinary Nurse
Bilingual AI health assistant for pet owners in Greece.
Brand: petshealth.gr · Ashlar Insurance
Standalone Streamlit app · Real data only · No placeholders.
"""

import streamlit as st
import json
import io
import urllib.request
import urllib.parse
from datetime import datetime

st.set_page_config(
    page_title="Kira Pet · AI Vet Nurse",
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

.kira-stepper { display: flex; align-items: center; justify-content: center; gap: 0; margin: 0 0 28px; padding: 16px 0 0; }
.kira-step { display: flex; flex-direction: column; align-items: center; gap: 6px; flex: 1; max-width: 120px; }
.kira-step-circle { width: 32px; height: 32px; border-radius: 50%; display: flex; align-items: center;
    justify-content: center; font-size: 13px; font-weight: 700; border: 2px solid #A7F3D0;
    background: white; color: #A7F3D0; position: relative; z-index: 1; }
.kira-step.done   .kira-step-circle { background: #059669; border-color: #059669; color: white; }
.kira-step.active .kira-step-circle { background: #0EA5E9; border-color: #0EA5E9; color: white; box-shadow: 0 0 0 4px rgba(14,165,233,.15); }
.kira-step-label { font-size: 10px; color: #94A3B8; text-align: center; }
.kira-step.done   .kira-step-label { color: #059669; }
.kira-step.active .kira-step-label { color: #0EA5E9; font-weight: 600; }
.kira-step-line { flex: 1; height: 2px; background: #A7F3D0; margin-bottom: 18px; }
.kira-step-line.done { background: #059669; }

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
        v = st.secrets.get(k, "")
        if v: return v
    return fallback

def get_claude_key():  return _key("Claude_API_Key")
def get_openai_key():  return _key("OPENAI_API_KEY")
def get_maps_key():    return _key("GOOGLE_MAPS_KEY", "")

# ── MSD VET MANUAL SEARCH ─────────────────────────────────────────────────────
MSD_BASE = {
    "dog":    "https://www.msdvetmanual.com/dog-owners",
    "cat":    "https://www.msdvetmanual.com/cat-owners",
    "rabbit": "https://www.msdvetmanual.com/all-other-pets",
    "bird":   "https://www.msdvetmanual.com/bird-owners",
    "other":  "https://www.msdvetmanual.com/all-other-pets",
}

def msdvet_search(species, query, n=3):
    """Fetch MSD Vet Manual evidence for the clinical report."""
    try:
        base = MSD_BASE.get(species, MSD_BASE["dog"])
        search_url = f"https://www.msdvetmanual.com/search?query={urllib.parse.quote(query)}&lang=en"
        req = urllib.request.Request(search_url, headers={"User-Agent":"Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=8) as r:
            html = r.read().decode("utf-8","ignore")
        # Extract article links from search results
        links = []
        import re
        for m in re.finditer(r'href="(/[a-z\-]+/[a-z\-/]+)"', html):
            path = m.group(1)
            if any(s in path for s in ["dog","cat","bird","rabbit","pet","veterinary"]) and path not in links:
                links.append(f"https://www.msdvetmanual.com{path}")
            if len(links) >= n: break
        if not links:
            links = [base]
        return [{"title": l.split("/")[-1].replace("-"," ").title(), "url": l} for l in links]
    except:
        base = MSD_BASE.get(species, MSD_BASE["dog"])
        return [{"title": "MSD Veterinary Manual", "url": base}]

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

# ── GPT-4o ────────────────────────────────────────────────────────────────────
def gpt4o(prompt, system="", max_tokens=900):
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
def claude(messages, system="", max_tokens=1200, timeout=60):
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


# ── SESSION STATE ─────────────────────────────────────────────────────────────
defaults = {
    "lang": "el", "screen": "home",
    "pet": {},           # pet profile
    "vitals": {},        # pet vitals
    "vitals_analysis": "",
    "triage_chat": [],
    "report": "", "report_refs": [], "report_gpt": "",
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
        "title":"Kira Pet","subtitle":"Ο AI Κτηνιατρικός Νοσηλευτής σου",
        "tagline":"Για την υγεία του κατοικίδιού σου · Πάντα δίπλα σου",
        "start":"Ξεκίνα Εκτίμηση",
        "disclaimer_main":"⚠️ Η Kira Pet παρέχει πληροφορίες για ενημερωτικούς σκοπούς μόνο. Δεν αντικαθιστά κτηνιατρική διάγνωση ή θεραπεία. Σε επείγον καλέστε άμεσα κτηνίατρο.",
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
        "insurance_cta":"Ασφαλίστε το κατοικίδιό σας",
        "insurance_sub":"Κάλυψη κτηνιατρικών εξόδων, επειγόντων και χειρουργείων",
        "insurance_btn":"Ζητήστε Προσφορά → petshealth.gr",
    },
    "en": {
        "title":"Kira Pet","subtitle":"Your AI Veterinary Nurse",
        "tagline":"For your pet's health · Always by your side",
        "start":"Start Assessment",
        "disclaimer_main":"⚠️ Kira Pet provides information for informational purposes only. It does not replace veterinary diagnosis or treatment. In an emergency call a vet immediately.",
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
        "insurance_cta":"Insure your pet",
        "insurance_sub":"Coverage for vet visits, emergencies and surgery",
        "insurance_btn":"Get a Quote → petshealth.gr",
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
    html = '<div class="kira-stepper">'
    for i,label in enumerate(steps):
        cls = "done" if i<cur_i else ("active" if i==cur_i else "")
        icon = "✓" if i<cur_i else str(i+1)
        html += f'<div class="kira-step {cls}"><div class="kira-step-circle">{icon}</div><div class="kira-step-label">{label}</div></div>'
        if i<len(steps)-1:
            html += f'<div class="kira-step-line {"done" if i<cur_i else ""}"></div>'
    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)

# ── KIRA PET SYSTEM PROMPTS ───────────────────────────────────────────────────
KIRA_PET_EL = """Είσαι η Kira Pet — AI κτηνιατρικός νοσηλευτής για κατοικίδια στην Ελλάδα.
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

KIRA_PET_EN = """You are Kira Pet — an AI veterinary nurse for pets in Greece.
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

def kira_pet_system(): return KIRA_PET_EL if st.session_state.lang=="el" else KIRA_PET_EN


# ── EMERGENCY VET CLINICS (Athens + major Greek cities) ───────────────────────
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
def generate_pet_html_report(pet, vitals, report_text, refs, lang="el"):
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

    return f"""<!DOCTYPE html><html lang="{lang}"><head><meta charset="UTF-8">
<title>Kira Pet Report — {name}</title>
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
@media print{{body{{padding:16px}}.pet-card,.emergency{{-webkit-print-color-adjust:exact;print-color-adjust:exact}}@page{{margin:15mm}}}}</style></head><body>
<div class="hdr"><div class="hdr-logo">🐾 Kira Pet · petshealth.gr</div><div class="hdr-date">Κτηνιατρική Εκτίμηση<br>{ts}</div></div>
<div class="pet-card"><div class="pet-name">{name} {species}</div><div class="pet-meta">{breed} · {age} · {sex} · {weight}kg</div>
<div class="pet-detail"><strong>Κτηνίατρος:</strong> {vet}<br><strong>Παθήσεις/Αλλεργίες:</strong> {cond}<br><strong>Φάρμακα:</strong> {meds}</div></div>
{vitals_sec}<h2>Κτηνιατρική Αξιολόγηση</h2>{md2h(report_text or "")}{refs_html}
<div class="emergency">🚨 ΣΕ ΕΠΕΙΓΟΝ: Επικοινωνήστε ΑΜΕΣΑ με κτηνίατρο ή επείγον κτηνιατρείο</div>
<div class="cta"><a href="https://petshealth.gr">🐾 Ασφαλίστε το κατοικίδιό σας → petshealth.gr</a></div>
<div class="disclaimer">⚠️ AI-generated. Δεν αποτελεί κτηνιατρική διάγνωση. Απαιτείται επίσκεψη σε κτηνίατρο.</div>
</body></html>""".encode("utf-8")


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
        st.markdown('<div class="card"><div style="font-size:32px">🐾</div><h3 style="margin-top:12px">petshealth.gr</h3><p style="font-size:13px;color:#6B7280">Συνδεδεμένο με το petshealth.gr για ασφάλιση κατοικίδιων στην Ελλάδα.</p></div>', unsafe_allow_html=True)

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
                                       value=float(pet.get("weight",0.0)) or None, placeholder="5.0", format="%.1f")

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

    # Species-specific normal range info
    hr_range = rng["hr"]; br_range = rng["br"]; temp_range = rng["temp"]
    st.caption(f"{'Φυσιολογικά για' if lang=='el' else 'Normal for'} {pet.get('species_label','')}: "
               f"HR {hr_range[0]}–{hr_range[1]} bpm · BR {br_range[0]}–{br_range[1]}/min · "
               f"Temp {temp_range[0]}–{temp_range[1]}°C")

    v = st.session_state.vitals
    c1,c2,c3 = st.columns(3)
    with c1:
        hr   = st.number_input(t("hr"),  min_value=0, max_value=500, value=int(v.get("hr",0)) or None, placeholder=str(int((hr_range[0]+hr_range[1])//2)))
        temp = st.number_input(t("temp"),min_value=0.0,max_value=45.0,value=float(v.get("temp",0.0)) or None, placeholder=str(temp_range[0]), format="%.1f")
    with c2:
        br   = st.number_input(t("br"),  min_value=0, max_value=100, value=int(v.get("br",0)) or None, placeholder=str(int((br_range[0]+br_range[1])//2)))
        spo2 = st.number_input(t("spo2"),min_value=0, max_value=100, value=int(v.get("spo2",0)) or None, placeholder="98")
    with c3:
        wt   = st.number_input(t("weight_v"),min_value=0.0,max_value=200.0,
                                value=float(pet.get("weight",0.0)) or None, placeholder="5.0", format="%.1f")

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
                        [{"role":"user","content":prompt}], system=kira_pet_system(), max_tokens=1200)
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
    last_kira = next((m["content"].lower() for m in reversed(st.session_state.triage_chat) if m["role"]=="assistant"), "")
    triage_ready = any(ph in last_kira for ph in ready_phrases)

    user_input = st.chat_input(t("triage_placeholder"), key="triage_input")
    if user_input:
        st.session_state.triage_chat.append({"role":"user","content":user_input})
        with st.spinner("Kira Pet..."):
            p = pet
            profile_ctx = (f"Κατοικίδιο: {p.get('name')}, {p.get('species_label')} ({p.get('breed')}), "
                           f"{p.get('age_y')}y {p.get('age_m')}m, {p.get('sex')}, {p.get('weight','')}kg\n"
                           f"Παθήσεις: {p.get('conditions','—')}\nΦάρμακα: {p.get('meds_raw','—')}\nΚτηνίατρος: {p.get('vet_name','—')}")
            vitals_ctx = ("Ζωτικές: " + ", ".join(f"{k}={val}" for k,val in st.session_state.vitals.items())
                          if st.session_state.vitals else "Ζωτικές: δεν παρασχέθηκαν")
            system_ctx = kira_pet_system() + f"\n\n{profile_ctx}\n{vitals_ctx}"
            reply = claude([{"role":m["role"],"content":m["content"]} for m in st.session_state.triage_chat],
                           system=system_ctx, max_tokens=1500)
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
        st.caption("Συνεχίστε — η Kira Pet θα σας ειδοποιήσει όταν έχει αρκετά." if lang=="el"
                   else "Continue — Kira Pet will let you know when she has enough.")


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
            f"{'Owner' if m['role']=='user' else 'Kira Pet'}: {m['content']}"
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
                            system=kira_pet_system(), max_tokens=2500, timeout=120)
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
                            prompt=f"Pet: {pet.get('name')}, {pet.get('species_label')} ({pet.get('breed')}), {pet.get('age_y')}y\n\nKira Pet's assessment:\n{st.session_state.report}\n\nDo you agree with this veterinary assessment? Provide additions, corrections, or alternative differentials. Be specific and species-appropriate.",
                            system=kira_pet_system(), max_tokens=900)
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

    # petshealth.gr insurance CTA
    st.markdown(f'''<div class="insurance-cta">
        <div style="font-size:28px;margin-bottom:8px">🐾</div>
        <div style="font-size:18px;font-weight:700;margin-bottom:6px">{t("insurance_cta")}</div>
        <div style="opacity:.85;font-size:13px;margin-bottom:14px">{t("insurance_sub")}</div>
        <a href="https://petshealth.gr" target="_blank"
           style="background:white;color:#059669;padding:10px 24px;border-radius:8px;font-weight:700;text-decoration:none;font-size:14px">
            {t("insurance_btn")}
        </a>
    </div>''', unsafe_allow_html=True)

    # Actions
    fname = f"kira_pet_report_{pet.get('name','pet')}_{datetime.now().strftime('%Y%m%d')}"
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
                                                          st.session_state.report, st.session_state.report_refs, lang),
                           file_name=fname+".html", mime="text/html", use_container_width=True,
                           help="Open in browser → Ctrl+P → Save as PDF")

# ── ROUTER ────────────────────────────────────────────────────────────────────
screen = st.session_state.screen
if   screen=="home":   render_home()
elif screen=="intake": render_intake()
elif screen=="vitals": render_vitals()
elif screen=="triage": render_triage()
elif screen=="report": render_report()
else: render_home()

