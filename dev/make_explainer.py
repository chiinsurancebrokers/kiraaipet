"""Builds the landing explainer videos (static/video/explainer_{en,el}.mp4 + poster_*.jpg).
Scenes are HTML rendered with Playwright, joined with ffmpeg cross-fades.  Run:  python3 dev/make_explainer.py
Needs: playwright + chromium, ffmpeg, Inter font.  Heroes come from static/heroes/*.png."""
import base64, os, subprocess, sys, tempfile
from playwright.sync_api import sync_playwright

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "static", "video")
FADE = 0.5


def hero(k):
    return "data:image/png;base64," + base64.b64encode(open(os.path.join(ROOT, "static", "heroes", k + ".png"), "rb").read()).decode()


H = {k: hero(k) for k in ("dog", "cat", "rabbit", "bird")}
# where the face sits in each hero picture (x%, y%), so the circle crops in on it
FACE = {"dog": (36, 30), "cat": (50, 30), "rabbit": (48, 32), "bird": (46, 36)}


def face(k, size, zoom=1.75):
    x, y = FACE[k]
    return (f"<div style='width:{size}px;height:{size}px;border-radius:50%;overflow:hidden;flex:none;background:#E7EAFB;position:relative'>"
            f"<img src='{H[k]}' style='position:absolute;width:{size*zoom:.0f}px;height:{size*zoom:.0f}px;left:{size/2 - size*zoom*x/100:.0f}px;top:{size/2 - size*zoom*y/100:.0f}px'></div>")

CSS = """
*{box-sizing:border-box;margin:0;padding:0}
body{width:1280px;height:720px;font-family:'Inter',sans-serif;overflow:hidden;position:relative;color:#0B1B4B}
.dark{background:radial-gradient(circle at 50% 30%,#2F49E0 0%,#1237C9 55%,#0E2AA0 100%);color:#fff}
.light{background:#F3F4FE}
.brand{position:absolute;left:48px;top:36px;font-weight:800;font-size:24px;display:flex;align-items:center;gap:10px}
.brand i{width:30px;height:30px;border-radius:9px;background:#F26B3A;display:inline-block}
.num{width:56px;height:56px;border-radius:50%;background:#F26B3A;color:#fff;font-weight:800;font-size:28px;display:flex;align-items:center;justify-content:center;margin-bottom:22px}
.left{position:absolute;left:90px;top:200px;width:480px}
.left h2{font-size:56px;line-height:1.05;font-weight:800;letter-spacing:-.03em}
.left p{font-size:24px;line-height:1.4;color:#5B6794;margin-top:18px}
.card{position:absolute;right:80px;top:96px;width:560px;height:540px;background:#fff;border-radius:34px;box-shadow:0 36px 70px -30px rgba(18,55,201,.45);padding:34px}
.card h4{font-size:15px;letter-spacing:.12em;color:#1237C9;font-weight:800;margin-bottom:20px}
.tiles{display:flex;gap:16px;margin-bottom:22px}
.tile{flex:1;height:170px;border-radius:24px;border:2px solid #E1E5F8;background:#fff;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:6px;font-weight:700;font-size:18px;color:#5B6794}
.tile img{width:118px;height:118px;object-fit:contain}
.tile.sel{border-color:#1237C9;background:#E7EAFB;color:#0B1B4B;box-shadow:0 0 0 4px rgba(18,55,201,.12)}
.field{display:flex;justify-content:space-between;align-items:center;border:2px solid #E1E5F8;border-radius:18px;padding:12px 20px;margin-bottom:10px;font-size:20px}
.field small{font-size:13px;letter-spacing:.1em;color:#8A93B8;font-weight:700;text-transform:uppercase}
.field b{font-size:24px}
.chips{display:flex;gap:10px;flex-wrap:wrap;margin-bottom:22px}
.chip{border:2px solid #E1E5F8;border-radius:999px;padding:10px 20px;font-weight:700;font-size:19px}
.chip.on{border-color:#F26B3A;color:#F26B3A;background:#FFF3EE}
.msg{max-width:78%;border-radius:22px;padding:16px 22px;font-size:22px;line-height:1.3;margin-bottom:14px;font-weight:500}
.msg.me{background:#1237C9;color:#fff;margin-left:auto;border-bottom-right-radius:6px}
.msg.ai{background:#E7EAFB;border-bottom-left-radius:6px}
.row{display:flex;align-items:flex-end;gap:12px}
.av{width:84px;height:84px;border-radius:50%;background:#E7EAFB;border:3px solid #fff;box-shadow:0 8px 20px -8px rgba(18,55,201,.5);overflow:hidden;flex:none;display:flex;align-items:center;justify-content:center}
.av img{width:118%;height:118%;object-fit:cover;object-position:50% 28%}
.bar{height:14px;border-radius:7px;background:#D5DAF7;margin:12px 0}
.sec{font-size:15px;letter-spacing:.12em;color:#1237C9;font-weight:800;margin-top:26px}
.cen{position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center}
.cen h1{font-size:92px;font-weight:800;letter-spacing:-.035em;line-height:1.02}
.cen h3{font-size:40px;font-weight:700;color:#FFC9B0;margin-top:14px}
.team{display:flex;gap:26px;margin-top:46px}
.team .t{width:220px;height:220px;border-radius:50%;background:#fff;display:flex;align-items:center;justify-content:center;box-shadow:0 26px 50px -22px rgba(0,0,0,.55)}
.team .t>div{border:0}
.btn{margin-top:26px;background:#F26B3A;color:#fff;border-radius:999px;padding:20px 54px;font-size:32px;font-weight:800;box-shadow:0 20px 40px -18px #F26B3A}
.note{position:absolute;bottom:34px;left:0;right:0;text-align:center;font-size:19px;color:#C9D2FF}
"""

