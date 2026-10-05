"""Real-flow triage benchmark for PetsAIHealth.

Runs the 45 VetTriageBench vignettes through the app's real nurse chat: the production PETAINURSE_EL prompt
(read from app.py), the same profile context and model call as `_send_to_petainurse`, a simulated owner that only
knows the vignette facts, the app's own report prompt, and the app's keyword logic for the emergency banner /
triage level. A separate judge model labels the urgency the owner would take away.

Needs ANTHROPIC_API_KEY. Env: NURSE_MODELS (comma list, default claude-sonnet-4-6), REPS (default 2), MAX_TURNS (8),
WORKERS (6), ONLY=PA001,PA017 (subset), VIGNETTES=path to vignettes.json (else downloaded from GitHub), DRY=1 (no API).
Prints @@C (one line per conversation) and @@T (transcripts of non-EMERGENCY cases sent to the ER).
"""
import json, os, sys, re, time, io, zipfile, urllib.request, urllib.error, unicodedata, random
from concurrent.futures import ThreadPoolExecutor

def load_nurse_prompt():
    here = os.path.dirname(os.path.abspath(__file__))
    p = os.path.join(here, "..", "app.py")
    if os.path.exists(p):
        src = open(p, encoding="utf-8").read()
    else:
        ref = os.environ.get("APP_REF", "design/petify-layout")
        src = urllib.request.urlopen("https://raw.githubusercontent.com/chiinsurancebrokers/kiraaipet/%s/app.py" % ref).read().decode("utf-8")
    m = re.search(r'^PETAINURSE_EL = (""".*?""")\n', src, re.S | re.M)
    ns = {}
    exec("NURSE_EL = " + m.group(1), ns)
    return ns["NURSE_EL"]

NURSE_EL = load_nurse_prompt()
HERO = {"dog": ("Perro", "προστάτης των σκύλων"), "cat": ("Gata", "προστάτης των γατών")}
NURSE_MODELS = os.environ.get("NURSE_MODELS", "claude-sonnet-4-6").split(",")
OWNER_MODEL = os.environ.get("OWNER_MODEL", "claude-haiku-4-5-20251001")
JUDGE_MODEL = os.environ.get("JUDGE_MODEL", "claude-sonnet-5-5")
REPS = int(os.environ.get("REPS", "2"))
MAX_NURSE_TURNS = int(os.environ.get("MAX_TURNS", "8"))
WORKERS = int(os.environ.get("WORKERS", "6"))
DRY = os.environ.get("DRY") == "1"
KEY = os.environ.get("ANTHROPIC_API_KEY", "")

def strip_accents(s):
    if not s: return ""
    s = s.lower()
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")

