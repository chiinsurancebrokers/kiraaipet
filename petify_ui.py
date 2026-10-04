"""
petify_ui.py — Petify-inspired visual layer for PetAiNurse (Kira AI Pet).

Original design in the same spirit as the Petify product page: a royal-blue brand
tile, lavender flow panels, an orange accent, a phone-scan visual and a small
"console" card. No third-party artwork, logos or copy are used.

Pure string builders — no Streamlit import — so they are easy to test.
"""
from __future__ import annotations

import html as _h

BLUE = "#1237C9"
BLUE2 = "#2F55F0"
ORANGE = "#FF6B2C"
INK = "#0B1B4B"
MUTED = "#5B6794"
LINE = "#D9DEF5"
LAV = "#E7EAFB"
LAV2 = "#C9D0F5"
BG = "#F4F6FE"

# ── theme overrides (injected AFTER the legacy CSS so it wins) ────────────────
THEME_CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Sora:wght@600;700;800&family=Inter:wght@400;500;600;700;800&display=swap');
:root {{
  --pn-blue:{BLUE}; --pn-blue2:{BLUE2}; --pn-orange:{ORANGE}; --pn-ink:{INK}; --pn-muted:{MUTED};
  --pn-line:{LINE}; --pn-lav:{LAV}; --pn-lav2:{LAV2}; --pn-bg:{BG}; --pn-display:'Sora','Inter',system-ui,sans-serif;
  --surface-0:{BG}; --surface-1:#F7F8FF; --border:{LINE};
  --text-primary:{INK}; --text-secondary:{MUTED};
}}
* {{ font-family:'Inter', system-ui, sans-serif; }}
[data-testid="stAppViewContainer"] {{ background:{BG} !important; overflow-x:hidden !important; }}
[data-testid="stHeader"] {{ background:transparent !important; }}
.main .block-container, [data-testid="stMainBlockContainer"] {{ max-width:1040px; padding-top:1.6rem !important; }}
h1,h2,h3,h4, [data-testid="stMarkdownContainer"] h1, [data-testid="stMarkdownContainer"] h2,
[data-testid="stMarkdownContainer"] h3, [data-testid="stMarkdownContainer"] h4 {{
  font-family:var(--pn-display) !important; letter-spacing:-.02em; color:{INK};
}}
@media (max-width:768px) {{
  input, textarea, select, [data-baseweb="select"] div, .stTextInput input, .stNumberInput input, .stTextArea textarea {{ font-size:16px !important; }}
}}