T = {
 "en": {
  "meet": "Meet PetsAIHealth", "sub": "Your AI vet nurse",
  "s1": ("Add your pet", "Name, species, age and weight. It takes about a minute."),
  "pet": "Pet profile", "dog": "Dog", "cat": "Cat", "rabbit": "Rabbit", "name": "Name", "age": "Age", "w": "Weight", "bobby": "Bobby", "ageV": "6 years", "wV": "29 kg",
  "s2": ("Tell us what you notice", "Type it, say it with your voice, or tap a quick pick."),
  "q": "What did you notice?", "chips": ["Not eating", "Vomiting", "Limping", "Coughing"], "m1": "Bobby hasn't eaten since yesterday.",
  "s3": ("One question at a time", "The nurse asks, explains, and keeps the emergency check always on."),
  "nurse": "AI vet nurse", "a1": "How long has Bobby not eaten?", "u1": "About 24 hours.", "a2": "Any vomiting or diarrhoea?",
  "s4": ("Get your vet report", "A clear summary with MSD Vet Manual references to take to the clinic."),
  "rep": "Report for the vet", "mc": "Main complaint", "as": "Assessment", "pl": "Plan",
  "ready": "Ready to ask?", "free": "Create your pet's profile and do the first check for free.", "cta": "Try it free",
  "foot": "Not a diagnosis. PetsAIHealth complements your vet, never replaces them."},
 "el": {
  "meet": "Γνώρισε την PetsAIHealth", "sub": "Η AI νοσηλεύτριά σου για το κατοικίδιο",
  "s1": ("Πρόσθεσε το ζωάκι σου", "Όνομα, είδος, ηλικία και βάρος. Παίρνει περίπου ένα λεπτό."),
  "pet": "Προφίλ ζώου", "dog": "Σκύλος", "cat": "Γάτα", "rabbit": "Κουνέλι", "name": "Όνομα", "age": "Ηλικία", "w": "Βάρος", "bobby": "Μπόμπι", "ageV": "6 ετών", "wV": "29 κιλά",
  "s2": ("Πες μας τι παρατηρείς", "Γράψε το, πες το με τη φωνή σου ή διάλεξε μια γρήγορη επιλογή."),
  "q": "Τι παρατήρησες;", "chips": ["Δεν τρώει", "Εμετός", "Κουτσαίνει", "Βήχας"], "m1": "Ο Μπόμπι δεν έχει φάει από χθες.",
  "s3": ("Μία ερώτηση τη φορά", "Η νοσηλεύτρια ρωτά, εξηγεί και κρατά τον έλεγχο επείγοντος πάντα ενεργό."),
  "nurse": "AI νοσηλεύτρια", "a1": "Πόση ώρα δεν έχει φάει ο Μπόμπι;", "u1": "Περίπου 24 ώρες.", "a2": "Έκανε εμετό ή διάρροια;",
  "s4": ("Πάρε την αναφορά για τον κτηνίατρο", "Καθαρή περίληψη με παραπομπές στο MSD Vet Manual για να την πας στο ιατρείο."),
  "rep": "Αναφορά για τον κτηνίατρο", "mc": "Κύριο πρόβλημα", "as": "Εκτίμηση", "pl": "Πλάνο",
  "ready": "Έτοιμος να ρωτήσεις;", "free": "Φτιάξε το προφίλ του ζώου σου και κάνε τον πρώτο έλεγχο δωρεάν.", "cta": "Δοκίμασε δωρεάν",
  "foot": "Δεν είναι διάγνωση. Η PetsAIHealth συμπληρώνει τον κτηνίατρό σου, δεν τον αντικαθιστά."},
}


def up(x):
    import unicodedata
    return ''.join(c for c in unicodedata.normalize('NFD', x) if unicodedata.category(c) != 'Mn').upper()


def page(body, dark=False):
    return f"<html><head><meta charset='utf-8'><style>{CSS}</style></head><body class='{'dark' if dark else 'light'}'>{body}</body></html>"


def brand():
    return "<div class='brand'><i></i>PetsAIHealth</div>"


def left(n, tt):
    return f"<div class='left'><div class='num'>{n}</div><h2>{tt[0]}</h2><p>{tt[1]}</p></div>"