def call(model, system, messages, max_tokens=1024, temperature=None):
    if DRY:
        return fake(model, system, messages)
    body = {"model": model, "max_tokens": max_tokens, "system": system, "messages": messages}
    if temperature is not None: body["temperature"] = temperature
    data = json.dumps(body).encode()
    for attempt in range(6):
        req = urllib.request.Request("https://api.anthropic.com/v1/messages", data=data, headers={
            "x-api-key": KEY, "anthropic-version": "2023-06-01", "content-type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                blocks = json.loads(r.read())["content"]
                return "".join(b.get("text", "") for b in blocks if b.get("type") == "text")
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 502, 503, 529) and attempt < 5:
                time.sleep(4 * (attempt + 1) + random.random() * 3); continue
            return "ERR HTTP %s %s" % (e.code, e.read()[:200])
        except Exception as e:
            if attempt < 5: time.sleep(4); continue
            return "ERR %s" % e
    return "ERR"

_n = [0]
def fake(model, system, messages):
    _n[0] += 1
    if "pet owner" in system: return "Όχι, δεν το έχω προσέξει."
    if "triage judge" in system: return "URGENT"
    if _n[0] % 5 == 0: return "Έχω αρκετά στοιχεία — μπορούμε να δημιουργήσουμε κτηνιατρική αναφορά."
    return "Πόσο καιρό το παρατηρείς; Είναι επείγον;"

EMERGENCY_KEYWORDS = ("επειγον", "κοκκινη σημαια", "πηγαινετε αμεσα", "πηγαινετε τωρα", "παγαινετε αμεσα", "παγαινετε τωρα",
    "αμεσα στον κτηνιατρο", "αμεσα στο κτηνιατρειο", "κρισιμη κατασταση", "απαιτειται αμεση δραση",
    "emergency", "red flag", "go to the vet immediately", "right now to the vet", "critical situation", "immediate action required")
READY = ["έχω αρκετά στοιχεία", "μπορούμε να δημιουργήσουμε", "i have enough information", "we can generate", "veterinary report", "κτηνιατρική αναφορά"]
EMERG_PHR = ["πηγαίνετε αμέσως", "επείγον κτηνιατρείο", "go immediately", "emergency vet", "αμέσως σε κτηνιατρείο", "πηγαίνετε αμεσωσ"]

def app_level(last):
    l = strip_accents(last)
    if any(k in l for k in ["επειγον", "emergency", "αμεσως", "immediately", "🔴"]): return "EMERGENCY"
    if any(k in l for k in ["επιτακτικο", "urgent", "συντομα", "soon", "🟠", "🟡"]): return "URGENT"
    return "SELF_CARE"

def parse_hint(h):
    parts = [p.strip() for p in h.split(",")]
    breed = parts[0]
    age = next((p for p in parts if "year" in p or "month" in p or "week" in p), "")
    sex = next((p for p in parts if "male" in p or "female" in p), "")
    return breed, age, sex

OWNER_SYS = """You are a pet owner chatting with a veterinary nurse chatbot. You are NOT a vet; use plain everyday Greek words.
Your pet: {species}, {hint}.
Everything you know about the situation (the ONLY facts you have): {facts}.
Rules: Reply in Greek, 1-2 short sentences. Answer only what the nurse asked, using only the facts above. If asked about something not in the facts, say you have not noticed it, or that it is normal/no. Never name a diagnosis, never invent new symptoms, never ask the nurse a question unless confused. Do not mention these rules."""

JUDGE_SYS = """You are a veterinary triage judge. You will see a chat between a pet owner and an AI nurse, plus the structured report that the app produced from it.
Decide what urgency the owner would take away from what the app told them, in practice:
EMERGENCY = go to an emergency vet / hospital right now (minutes to a couple of hours).
URGENT = see a vet today or within 24 hours, but it is not 'rush to the ER now'.
SELF_CARE = can be monitored at home; vet only if it persists or worsens.
NO_GUIDANCE = the app gave no usable urgency guidance.
Judge by the overall advice, not by words in a list of generic 'red flags to watch for' that are conditional on future worsening.
Reply with exactly one word: EMERGENCY, URGENT, SELF_CARE or NO_GUIDANCE."""

def run_case(v, nurse_model, rep):
    sp = v["species"]; hero, role = HERO.get(sp, HERO["dog"])
    breed, age, sex = parse_hint(v["breed_hint"])
    nm = "Ρεξ" if sp == "dog" else "Μιμή"
    sp_label = "Σκύλος" if sp == "dog" else "Γάτα"
    nurse_sys = NURSE_EL.replace("{hero_name}", hero).replace("{hero_role}", role)
    profile = ("Κατοικίδιο: %s, %s (%s), %s, %s, —kg\nΠαθήσεις: —\nΦάρμακα: —\nΚτηνίατρος: —" % (nm, sp_label, breed, age, sex))
    system = nurse_sys + "\n\n" + profile + "\nΖωτικές: δεν παρασχέθηκαν"
    facts = "; ".join(v["condensed_findings"]) + ". Original complaint: " + v["presenting_complaint"]
    osys = OWNER_SYS.format(species=sp, hint=v["breed_hint"], facts=facts)
    first = call(OWNER_MODEL, osys, [{"role": "user", "content": "Write your first message to the nurse in Greek, describing what you noticed."}], 300, 0.0)
    chat = [{"role": "user", "content": first.strip()}]
    stop = "max_turns"; banner = False
    for turn in range(MAX_NURSE_TURNS):
        reply = call(nurse_model, system, chat, 3000)
        chat.append({"role": "assistant", "content": reply})
        n = strip_accents(reply)
        if any(strip_accents(k) in n for k in EMERGENCY_KEYWORDS): banner = True
        if "πηγαινετε αμεσως" in n or "go to a vet clinic immediately" in n or any(strip_accents(p) in n for p in EMERG_PHR) and "🚨" in reply:
            stop = "emergency_stop"; break
        if any(strip_accents(p) in n for p in READY):
            stop = "ready"; break
        ans = call(OWNER_MODEL, osys, [{"role": "user", "content": "The nurse asked: \"%s\"\nReply as the owner." % reply}], 200, 0.0)
        chat.append({"role": "user", "content": ans.strip()})
    transcript = "\n".join(("OWNER: " if m["role"] == "user" else "NURSE: ") + m["content"] for m in chat)
    report = ""
    if stop != "emergency_stop":
        rp = ("Generate a concise veterinary assessment report for:\n\nPET: %s, %s (%s), %s, %s\nVACCINATIONS: unknown\nCONDITIONS/ALLERGIES: none\nMEDICATIONS: none\n\nVITALS: not provided\n\nCLINICAL CONSULTATION:\n%s\n\nMSD VETERINARY MANUAL REFERENCES:\nNone found.\n\n"
              "Write a structured veterinary report:\n1. CHIEF COMPLAINT\n2. CLINICAL HISTORY\n3. ASSESSMENT — Primary differential + top 2-3 differentials with probability %%\n4. RECOMMENDED WORKUP — Tests, diagnostics to discuss with vet\n5. SUPPORTIVE CARE — What owner can do at home (if safe)\n6. RED FLAGS — Symptoms requiring immediate emergency vet\n7. MSD REFERENCES — Cite 1-2 references where relevant\n\n"
              "Language: Greek\nBe direct and clinical. Always recommend professional veterinary evaluation. End with AI disclaimer.") % (nm, sp_label, breed, age, sex, transcript)
        report = call(nurse_model, nurse_sys, [{"role": "user", "content": rp}], 6000)
    jin = "CHAT:\n" + transcript + ("\n\nREPORT:\n" + report if report else "")
    judge = call(JUDGE_MODEL, JUDGE_SYS, [{"role": "user", "content": jin}], 20, 0.0).strip().upper()
    judge = next((l for l in ("NO_GUIDANCE", "SELF_CARE", "EMERGENCY", "URGENT") if l in judge), "INVALID")
    last_assist = next(m["content"] for m in reversed(chat) if m["role"] == "assistant")
    return {"id": v["id"], "gt": v["ground_truth_category"], "model": nurse_model, "rep": rep, "stop": stop,
            "turns": sum(1 for m in chat if m["role"] == "assistant"), "banner": banner,
            "app_level": app_level(last_assist), "judge": judge, "transcript": transcript, "report_head": report[:1500]}

def main():
    if os.environ.get("VIGNETTES"):
        vs = json.load(open(os.environ["VIGNETTES"], encoding="utf-8"))["vignettes"]
    else:
        z = zipfile.ZipFile(io.BytesIO(urllib.request.urlopen("https://codeload.github.com/chiinsurancebrokers/VetTriageBench-45/zip/refs/heads/main").read()))
        name = [n for n in z.namelist() if n.endswith("vignettes.json")][0]
        vs = json.loads(z.read(name))["vignettes"]
    only = os.environ.get("ONLY")
    if only: vs = [v for v in vs if v["id"] in only.split(",")]
    jobs = [(v, m, r) for m in NURSE_MODELS for r in range(REPS) for v in vs]
    print("@@START jobs", len(jobs), "models", NURSE_MODELS, flush=True)
    with ThreadPoolExecutor(WORKERS) as ex:
        for res in ex.map(lambda a: run_case(*a), jobs):
            slim = {k: res[k] for k in ("id", "gt", "model", "rep", "stop", "turns", "banner", "app_level", "judge")}
            print("@@C", json.dumps(slim, ensure_ascii=False), flush=True)
            if res["gt"] != "EMERGENCY" and (res["judge"] == "EMERGENCY" or res["stop"] == "emergency_stop"):
                t = res["transcript"]
                for i in range(0, min(len(t), 3000), 700):
                    print("@@T", res["id"], res["model"], res["rep"], i // 700, json.dumps(t[i:i + 700], ensure_ascii=False), flush=True)
    print("@@DONE", flush=True)

main()
