"""
petify_ui.py — Petify-inspired visual layer for PetAiNurse (Kira AI Pet).

Original design in the same spirit as the Petify product page: a royal-blue brand
tile, lavender flow panels, an orange accent, a phone-scan visual and a small
"console" card. No third-party artwork, logos or copy are used.

Pure string builders — no Streamlit import — so they are easy to test.
"""
from __future__ import annotations

import html as _h

import petify_art as _art

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
div[data-testid="stHorizontalBlock"]:has([class*="pn-feat-"]) > div[data-testid="stColumn"] > div[data-testid="stVerticalBlock"] > div[data-testid="stLayoutWrapper"] {{ flex:1 1 auto; display:flex; flex-direction:column; }}
div[data-testid="stHorizontalBlock"]:has([class*="pn-feat-"]) > div[data-testid="stColumn"] > div[data-testid="stVerticalBlock"] > div[data-testid="stLayoutWrapper"] > div[data-testid="stVerticalBlock"] {{ flex:1 1 auto; justify-content:space-between; }}

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
@media (max-width:640px) {{ .pn-h2 {{ font-size:24px; }} .pn-resface {{ display:none; }} }}

/* Illustrated cards & banners */
.pn-art-wrap {{ border-radius:20px; overflow:hidden; aspect-ratio:400/196; margin:0 0 14px; background:{LAV}; }}
.pn-art-wrap.sm {{ aspect-ratio:400/160; margin-bottom:12px; }}
.pn-art-wrap img, .pn-screen .pet img, .pn-mascot img {{ mix-blend-mode:multiply; }}
.pn-banner {{ display:grid; grid-template-columns:minmax(0,1fr) 340px; gap:0; border-radius:26px; overflow:hidden; margin:4px 0 18px;
  background:{LAV}; border:1px solid {LAV2}; align-items:stretch; }}
.pn-banner.dark {{ background:radial-gradient(120% 100% at 100% 0%, rgba(47,85,240,.7) 0%, rgba(47,85,240,0) 60%), {BLUE}; border:none;
  box-shadow:0 26px 50px -32px rgba(18,55,201,.75); }}