def scenes(lg):
    t = T[lg]
    S = []
    team = "".join(f"<div class='t'>{face(k, 206, 1.9)}</div>" for k in ("dog", "cat", "rabbit", "bird"))
    S.append((page(f"<div class='cen'><h1>{t['meet']}</h1><h3>{t['sub']}</h3><div class='team'>{team}</div></div>", True), 4.5))
    tiles = "".join(f"<div class='tile{' sel' if k=='dog' else ''}'>{face(k, 104, 1.8)}{t[k]}</div>" for k in ("dog", "cat", "rabbit"))
    fields = f"<div class='field'><small>{up(t['name'])}</small><b>{t['bobby']}</b></div><div class='field'><small>{up(t['age'])}</small><b>{t['ageV']}</b></div><div class='field'><small>{up(t['w'])}</small><b>{t['wV']}</b></div>"
    S.append((page(brand() + left(1, t['s1']) + f"<div class='card'><h4>{up(t['pet'])}</h4><div class='tiles'>{tiles}</div>{fields}</div>"), 5.5))
    chips = "".join(f"<div class='chip{' on' if i==0 else ''}'>{c}</div>" for i, c in enumerate(t['chips']))
    S.append((page(brand() + left(2, t['s2']) + f"<div class='card'><h4>{up(t['q'])}</h4><div class='chips'>{chips}</div><div class='msg me'>{t['m1']}</div></div>"), 5.0))
    av = face("dog", 92, 1.8)
    def chat(n):
        m = f"<div class='row'>{av}<div class='msg ai'>{t['a1']}</div></div>"
        if n > 1: m += f"<div class='msg me'>{t['u1']}</div>"
        if n > 2: m += f"<div class='row'>{av}<div class='msg ai'>{t['a2']}</div></div>"
        return page(brand() + left(3, t['s3']) + f"<div class='card'><h4>{up(t['nurse'])}</h4>{m}</div>")
    S += [(chat(1), 3.0), (chat(2), 2.5), (chat(3), 3.5)]
    rep = (f"<h4>{up(t['rep'])}</h4><div class='sec' style='margin-top:6px'>{up(t['mc'])}</div><div class='bar' style='width:92%'></div><div class='bar' style='width:70%'></div>"
           f"<div class='sec'>{up(t['as'])}</div><div class='bar' style='width:96%'></div><div class='bar' style='width:84%'></div><div class='bar' style='width:60%'></div>"
           f"<div class='sec'>{up(t['pl'])}</div><div class='bar' style='width:88%'></div><div class='bar' style='width:52%'></div>")
    S.append((page(brand() + left(4, t['s4']) + f"<div class='card'>{rep}</div>"), 5.0))
    team2 = "".join(f"<div class='t' style='width:176px;height:176px'>{face(k, 164, 1.9)}</div>" for k in ("dog", "cat", "rabbit", "bird"))
    S.append((page(f"<div class='cen'><div class='team' style='margin:0 0 30px'>{team2}</div><h1 style='font-size:84px'>{t['ready']}</h1><h3 style='font-size:30px;font-weight:500;color:#DCE3FF'>{t['free']}</h3><div class='btn'>{t['cta']}</div></div><div class='note'>{t['foot']}</div>", True), 5.0))
    return S


def build(pw, lg):
    tmp = tempfile.mkdtemp()
    b = pw.chromium.launch()
    pg = b.new_page(viewport={"width": 1280, "height": 720})
    files = []
    S = scenes(lg)
    for i, (html, d) in enumerate(S):
        pg.set_content(html); pg.wait_for_timeout(250)
        f = os.path.join(tmp, f"s{i}.png"); pg.screenshot(path=f); files.append((f, d))
    b.close()
    # poster = intro scene
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", files[0][0], "-q:v", "3", os.path.join(OUT, f"poster_{lg}.jpg")], check=True)
    inputs, filt, off, last = [], [], 0.0, None
    for i, (f, d) in enumerate(files):
        inputs += ["-loop", "1", "-t", str(d + FADE), "-i", f]
    prev = "0:v"
    for i in range(1, len(files)):
        off += files[i - 1][1]
        filt.append(f"[{prev}][{i}:v]xfade=transition=fade:duration={FADE}:offset={off:.2f}[x{i}]"); prev = f"x{i}"
    total = off + files[-1][1]
    filt.append(f"[{prev}]fps=25,format=yuv420p,drawbox=x=0:y=ih-6:w='iw*t/{total:.2f}':h=6:color=0xF26B3A:t=fill[v]")
    out = os.path.join(OUT, f"explainer_{lg}.mp4")
    subprocess.run(["ffmpeg", "-v", "error", "-y", *inputs, "-filter_complex", ";".join(filt), "-map", "[v]", "-t", f"{total:.2f}",
                    "-c:v", "libx264", "-preset", "veryfast", "-crf", "23", "-movflags", "+faststart", out], check=True)
    return out, total


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    with sync_playwright() as pw:
        for lg in (sys.argv[1:] or ["en", "el"]):
            print(build(pw, lg))