/* Buttons — blue pill primary, quiet white secondary */
.stButton button[kind="primary"], .stFormSubmitButton button[kind="primary"], [data-testid="stBaseButton-primaryFormSubmit"],
.stDownloadButton button[kind="primary"], .stLinkButton a[kind="primary"] {{
  background:{BLUE} !important; color:#fff !important; border:none !important; border-radius:999px !important;
  font-weight:700 !important; min-height:46px !important; box-shadow:0 12px 28px -12px rgba(18,55,201,.65) !important;
  transition:transform .2s ease, box-shadow .2s ease, background .2s ease !important;
}}
.stButton button[kind="primary"] p, .stFormSubmitButton button p, .stDownloadButton button[kind="primary"] p {{ color:#fff !important; font-weight:700 !important; }}
.stButton button[kind="primary"]:hover {{ background:{BLUE2} !important; transform:translateY(-2px); }}
.stButton button[kind="primary"]:disabled {{ background:#DDE2F5 !important; box-shadow:none !important; transform:none; }}
.stButton button[kind="primary"]:disabled p {{ color:#98A2C8 !important; }}
.stButton button[kind="secondary"], .stDownloadButton button[kind="secondary"], .stFormSubmitButton button[kind="secondary"] {{
  background:#fff !important; color:{INK} !important; border:1px solid {LINE} !important; border-radius:999px !important; min-height:44px !important;
}}
.stButton button[kind="secondary"]:hover {{ border-color:{BLUE} !important; color:{BLUE} !important; background:{LAV} !important; }}

/* Inputs */
.stTextInput input, .stNumberInput input, .stTextArea textarea {{ border-radius:12px !important; background:#fff !important; border:1px solid {LINE} !important; }}
div[data-baseweb="input"], div[data-baseweb="textarea"], div[data-baseweb="select"] {{ border-radius:12px !important; }}
.stTextInput input:focus, .stNumberInput input:focus, .stTextArea textarea:focus {{ border-color:{BLUE} !important; box-shadow:0 0 0 3px rgba(18,55,201,.12) !important; }}

/* Cards and expanders */
[data-testid="stVerticalBlockBorderWrapper"] {{ border-color:{LINE} !important; border-radius:22px !important; background:#fff; }}
[data-testid="stExpander"] {{ border:1px solid {LINE} !important; border-radius:18px !important; background:#fff; box-shadow:none !important; }}
.card {{ border:1px solid {LINE}; border-radius:20px; background:#fff; padding:18px 20px; }}
.card h3 {{ font-family:var(--pn-display); font-size:15px; font-weight:700; color:{INK}; }}

/* Tabs */
[data-baseweb="tab-list"] {{ gap:6px; }}
[data-baseweb="tab"] {{ border-radius:999px !important; padding:6px 16px !important; }}
[aria-selected="true"][data-baseweb="tab"] {{ background:{LAV} !important; color:{BLUE} !important; }}
[data-baseweb="tab-highlight"] {{ background:{BLUE} !important; }}

/* Chat */
[data-testid="stChatMessage"] {{ border-radius:18px; border:1px solid {LINE}; background:#fff; }}
[data-testid="stChatInput"] > div {{ border-radius:999px !important; border:1px solid {LINE} !important; }}
[data-testid="stChatInputSubmitButton"] {{ background:{BLUE} !important; color:#fff !important; border-radius:999px !important; }}

/* Legacy teal blocks → blue */
.pet-hero {{ background:radial-gradient(120% 90% at 100% 0%, rgba(47,85,240,.55) 0%, rgba(47,85,240,0) 60%), {BLUE}; border-radius:24px; }}
.pet-hero h1 {{ font-family:var(--pn-display); font-weight:700; }}
.wellness-wrap {{ background:{BLUE}; border-radius:20px; }}
.emergency-vet {{ background:{BLUE}; }}
.insurance-cta {{ background:{LAV}; border-color:{LAV2}; border-radius:20px; }}
.pan-step-card {{ border-left-color:{BLUE}; border-radius:0 14px 14px 0; }}
.pan-step-card .step-num {{ color:{BLUE}; }}
.pan-step-circle {{ border-color:{LAV2}; color:{LAV2}; }}
.pan-step.done .pan-step-circle {{ background:{BLUE2}; border-color:{BLUE2}; }}
.pan-step.active .pan-step-circle {{ background:{BLUE}; border-color:{BLUE}; box-shadow:0 0 0 4px rgba(18,55,201,.14); }}
.pan-step.done .pan-step-label {{ color:{BLUE2}; }}
.pan-step.active .pan-step-label {{ color:{BLUE}; font-weight:700; }}
.pan-step-line {{ background:{LAV2}; }} .pan-step-line.done {{ background:{BLUE2}; }}
.pan-dph-logo {{ background:{LAV} !important; }}
.pan-doc-page-head {{ border-color:{LINE} !important; border-radius:20px !important; }}

/* Feature cards side by side: equal heights */
div[data-testid="stHorizontalBlock"]:has([class*="pn-feat-"]) {{ align-items:stretch !important; }}
div[data-testid="stHorizontalBlock"]:has([class*="pn-feat-"]) > div[data-testid="stColumn"] > div[data-testid="stVerticalBlock"] {{ height:100%; }}
div[data-testid="stHorizontalBlock"]:has([class*="pn-feat-"]) > div[data-testid="stColumn"] > div[data-testid="stVerticalBlock"] > div[data-testid="stVerticalBlockBorderWrapper"] {{ flex:1 1 auto; }}
div[data-testid="stHorizontalBlock"]:has([class*="pn-feat-"]) [data-testid="stVerticalBlockBorderWrapper"] > div[data-testid="stVerticalBlock"] {{ height:100%; justify-content:space-between; }}

/* Shared Petify building blocks */
.pn-eyebrow {{ display:inline-flex; align-items:center; width:fit-content; padding:6px 12px; border-radius:999px;
  font:700 11px/1 'Inter',sans-serif; letter-spacing:.12em; text-transform:uppercase; color:{BLUE}; background:{LAV}; border:1px solid {LAV2}; }}
.pn-eyebrow.dark {{ color:#fff; background:rgba(255,255,255,.14); border-color:rgba(255,255,255,.28); }}
.pn-eyebrow.orange {{ color:#fff; background:{ORANGE}; border-color:{ORANGE}; }}
.pn-h2 {{ font-family:var(--pn-display); font-weight:700; font-size:30px; line-height:1.1; letter-spacing:-.03em; color:{INK}; margin:12px 0 8px; }}
.pn-sub {{ font-size:15px; line-height:1.6; color:{MUTED}; max-width:620px; }}
.pn-sec {{ font:700 11.5px/1 'Inter',sans-serif; letter-spacing:.12em; text-transform:uppercase; color:{BLUE}; margin:22px 4px 10px; }}
.pn-chip {{ display:inline-flex; align-items:center; gap:6px; padding:5px 11px; border-radius:999px; background:#fff; border:1px solid {LINE}; font-size:12px; font-weight:600; color:{INK}; }}
.pn-chip.ok {{ color:#047857; border-color:#A7F3D0; background:#ECFDF5; }}
.pn-chip.blue {{ color:{BLUE}; border-color:{LAV2}; background:{LAV}; }}
@media (max-width:640px) {{ .pn-h2 {{ font-size:24px; }} }}
</style>
"""


def feature_banner_css(marker: str, dark: bool) -> str:
    """CSS that turns the bordered container holding `.marker` into a Petify card."""
    sel = f'div[data-testid="stVerticalBlock"]:has(> div[data-testid="stElementContainer"] .{marker})'
    if dark:
        bg = (f"radial-gradient(120% 90% at 100% 0%, rgba(47,85,240,.65) 0%, rgba(47,85,240,0) 60%), {BLUE}")
        return (f"<style>{sel}{{background:{bg} !important;border:none !important;border-radius:24px !important;"
                f"box-shadow:0 26px 50px -30px rgba(18,55,201,.7);height:100%;}}"
                f"{sel} button{{background:{ORANGE} !important;color:#fff !important;border:none !important;"
                f"border-radius:999px !important;font-weight:700 !important;min-height:46px !important;box-shadow:none !important;}}"
                f"{sel} button p{{color:#fff !important;font-weight:700 !important;}}</style>")
    return (f"<style>{sel}{{background:{LAV} !important;border:1px solid {LAV2} !important;border-radius:24px !important;"
            f"box-shadow:none;height:100%;}}</style>")


# ── hero ─────────────────────────────────────────────────────────────────────
HERO_CSS = f"""
<style>
.pn-hero-head {{ display:flex; flex-wrap:wrap; gap:14px; align-items:stretch; margin:2px 0 14px; }}
.pn-brand-tile {{ flex:1 1 360px; background:radial-gradient(120% 100% at 100% 0%, rgba(47,85,240,.7) 0%, rgba(47,85,240,0) 60%), {BLUE};
  border-radius:26px; padding:30px 30px 28px; color:#fff; display:flex; flex-direction:column; gap:14px; box-shadow:0 30px 60px -34px rgba(18,55,201,.8); }}
.pn-logo-row {{ display:flex; align-items:center; gap:12px; }}
.pn-logo-mark {{ width:52px; height:52px; border-radius:17px; background:{ORANGE}; display:flex; align-items:center; justify-content:center; font-size:27px;
  box-shadow:0 8px 20px -8px rgba(255,107,44,.9); transform:rotate(-6deg); }}
.pn-wordmark {{ font-family:var(--pn-display); font-weight:800; font-size:36px; letter-spacing:-.04em; line-height:1; }}
.pn-h1 {{ font-family:var(--pn-display); font-weight:700; font-size:40px; line-height:1.04; letter-spacing:-.035em; margin:6px 0 0; }}
.pn-h1 span {{ color:#FFB48F; }}
.pn-lead {{ font-size:15.5px; line-height:1.6; color:#D5DCFF; max-width:520px; }}
.pn-trust {{ list-style:none; padding:0; margin:4px 0 0; display:flex; flex-wrap:wrap; gap:8px 18px; }}
.pn-trust li {{ font-size:13px; color:#E8ECFF; display:flex; align-items:center; gap:8px; }}
.pn-trust i {{ width:7px; height:7px; border-radius:50%; background:{ORANGE}; display:inline-block; }}
.pn-grid {{ display:grid; grid-template-columns:280px minmax(0,1fr); gap:14px; margin:0 0 22px; }}
.pn-phone-tile {{ background:{LAV2}; border-radius:26px; padding:26px 0 0; display:flex; justify-content:center; align-items:flex-end; overflow:hidden; min-height:430px; }}
.pn-phone {{ width:212px; height:410px; background:#101322; border-radius:38px 38px 0 0; padding:9px 9px 0; box-shadow:0 30px 60px -26px rgba(11,27,75,.7); position:relative; }}
.pn-phone:before {{ content:''; position:absolute; top:14px; left:50%; width:62px; height:16px; margin-left:-31px; border-radius:10px; background:#101322; z-index:3; }}
.pn-screen {{ background:linear-gradient(180deg,#FFF1E8,#FFDCC7); height:100%; border-radius:30px 30px 0 0; position:relative; overflow:hidden; display:flex; align-items:center; justify-content:center; }}
.pn-screen .pet {{ transform:scale(1.5); margin-top:-40px; }}
.pn-scanring {{ position:absolute; left:50%; top:46%; width:150px; height:112px; margin:-56px 0 0 -75px; border:3px solid {ORANGE}; border-radius:46% 46% 50% 50%; animation:pnpulse 2.4s ease-in-out infinite; }}
@keyframes pnpulse {{ 0%,100%{{opacity:.95; transform:scale(1);}} 50%{{opacity:.45; transform:scale(1.06);}} }}
.pn-scanpill {{ position:absolute; left:14px; right:14px; bottom:62px; background:rgba(255,255,255,.95); border-radius:16px; padding:9px 10px; font:600 12px 'Inter',sans-serif; color:#047857; text-align:center; transform:rotate(-4deg); }}
.pn-bar {{ position:absolute; left:0; right:0; bottom:0; height:46px; background:#101322; border-radius:18px 18px 0 0; display:flex; justify-content:center; align-items:center; gap:18px; color:#fff; font-size:12px; }}
.pn-bar b {{ background:{ORANGE}; width:30px; height:30px; border-radius:50%; display:inline-flex; align-items:center; justify-content:center; font-size:14px; }}
.pn-right {{ display:flex; flex-direction:column; gap:14px; min-width:0; }}
.pn-flow-tile {{ background:{LAV}; border-radius:26px; padding:22px; }}
.pn-flow {{ display:flex; align-items:center; gap:10px; flex-wrap:wrap; margin-top:12px; }}
.pn-node {{ background:#fff; border:1px solid {LINE}; border-radius:14px; padding:10px 14px; font:600 13.5px 'Inter',sans-serif; color:{INK}; box-shadow:0 6px 16px -12px rgba(11,27,75,.5); }}
.pn-node small {{ display:block; font-weight:500; font-size:11px; color:{MUTED}; margin-top:2px; }}
.pn-node .ok {{ display:inline-block; margin-top:4px; font-size:10.5px; font-weight:700; color:{BLUE}; border:1px solid {BLUE}; border-radius:6px; padding:1px 6px; background:#fff; }}
.pn-node.sq {{ width:46px; height:46px; padding:0; display:flex; align-items:center; justify-content:center; font-size:22px; background:{ORANGE}; border-color:{ORANGE}; }}
.pn-arrow {{ color:{BLUE}; font-weight:700; }}
.pn-stack {{ display:flex; flex-direction:column; gap:8px; }}
.pn-console-tile {{ background:{LAV2}; border-radius:26px; padding:22px; flex:1; }}
.pn-console {{ background:#fff; border-radius:18px; padding:18px 20px; border:1px solid {LINE}; }}
.pn-console h4 {{ font-family:var(--pn-display); font-size:18px; margin:0; color:{INK}; }}
.pn-console p {{ margin:2px 0 14px; font-size:12.5px; color:{MUTED}; }}
.pn-kpis {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(130px,1fr)); gap:10px; }}
.pn-kpi {{ background:#F3F5FD; border-radius:14px; padding:12px 14px; }}
.pn-kpi .k {{ font-size:11px; color:{MUTED}; }} .pn-kpi .v {{ font:700 24px 'Sora',sans-serif; color:{BLUE}; letter-spacing:-.03em; margin-top:2px; }}
.pn-kpi .v small {{ font-size:11px; color:{MUTED}; font-weight:600; }}
.pn-example {{ font-size:11px; color:{MUTED}; margin-top:10px; }}
@media (max-width:820px) {{
  .pn-grid {{ grid-template-columns:1fr; }}
  .pn-phone-tile {{ min-height:0; padding-top:22px; }}
  .pn-h1 {{ font-size:31px; }} .pn-brand-tile {{ padding:24px 22px; }}
}}
</style>
"""


def hero_html(lang: str, mascot_html: str = "") -> str:
    el = lang == "el"
    tx = {
        "kicker": "Ζωτικά & μακροζωία για κατοικίδια" if el else "Vitals & longevity for pets",
        "h1": ("Δες πώς είναι το κατοικίδιό σου, <span>πριν χρειαστεί ο κτηνίατρος.</span>" if el
               else "See how your pet is really doing, <span>before the vet visit.</span>"),
        "lead": ("Μέτρηση αναπνοών με την κάμερα, έλεγχος μακροζωίας και δομημένη αξιολόγηση συμπτωμάτων με παραπομπές MSD — "
                 "χωρίς να υποκαθιστά τον κτηνίατρο." if el else
                 "Camera breathing count, a longevity check and a structured symptom assessment with MSD references — "
                 "without replacing your vet."),
        "t1": "Παραπομπές MSD Vet Manual" if el else "MSD Vet Manual references",
        "t2": "Έλεγχος επείγοντος πάντα ενεργός" if el else "Emergency check always on",
        "t3": "GDPR · χωρίς αποθήκευση φωτογραφιών" if el else "GDPR · no photos stored",
        "flow_t": "Πώς δουλεύει" if el else "How it works",
        "n1": "Το κατοικίδιό σου" if el else "Your pet", "n1s": "Είδος · ηλικία · βάρος" if el else "Species · age · weight",
        "n2": "Σάρωση αναπνοής" if el else "Breathing scan", "n2s": "Κάμερα ή μέτρημα με το χέρι" if el else "Camera or hand count",
        "n3": "Ζωτικά & φωτογραφίες" if el else "Vitals & photos", "n3s": "Μάτια · δέρμα · ούλα" if el else "Eyes · skin · gums",
        "n4": "AI αξιολόγηση" if el else "AI triage", "n4s": "Claude + MSD",
        "n5": "Αναφορά κτηνιάτρου" if el else "Vet report", "n5s": "PDF · Word",
        "conn": "Έτοιμο" if el else "Ready",
        "c_t": "Η σελίδα του κατοικιδίου" if el else "Your pet's page",
        "c_s": "Παράδειγμα με φανταστικό κατοικίδιο" if el else "Example with an imaginary pet",
        "k1": "Αναπνοές ηρεμίας" if el else "Resting breaths", "k2": "Σωματική κατάσταση" if el else "Body condition",
        "k3": "Ηλικία σε ανθρώπινα" if el else "Age in human years", "k4": "Στάδιο ζωής" if el else "Life stage",
        "k4v": "Μεσήλικο" if el else "Mature",
        "scan": "Σάρωση… μείνε ακίνητος" if el else "Scanning… keep still",
        "ex": "Τα νούμερα είναι ενδεικτικά." if el else "Figures shown are illustrative.",
    }
    return HERO_CSS + f"""
<div class="pn-hero-head">
  <div class="pn-brand-tile">
    <div class="pn-logo-row"><div class="pn-logo-mark">🐾</div><div class="pn-wordmark">PetAiNurse</div></div>
    <div><span class="pn-eyebrow dark">{tx['kicker']}</span></div>
    <div class="pn-h1">{tx['h1']}</div>
    <div class="pn-lead">{tx['lead']}</div>
    <ul class="pn-trust"><li><i></i>{tx['t1']}</li><li><i></i>{tx['t2']}</li><li><i></i>{tx['t3']}</li></ul>
  </div>
</div>
<div class="pn-grid">
  <div class="pn-phone-tile"><div class="pn-phone"><div class="pn-screen">
      <div class="pet">{mascot_html}</div><div class="pn-scanring"></div>
      <div class="pn-scanpill">{tx['scan']}</div>
      <div class="pn-bar"><span>🫁</span><b>●</b><span>❤️</span></div>
  </div></div></div>
  <div class="pn-right">
    <div class="pn-flow-tile">
      <span class="pn-eyebrow">{tx['flow_t']}</span>
      <div class="pn-flow">
        <div class="pn-node">{tx['n1']}<small>{tx['n1s']}</small></div><span class="pn-arrow">→</span>
        <div class="pn-node sq">🫁</div>
        <div class="pn-stack">
          <div class="pn-node">{tx['n2']}<small>{tx['n2s']}</small><span class="ok">● {tx['conn']}</span></div>
          <div class="pn-node">{tx['n3']}<small>{tx['n3s']}</small><span class="ok">● {tx['conn']}</span></div>
        </div><span class="pn-arrow">→</span>
        <div class="pn-node">{tx['n4']}<small>{tx['n4s']}</small></div><span class="pn-arrow">→</span>
        <div class="pn-node">{tx['n5']}<small>{tx['n5s']}</small></div>
      </div>
    </div>
    <div class="pn-console-tile"><div class="pn-console">
      <h4>{tx['c_t']}</h4><p>{tx['c_s']}</p>
      <div class="pn-kpis">
        <div class="pn-kpi"><div class="k">{tx['k1']}</div><div class="v">22 <small>/min</small></div></div>
        <div class="pn-kpi"><div class="k">{tx['k2']}</div><div class="v">5 <small>/9</small></div></div>
        <div class="pn-kpi"><div class="k">{tx['k3']}</div><div class="v">47</div></div>
        <div class="pn-kpi"><div class="k">{tx['k4']}</div><div class="v" style="font-size:18px;padding-top:5px">{tx['k4v']}</div></div>
      </div>
      <div class="pn-example">{tx['ex']}</div>
    </div></div>
  </div>
</div>
"""


# ── longevity result building blocks ──────────────────────────────────────────
def pillar_html(pl: dict, levels: list) -> str:
    bars = "".join(
        f'<span style="flex:1;height:8px;border-radius:6px;background:{(col if i <= pl["score"] else "#E3E7F8")};"></span>'
        for i, (_k, _e, _n, col) in enumerate(levels))
    val = f'<div style="font:700 16px Sora,Inter,sans-serif;color:{INK};white-space:nowrap;">{_h.escape(pl["value"])}</div>' if pl.get("value") else ""
    return (f'<div style="background:#fff;border:1px solid {LINE};border-radius:18px;padding:14px 16px;margin-bottom:10px;">'
            f'<div style="display:flex;justify-content:space-between;align-items:baseline;gap:10px;">'
            f'<div style="font-weight:700;font-size:14.5px;color:{INK};">{_h.escape(pl["name"])}</div>{val}</div>'
            f'<div style="display:flex;gap:4px;margin:10px 0 6px;">{bars}</div>'
            f'<div style="font-size:12.5px;font-weight:700;color:{pl["color"]};">{_h.escape(pl["label"])}</div></div>')


def result_card_html(res: dict, lang: str) -> str:
    el = lang == "el"
    name = _h.escape(res.get("name") or ("Το κατοικίδιο" if el else "Your pet"))
    ha = res.get("human_age")
    lo, hi = res.get("lifespan", (0, 0))
    pct = res.get("life_pct", 0)
    ha_html = (f'<div style="font:800 54px Sora,Inter,sans-serif;letter-spacing:-.04em;line-height:1;">{ha}</div>'
               f'<div style="color:#D5DCFF;font-size:14px;line-height:1.5;">{"ανθρώπινα χρόνια" if el else "human years"} · '
               f'{res["years"]} {"ετών" if el else "years old"}<br><b style="color:#fff">{_h.escape(res.get("stage",""))}</b></div>'
               if ha is not None else
               f'<div style="font:800 30px Sora,Inter,sans-serif;">{res["years"]} {"έτη" if el else "years"}</div>')
    return f"""
<div style="background:radial-gradient(120% 90% at 100% 0%, rgba(47,85,240,.7) 0%, rgba(47,85,240,0) 60%), {BLUE};
  border-radius:24px;padding:22px 22px 18px;margin:0 0 12px;color:#fff;box-shadow:0 26px 50px -30px rgba(18,55,201,.8);">
  <span class="pn-eyebrow dark">{"ΕΛΕΓΧΟΣ ΜΑΚΡΟΖΩΙΑΣ" if el else "LONGEVITY CHECK"} · {name}</span>
  <div style="display:flex;align-items:flex-end;gap:16px;margin-top:14px;flex-wrap:wrap;">{ha_html}
    <div style="margin-left:auto;text-align:right;"><div style="font:800 34px Sora,Inter,sans-serif;color:#FFB48F;letter-spacing:-.03em;">{res.get("score", 0)}<small style="font-size:14px;color:#D5DCFF;">/100</small></div>
    <div style="font-size:12px;color:#D5DCFF;">{"δείκτης ευεξίας" if el else "wellness score"}</div></div></div>
  <div style="margin-top:16px;">
    <div style="display:flex;justify-content:space-between;font-size:11.5px;color:#D5DCFF;margin-bottom:5px;"><span>0</span>
      <span>{"τυπική διάρκεια ζωής" if el else "typical lifespan"} {lo}–{hi} {"έτη" if el else "yrs"}</span></div>
    <div style="height:9px;border-radius:9px;background:rgba(255,255,255,.2);overflow:hidden;"><div style="width:{pct}%;height:100%;background:{ORANGE};border-radius:9px;"></div></div>
  </div>
  <div style="color:#B9C4FF;font-size:11.5px;margin-top:10px;">{"Εκτίμηση ευεξίας από όσα παρατηρείς — όχι διάγνωση. Το εύρος ζωής είναι τυπικό για το μέγεθος/είδος, όχι πρόβλεψη για το δικό σου ζώο." if el else "A wellness estimate from what you observe — not a diagnosis. The lifespan range is typical for the size/species, not a prediction for your animal."}</div>
</div>"""