.pn-banner .tx {{ padding:22px 24px; display:flex; flex-direction:column; justify-content:center; gap:6px; min-width:0; }}
.pn-banner .org {{ font:700 10.5px/1 'Inter',sans-serif; letter-spacing:.14em; text-transform:uppercase; color:{BLUE}; }}
.pn-banner.dark .org {{ color:#FFB48F; }}
.pn-banner .ttl {{ font-family:var(--pn-display); font-weight:700; font-size:26px; line-height:1.12; letter-spacing:-.03em; color:{INK}; }}
.pn-banner.dark .ttl {{ color:#fff; }}
.pn-banner .sb {{ font-size:13.5px; line-height:1.5; color:{MUTED}; }}
.pn-banner.dark .sb {{ color:#D5DCFF; }}
.pn-banner .art {{ min-height:150px; }}
@media (max-width:640px) {{
  .pn-banner {{ grid-template-columns:1fr; }} .pn-banner .art {{ order:-1; height:132px; min-height:0; }}
  .pn-banner .ttl {{ font-size:21px; }} .pn-banner .tx {{ padding:16px 18px 18px; }}
}}
.pn-pillar {{ display:flex; gap:12px; align-items:flex-start; }}
.pn-pillar .ic {{ width:40px; height:40px; border-radius:13px; background:{LAV}; display:flex; align-items:center; justify-content:center; flex-shrink:0; }}
.pn-snap {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(150px,1fr)); gap:10px; margin:12px 0 4px; }}
.pn-snap .it {{ background:#fff; border:1px solid {LINE}; border-radius:20px; padding:14px 16px; display:flex; gap:12px; align-items:center; }}
.pn-snap .ic {{ width:42px; height:42px; border-radius:14px; background:{LAV}; display:flex; align-items:center; justify-content:center; flex-shrink:0; }}
.pn-snap .k {{ font-size:11.5px; color:{MUTED}; }} .pn-snap .v {{ font:700 20px 'Sora',sans-serif; color:{INK}; letter-spacing:-.03em; line-height:1.15; }}
.pn-snap .v small {{ font-size:11px; color:{MUTED}; font-weight:600; }}
.pn-gallery {{ display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:14px; margin:0 0 22px; }}
.pn-gcard {{ background:#fff; border:1px solid {LINE}; border-radius:24px; overflow:hidden; display:flex; flex-direction:column; }}
.pn-gcard .im {{ aspect-ratio:400/200; }} .pn-gcard .bd {{ padding:16px 18px 20px; }}
.pn-gcard .n {{ font:700 11px 'Inter',sans-serif; letter-spacing:.12em; color:{ORANGE}; }}
.pn-gcard h4 {{ font-family:var(--pn-display); font-size:18px; letter-spacing:-.02em; margin:6px 0 6px; color:{INK}; line-height:1.2; }}
.pn-gcard p {{ margin:0; font-size:13px; line-height:1.55; color:{MUTED}; }}
@media (max-width:820px) {{ .pn-gallery {{ grid-template-columns:1fr; }} .pn-gcard .im {{ height:150px; }} }}
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
.pn-brand-tile {{ flex:1 1 360px; position:relative; overflow:hidden; background:radial-gradient(120% 100% at 100% 0%, rgba(47,85,240,.7) 0%, rgba(47,85,240,0) 60%), {BLUE};
  border-radius:26px; padding:30px 30px 28px; color:#fff; display:flex; flex-direction:column; gap:14px; box-shadow:0 30px 60px -34px rgba(18,55,201,.8); }}
.pn-hero-art {{ position:absolute; right:0; top:0; bottom:0; width:44%; }}
.pn-hero-art .fw {{ position:absolute; right:26px; left:0; top:50%; transform:translateY(-50%); aspect-ratio:400/230; }}
.pn-hero-art .frame {{ position:absolute; inset:0; border-radius:22px; overflow:hidden; box-shadow:0 24px 50px -26px rgba(0,0,0,.55); }}
.pn-hero-art .chip {{ position:absolute; background:#fff; color:{INK}; border-radius:14px; padding:8px 12px; font:700 12px 'Inter',sans-serif; box-shadow:0 14px 30px -14px rgba(0,0,0,.5); z-index:2; }}
.pn-hero-art .chip b {{ color:{BLUE}; font:800 17px 'Sora',sans-serif; display:block; letter-spacing:-.02em; }}
.pn-hero-art .chip.a {{ left:10px; bottom:-18px; }} .pn-hero-art .chip.b {{ right:-10px; top:-16px; background:{ORANGE}; color:#fff; }}
.pn-hero-art .chip.b b {{ color:#fff; }}
.pn-hero-copy {{ position:relative; z-index:1; max-width:52%; display:flex; flex-direction:column; gap:14px; }}
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
  .pn-hero-art {{ position:relative; width:auto; height:190px; order:-1; margin:-24px -22px 8px; }}
  .pn-hero-art .fw {{ position:absolute; inset:0; transform:none; aspect-ratio:auto; right:0; }}
  .pn-hero-art .frame {{ border-radius:0; box-shadow:none; }}
  .pn-hero-art .chip {{ display:none; }} .pn-hero-art {{ height:210px; }}
  .pn-hero-copy {{ max-width:none; }}
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
    gallery = gallery_html(lang)
    art = _art.scene("breath", "dog")
    c1 = "Αναπνοές ηρεμίας" if el else "Resting breaths"
    c2 = "Ηλικία σε ανθρώπινα" if el else "Human years"
    return (HERO_CSS + f"""
<div class="pn-hero-head">
  <div class="pn-brand-tile">
    <div class="pn-hero-art"><div class="fw"><div class="frame">__ART_BREATH__</div>
      <div class="chip a"><span>__C1__</span><b>22 /min</b></div><div class="chip b"><span>__C2__</span><b>45 ↗</b></div></div></div>
    <div class="pn-hero-copy">
    <div class="pn-logo-row"><div class="pn-logo-mark">🐾</div><div class="pn-wordmark">PetAiNurse</div></div>
    <div><span class="pn-eyebrow dark">{tx['kicker']}</span></div>
    <div class="pn-h1">{tx['h1']}</div>
    <div class="pn-lead">{tx['lead']}</div>
    <ul class="pn-trust"><li><i></i>{tx['t1']}</li><li><i></i>{tx['t2']}</li><li><i></i>{tx['t3']}</li></ul>
    </div>
  </div>
</div>
{gallery}
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
""").replace("__ART_BREATH__", art).replace("__C1__", c1).replace("__C2__", c2)


# ── longevity result building blocks ──────────────────────────────────────────
def pillar_html(pl: dict, levels: list) -> str:
    bars = "".join(
        f'<span style="flex:1;height:8px;border-radius:6px;background:{(col if i <= pl["score"] else "#E3E7F8")};"></span>'
        for i, (_k, _e, _n, col) in enumerate(levels))
    val = f'<div style="font:700 16px Sora,Inter,sans-serif;color:{INK};white-space:nowrap;">{_h.escape(pl["value"])}</div>' if pl.get("value") else ""
    ic = _art.pillar_icon(pl.get("id", ""), pl.get("color", BLUE))
    return (f'<div class="pn-pillar" style="background:#fff;border:1px solid {LINE};border-radius:20px;padding:14px 16px;margin-bottom:10px;">'
            f'<div class="ic">{ic}</div><div style="flex:1;min-width:0;">'
            f'<div style="display:flex;justify-content:space-between;align-items:baseline;gap:10px;">'
            f'<div style="font-weight:700;font-size:14.5px;color:{INK};">{_h.escape(pl["name"])}</div>{val}</div>'
            f'<div style="display:flex;gap:4px;margin:10px 0 6px;">{bars}</div>'
            f'<div style="font-size:12.5px;font-weight:700;color:{pl["color"]};">{_h.escape(pl["label"])}</div></div></div>')


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
  border-radius:24px;padding:22px 22px 18px;margin:0 0 12px;color:#fff;box-shadow:0 26px 50px -30px rgba(18,55,201,.8);position:relative;overflow:hidden;">
  <div class="pn-resface" style="position:absolute;right:16px;top:14px;opacity:.95;">{_art.species_face(res.get("species","dog"), 74)}</div>
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


# ── illustrated blocks ───────────────────────────────────────────────────────
_BANNER_SCENE = {"🫁": ("breath", True), "🧬": ("longevity", True), "❤️": ("vitals", False),
                 "💬": ("symptoms", False), "📋": ("report", False), "📷": ("photo", False),
                 "📍": ("vets", False), "🧪": ("labs", False), "📅": ("diary", False),
                 "🛡️": ("shield", False), "🩺": ("nurse", True),
                 "🐾": ("pets", False), "📏": ("measure", False), "🩹": ("report", False), "💊": ("meds", False)}
BANNER_ICONS = tuple(_BANNER_SCENE.keys())


def banner_html(icon: str, title: str, sub: str, org: str, species: str = "dog") -> str:
    scene, dark = _BANNER_SCENE.get(icon, ("symptoms", False))
    sp = species if species in ("dog", "cat") else "dog"
    return (f'<div class="pn-banner{" dark" if dark else ""}"><div class="tx"><div class="org">{_h.escape(org)}</div>'
            f'<div class="ttl">{_h.escape(title)}</div>' + (f'<div class="sb">{_h.escape(sub)}</div>' if sub else "") +
            f'</div><div class="art">{_art.scene(scene, sp)}</div></div>')


def feature_art_html(kind: str, species: str = "dog", compact: bool = False, raw: bool = False) -> str:
    scene = {"assess": "symptoms", "scan": "breath"}.get(kind, kind)
    sp = species if species in ("dog", "cat") else "dog"
    svg = _art.scene(scene, sp)
    if raw:
        return svg
    return f'<div class="pn-art-wrap{" sm" if compact else ""}">{svg}</div>'


def snapshot_html(items: list) -> str:
    """items: [(pillar_icon_id, label, value_html)] -> small illustrated stat tiles."""
    cells = "".join(f'<div class="it"><div class="ic">{_art.pillar_icon(i)}</div><div><div class="k">{_h.escape(k)}</div>'
                    f'<div class="v">{v}</div></div></div>' for i, k, v in items)
    return f'<div class="pn-snap">{cells}</div>'


def gallery_html(lang: str, species: str = "dog") -> str:
    el = lang == "el"
    cards = [
        ("breath", "01", "Μέτρησε τις αναπνοές" if el else "Count the breaths",
         "60 δευτερόλεπτα με την κάμερα δίπλα στο κατοικίδιο που κοιμάται." if el else "60 seconds with the camera beside your sleeping pet."),
        ("longevity", "02", "Δες τα χρόνια του" if el else "See their years",
         "Ηλικία σε ανθρώπινα χρόνια, δείκτης ευεξίας και πλάνο φροντίδας." if el else "Age in human years, a wellness score and a care plan."),
        ("symptoms", "03", "Πες τι παρατηρείς" if el else "Tell us what you notice",
         "Μία ερώτηση τη φορά και αναφορά για τον κτηνίατρο με παραπομπές MSD." if el else "One question at a time, then a vet report with MSD references."),
    ]
    sp = species if species in ("dog", "cat") else "dog"
    return '<div class="pn-gallery">' + "".join(
        f'<div class="pn-gcard"><div class="im">{_art.scene(k, sp)}</div><div class="bd"><div class="n">{n}</div><h4>{t}</h4><p>{b}</p></div></div>'
        for k, n, t, b in cards) + '</div>'


# ── landing page (what PetAiNurse does + the other services) ─────────────────
LANDING_CSS = f"""
<style>
.pn-l-hero {{ display:grid; grid-template-columns:minmax(0,1fr) 380px; gap:22px; align-items:center; background:radial-gradient(120% 100% at 100% 0%, rgba(47,85,240,.7) 0%, rgba(47,85,240,0) 60%), {BLUE};
  border-radius:28px; padding:34px 32px; color:#fff; box-shadow:0 30px 60px -34px rgba(18,55,201,.8); margin:4px 0 14px; }}
.pn-l-hero h1 {{ font-family:var(--pn-display); font-weight:700; font-size:40px; line-height:1.06; letter-spacing:-.035em; margin:14px 0 12px; color:#fff; }}
.pn-l-hero h1 span {{ color:#FFB48F; }}
.pn-l-hero p {{ font-size:15.5px; line-height:1.65; color:#D5DCFF; max-width:520px; margin:0; }}
.pn-l-hero .art {{ border-radius:22px; overflow:hidden; aspect-ratio:400/220; box-shadow:0 24px 50px -26px rgba(0,0,0,.55); }}
.pn-l-svc {{ display:grid; grid-template-columns:minmax(0,1.05fr) minmax(0,1fr); gap:0; background:#fff; border:1px solid {LINE}; border-radius:28px; overflow:hidden; margin:0 0 16px; }}
.pn-l-svc.flip .art {{ order:2; }}
.pn-l-svc .art {{ display:flex; align-items:center; padding:22px; background:linear-gradient(160deg,{LAV},#fff); }}
.pn-l-svc .art svg {{ position:static !important; width:100%; height:auto !important; aspect-ratio:400/220; flex:none; border-radius:22px; box-shadow:0 18px 36px -24px rgba(11,27,75,.45); }}
.pn-l-svc .bd {{ padding:28px 30px 28px; display:flex; flex-direction:column; gap:10px; min-width:0; }}
.pn-l-svc .meta {{ font-size:12px; color:{MUTED}; }}
.pn-l-svc h2 {{ font-family:var(--pn-display); font-weight:700; font-size:26px; line-height:1.12; letter-spacing:-.03em; color:{INK}; margin:2px 0 0; }}
.pn-l-svc .sum {{ font-size:14.5px; line-height:1.6; color:{MUTED}; }}
.pn-l-svc .prob {{ background:{LAV}; border:1px solid {LAV2}; border-radius:16px; padding:12px 14px; font-size:13.5px; line-height:1.55; color:{INK}; }}
.pn-l-svc .prob b {{ display:block; font:800 11px 'Inter',sans-serif; letter-spacing:.12em; color:{BLUE}; margin-bottom:3px; text-transform:uppercase; }}
.pn-l-svc h3 {{ font:800 11px 'Inter',sans-serif; letter-spacing:.12em; text-transform:uppercase; color:{ORANGE}; margin:6px 0 0; }}
.pn-l-svc ol {{ list-style:none; margin:0; padding:0; display:flex; flex-direction:column; gap:9px; counter-reset:s; }}
.pn-l-svc li {{ counter-increment:s; display:flex; gap:11px; align-items:flex-start; font-size:13.5px; line-height:1.5; color:{INK}; }}
.pn-l-svc li:before {{ content:counter(s); flex:0 0 24px; height:24px; border-radius:50%; background:{BLUE}; color:#fff; font:700 12px 'Inter',sans-serif; display:flex; align-items:center; justify-content:center; margin-top:1px; }}
.pn-l-svc .note {{ font-size:11.5px; color:{MUTED}; line-height:1.5; }}
.pn-l-svc.main {{ border-color:{BLUE}; box-shadow:0 26px 50px -36px rgba(18,55,201,.6); }}
.pn-l-more {{ display:grid; grid-template-columns:repeat(5,minmax(0,1fr)); gap:12px; margin:0 0 18px; }}
.pn-l-more .c {{ background:#fff; border:1px solid {LINE}; border-radius:20px; overflow:hidden; }}
.pn-l-more .im {{ aspect-ratio:400/190; }} .pn-l-more .t {{ padding:10px 12px 12px; font:700 13px 'Sora',sans-serif; color:{INK}; letter-spacing:-.01em; line-height:1.25; }}
.pn-l-more .t small {{ display:block; font:500 11.5px 'Inter',sans-serif; color:{MUTED}; margin-top:3px; letter-spacing:0; }}
@media (max-width:900px) {{ .pn-l-more {{ grid-template-columns:repeat(2,minmax(0,1fr)); }} }}
@media (max-width:820px) {{
  .pn-l-hero {{ grid-template-columns:1fr; padding:24px 22px; }} .pn-l-hero h1 {{ font-size:30px; }} .pn-l-hero .art {{ order:-1; }}
  .pn-l-svc {{ grid-template-columns:1fr; }} .pn-l-svc.flip .art {{ order:0; }} .pn-l-svc .art {{ padding:14px 14px 0; }}
  .pn-l-svc .bd {{ padding:20px 20px 22px; }} .pn-l-svc h2 {{ font-size:22px; }}
}}
</style>
"""


def landing_parts(lang: str) -> dict:
    el = lang == "el"
    hero = f"""{LANDING_CSS}
<div class="pn-l-hero"><div>
  <span class="pn-eyebrow dark">{"AI ΚΤΗΝΙΑΤΡΙΚΗ ΝΟΣΗΛΕΥΤΡΙΑ" if el else "AI VET NURSE"}</span>
  <h1>{"Πες τι παρατηρείς. <span>Η PetAiNurse ρωτά, εξηγεί και ετοιμάζει την αναφορά.</span>" if el else "Tell us what you notice. <span>PetAiNurse asks, explains and prepares the report.</span>"}</h1>
  <p>{"Δομημένη αξιολόγηση συμπτωμάτων με παραπομπές MSD Vet Manual — και γύρω της υπηρεσίες για κάλυψη ασφαλιστηρίου, μακροζωία και ιατρική αναφορά. Συμπληρώνει, δεν αντικαθιστά τον κτηνίατρο." if el
      else "A structured symptom assessment with MSD Vet Manual references — with services around it for insurance coverage, longevity and the medical report. It complements your vet, never replaces them."}</p>
</div><div class="art">{_art.scene("nurse", "dog")}</div></div>"""

    def svc(scene, flip, main, tag, title, summary, problem, steps, note=""):
        lis = "".join(f"<li>{x}</li>" for x in steps)
        return (f'<div class="pn-l-svc{" flip" if flip else ""}{" main" if main else ""}"><div class="art">{_art.scene(scene, "dog").replace("slice","meet")}</div>'
                f'<div class="bd"><div><span class="pn-eyebrow{" orange" if main else ""}">{tag}</span></div><h2>{title}</h2><div class="sum">{summary}</div>'
                f'<div class="prob"><b>{"Το πρόβλημα" if el else "The problem"}</b>{problem}</div>'
                f'<h3>{"Πώς δουλεύει" if el else "How it works"}</h3><ol>{lis}</ol>'
                + (f'<div class="note">{note}</div>' if note else "") + '</div></div>')

    if el:
        services = "".join([
            svc("nurse", False, True, "ΚΥΡΙΑ ΥΠΗΡΕΣΙΑ", "PetAiNurse — εκτίμηση συμπτωμάτων",
                "Ο ιδιοκτήτης περιγράφει τι βλέπει· η PetAiNurse ρωτά μία ερώτηση τη φορά και ετοιμάζει δομημένη σύνοψη για τον κτηνίατρο.",
                "Στο σπίτι δεν ξέρεις αν ένα σύμπτωμα θέλει αναμονή ή επείγον. Στο ιατρείο, ο κτηνίατρος έχει λίγα λεπτά και ένα ασαφές ιστορικό.",
                ["Φτιάχνεις το προφίλ του κατοικιδίου: είδος, ηλικία, βάρος, φάρμακα.",
                 "Περιγράφεις με λόγια, με φωνή ή με γρήγορες επιλογές. Προαιρετικά προσθέτεις φωτογραφία, ζωτικά ή εξετάσεις.",
                 "Η PetAiNurse ρωτά μία ερώτηση τη φορά· ο έλεγχος επείγοντος είναι πάντα ενεργός.",
                 "Παίρνεις αξιολόγηση με παραπομπές MSD και οδηγία για το επόμενο βήμα."],
                "Δεν είναι διάγνωση. Σε επείγουσες καταστάσεις επικοινώνησε αμέσως με κτηνίατρο."),
            svc("shield", True, False, "ΑΣΦΑΛΙΣΤΙΚΗ ΚΑΛΥΨΗ", "Έλεγχος κάλυψης ασφαλιστηρίου",
                "Μετά την αξιολόγηση, η AI ελέγχει αν η κατάσταση καλύπτεται από το ασφαλιστήριο του κατοικιδίου σου και πόσο θα πληρώσεις.",
                "Οι ιδιοκτήτες δεν ξέρουν αν και πόσο καλύπτεται ένα ραντεβού πριν πάνε στην κλινική.",
                ["Επιλέγεις την ασφαλιστική σου στο προφίλ.",
                 "Ολοκληρώνεις την αξιολόγηση συμπτωμάτων.",
                 "Βλέπεις αν καλύπτεται, τη συμμετοχή ανά επίσκεψη ή εξέταση και τις συμβεβλημένες κλινικές.",
                 "Ρωτάς ό,τι θέλεις για το συμβόλαιό σου."],
                "Ο έλεγχος γίνεται από AI και δεν είναι επίσημη γνωμάτευση της ασφαλιστικής. 7 μέρες δωρεάν."),
            svc("longevity", False, False, "ΜΑΚΡΟΖΩΙΑ", "Έλεγχος μακροζωίας",
                "Ηλικία σε ανθρώπινα χρόνια, δείκτης ευεξίας 0–100 και πλάνο φροντίδας για περισσότερα χρόνια μαζί.",
                "«Πόσο χρονών είναι πραγματικά;» και «τι να αλλάξω για να ζήσει περισσότερο;» δεν έχουν απλή απάντηση.",
                ["Απαντάς σε 5 ερωτήσεις: βάρος, δόντια, δραστηριότητα, πρόληψη.",
                 "Προαιρετικά μετράς τις αναπνοές στον ύπνο με την κάμερα του κινητού.",
                 "Βλέπεις ηλικία σε ανθρώπινα χρόνια και επίπεδο ανά τομέα.",
                 "Παίρνεις πλάνο με τα επόμενα βήματα."],
                "Εκτίμηση ευεξίας — όχι διάγνωση ή πρόβλεψη για το δικό σου ζώο."),
            svc("report", True, False, "ΙΑΤΡΙΚΗ ΑΝΑΦΟΡΑ", "Αναφορά για τον κτηνίατρο",
                "Η συζήτηση, οι μετρήσεις και οι εξετάσεις γίνονται ένα καθαρό έγγραφο για το ιατρείο.",
                "Στο ιατρείο θυμάσαι τα μισά και οι εξετάσεις είναι σκόρπιες σε φωτογραφίες και PDF.",
                ["Ολοκληρώνεις τη συζήτηση με την PetAiNurse.",
                 "Συγκεντρώνονται προφίλ, ζωτικά, φωτογραφίες και εξετάσεις.",
                 "Επιλέγεις γλώσσα για την αναφορά.",
                 "Την κατεβάζεις ή την τυπώνεις και την παίρνεις μαζί σου."]),
        ])
        more_t = "ΚΑΙ ΑΚΟΜΑ"
        more = [("breath", "Ζωτικά & αναπνοές", "Κάμερα ή με το χέρι"), ("photo", "Φωτογραφία", "Μάτια, δέρμα, ούλα"),
                ("labs", "Εξετάσεις", "PDF ή φωτογραφία"), ("diary", "Ημερολόγιο", "Συμπτώματα στο χρόνο"), ("vets", "Κτηνίατρος", "Κοντινός & επείγων")]
        foot = "Η PetAiNurse δεν παρέχει κτηνιατρική διάγνωση και δεν αντικαθιστά τον κτηνίατρο."
    else:
        services = "".join([
            svc("nurse", False, True, "MAIN SERVICE", "PetAiNurse — symptom assessment",
                "The owner describes what they see; PetAiNurse asks one question at a time and prepares a structured summary for the vet.",
                "At home you can't tell whether a symptom can wait or is an emergency. At the clinic the vet has a few minutes and a vague history.",
                ["Create your pet's profile: species, age, weight, medication.",
                 "Describe it in words, by voice or with quick picks. Optionally add a photo, vitals or lab results.",
                 "PetAiNurse asks one question at a time; the emergency check is always on.",
                 "You get an assessment with MSD references and a next step."],
                "Not a diagnosis. In an emergency contact a vet immediately."),
            svc("shield", True, False, "INSURANCE COVERAGE", "Policy coverage check",
                "After the assessment, the AI checks whether the condition is covered by your pet's policy and what you would pay.",
                "Owners don't know whether, or how much, a visit is covered before they reach the clinic.",
                ["Choose your insurer in the profile.",
                 "Finish the symptom assessment.",
                 "See whether it is covered, the co-payment per visit or test, and the network clinics.",
                 "Ask anything about your policy."],
                "The check is done by AI and is not an official statement from your insurer. 7 days free."),
            svc("longevity", False, False, "LONGEVITY", "Longevity check",
                "Age in human years, a 0–100 wellness score and a care plan for more years together.",
                "\"How old are they really?\" and \"what should I change so they live longer?\" have no simple answer.",
                ["Answer 5 questions: weight, teeth, activity, prevention.",
                 "Optionally count sleeping breaths with your phone camera.",
                 "See age in human years and a level for each area.",
                 "Get a plan with next steps."],
                "A wellness estimate — not a diagnosis or a prediction for your animal."),
            svc("report", True, False, "MEDICAL REPORT", "Report for the vet",
                "The chat, the measurements and the lab results become one clean document for the clinic.",
                "At the clinic you forget half of it, and the tests are scattered across photos and PDFs.",
                ["Finish the chat with PetAiNurse.",
                 "Profile, vitals, photos and lab results are gathered.",
                 "Choose the report language.",
                 "Download or print it and take it with you."]),
        ])
        more_t = "AND MORE"
        more = [("breath", "Vitals & breathing", "Camera or by hand"), ("photo", "Photo check", "Eyes, skin, gums"),
                ("labs", "Lab results", "PDF or photo"), ("diary", "Symptom diary", "Over time"), ("vets", "Find a vet", "Nearby & emergency")]
        foot = "PetAiNurse does not provide veterinary diagnosis and does not replace your vet."
    more_html = (f'<div class="pn-sec">{more_t}</div><div class="pn-l-more">' +
                 "".join(f'<div class="c"><div class="im">{_art.scene(k, "dog")}</div><div class="t">{t}<small>{sm}</small></div></div>' for k, t, sm in more) + '</div>')
    return {"hero": hero, "services": services, "more": more_html, "foot": foot}
