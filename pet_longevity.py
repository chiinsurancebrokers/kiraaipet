"""
pet_longevity.py — "Longevity check" for pets (pure functions, no UI).

Wellness estimate for dogs, cats and rabbits from what an owner can observe or
measure at home: body condition, teeth, activity, preventive care, resting
breathing rate while asleep (camera or tap count) and resting pulse (tap count).
It is NOT a diagnosis. Anything abnormal is routed to a vet.

Methods and sources
-------------------
Dog age in human years  Epigenetic clock: human_age = 16 * ln(dog_age) + 31
                        (Wang T et al., Cell Systems 2020, Labrador cohort). Valid
                        from about 1 year; younger dogs use a linear ramp.
Cat age in human years  Standard feline life-stage table (AAFP / AAHA 2021):
                        1 y = 15, 2 y = 24, then +4 per year.
Rabbit                  Approximate: 1 y = 18, then +5 per year (indicative only).
Typical lifespan        Ranges by size band, not individual predictions:
                        dogs from VetCompass (O'Neill 2013, Teng 2018) and
                        Kraus 2013; cats ~12-16 y (indoor-only at the top end);
                        rabbits ~8-10 y typical for pets.
Body condition          9-point WSAVA / Purina scale; ideal 4-5. In the Purina
                        lifetime Labrador study, lean-fed dogs lived a median of
                        ~1.8 years longer than their heavier littermates (Kealy
                        2002, JAVMA).
Resting breathing rate  Sleeping respiratory rate (SRR). Persistently >30 breaths
                        per minute at rest in dogs and cats is the standard
                        home-monitoring threshold for cardiac disease; >40 is
                        a same-day vet call (ACVIM consensus, Rishniw/Ljungvall
                        et al.; Tufts/Cornell owner guidance).
Resting heart rate      Species/size reference ranges (Merck Vet Manual).
                        Tap-count estimates are rough (about +/-10 %).

TODO before marketing claims: validate the camera breathing counter against
manual counts on 20+ real sleeping dogs/cats.
"""
from __future__ import annotations

import math

LEVELS = [
    ("severe", "Χρειάζεται έλεγχος", "Needs a check", "#DC2626"),
    ("limit", "Προσοχή", "Watch", "#F59E0B"),
    ("neutral", "Μέτριο", "Fair", "#3B6BFF"),
    ("good", "Καλό", "Good", "#14B8A6"),
    ("excellent", "Εξαιρετικό", "Excellent", "#059669"),
]
_LV = {k: i for i, (k, *_r) in enumerate(LEVELS)}


def level(key, lang="el"):
    k, el, en, col = LEVELS[_LV[key]]
    return {"key": k, "label": el if lang == "el" else en, "color": col, "score": _LV[key]}


SUPPORTED = ("dog", "cat", "rabbit")


# ── age ──────────────────────────────────────────────────────────────────────
def age_years(age_y, age_m):
    return float(age_y or 0) + float(age_m or 0) / 12.0


def human_age(species, years):
    """Human-equivalent age. Returns None when there is no sound conversion."""
    y = max(0.0, float(years))
    if species == "dog":
        if y < 1.0:
            return round(15 * y) if y > 0 else 0
        return round(16 * math.log(y) + 31)
    if species == "cat":
        if y < 1.0:
            return round(15 * y)
        if y < 2.0:
            return round(15 + 9 * (y - 1))
        return round(24 + 4 * (y - 2))
    if species == "rabbit":
        if y < 1.0:
            return round(18 * y)
        return round(18 + 5 * (y - 1))
    return None


def size_band(species, weight_kg):
    w = float(weight_kg or 0)
    if species == "dog":
        if w <= 0:
            return "medium"
        if w < 10:
            return "small"
        if w < 25:
            return "medium"
        if w < 45:
            return "large"
        return "giant"
    return "all"


# (low, high) typical lifespan in years
LIFESPAN = {
    ("dog", "small"): (13, 16),
    ("dog", "medium"): (11, 14),
    ("dog", "large"): (10, 12),
    ("dog", "giant"): (7, 10),
    ("cat", "all"): (12, 16),
    ("rabbit", "all"): (8, 10),
}


def lifespan(species, weight_kg, indoor=True):
    lo, hi = LIFESPAN.get((species, size_band(species, weight_kg)), (10, 14))
    if species == "cat" and not indoor:
        lo, hi = 9, 13
    return lo, hi


def life_stage(species, years, weight_kg=None, lang="el"):
    el = lang == "el"
    lo, hi = lifespan(species, weight_kg)
    frac = years / ((lo + hi) / 2.0)
    if years < 1:
        return ("Νεαρό" if el else "Young"), "young"
    if frac < 0.4:
        return ("Ενήλικο" if el else "Adult"), "adult"
    if frac < 0.7:
        return ("Μεσήλικο" if el else "Mature"), "mature"
    if frac < 0.9:
        return ("Ηλικιωμένο" if el else "Senior"), "senior"
    return ("Γηριατρικό" if el else "Geriatric"), "geriatric"


# ── pillar levels ─────────────────────────────────────────────────────────────
# Owner-friendly body condition: three questions map to a 9-point score estimate.
def bcs_from_answers(ribs, waist):
    """ribs: 'easy' | 'ok' | 'hard' | 'none' ; waist: 'marked' | 'slight' | 'none' | 'bulge'."""
    base = {"easy": 3, "ok": 5, "hard": 7, "none": 9}.get(ribs, 5)
    adj = {"marked": -0.5, "slight": 0, "none": 0.5, "bulge": 1}.get(waist, 0)
    return max(1, min(9, round(base + adj)))


def bcs_level(bcs):
    if bcs in (4, 5):
        return "excellent"
    if bcs in (3, 6):
        return "good"
    if bcs in (2, 7):
        return "limit"
    return "severe"


def dental_level(answer):
    return {"clean": "excellent", "mild": "good", "tartar": "limit", "bad": "severe"}.get(answer, "neutral")


def activity_level(species, active_min_per_day):
    m = float(active_min_per_day or 0)
    # dogs need more structured activity than cats/rabbits
    cut = (60, 40, 25, 12) if species == "dog" else (40, 25, 15, 8)
    if m >= cut[0]:
        return "excellent"
    if m >= cut[1]:
        return "good"
    if m >= cut[2]:
        return "neutral"
    if m >= cut[3]:
        return "limit"
    return "severe"


def prevention_level(vaccines_ok, parasites_ok, checkup_12m):
    n = int(bool(vaccines_ok)) + int(bool(parasites_ok)) + int(bool(checkup_12m))
    return ["severe", "limit", "good", "excellent"][n]


def srr_level(bpm):
    b = float(bpm)
    if b < 25:
        return "excellent"
    if b < 30:
        return "good"
    if b < 35:
        return "neutral"
    if b < 40:
        return "limit"
    return "severe"


# resting heart rate reference (low, high) bpm by species / size
def hr_reference(species, weight_kg):
    if species == "dog":
        w = float(weight_kg or 15)
        if w < 10:
            return (90, 140)
        if w < 25:
            return (80, 120)
        return (60, 110)
    if species == "cat":
        return (140, 220)
    if species == "rabbit":
        return (130, 325)
    return (60, 140)


def hr_level(species, bpm, weight_kg):
    lo, hi = hr_reference(species, weight_kg)
    b = float(bpm)
    if lo <= b <= hi:
        mid_span = (hi - lo) * 0.25
        return "excellent" if (lo + mid_span) <= b <= (hi - mid_span) else "good"
    if lo * 0.85 <= b <= hi * 1.15:
        return "limit"
    return "severe"


# ── main analysis ─────────────────────────────────────────────────────────────
def analyse(pet, q, breath=None, pulse=None, lang="el"):
    """pet: {species_key, name, weight, age_y, age_m, sex...}; q: questionnaire dict;
    breath: result of the breathing scan (or None); pulse: tap-heart-rate result (or None)."""
    el = lang == "el"
    sp = pet.get("species_key", "dog")
    years = age_years(pet.get("age_y"), pet.get("age_m"))
    try:
        weight = float(pet.get("weight") or 0)
    except (TypeError, ValueError):
        weight = 0.0
    res = {"species": sp, "name": pet.get("name", ""), "years": round(years, 1),
           "pillars": [], "notes": [], "plan": [], "alerts": []}

    ha = human_age(sp, years)
    res["human_age"] = ha
    lo, hi = lifespan(sp, weight, indoor=bool(q.get("indoor", True)))
    res["lifespan"] = (lo, hi)
    res["life_pct"] = max(0, min(100, round(100 * years / ((lo + hi) / 2.0))))
    res["stage"], res["stage_key"] = life_stage(sp, years, weight, lang)

    # pillars ---------------------------------------------------------------
    def add(pid, name_el, name_en, value, lv):
        res["pillars"].append({"id": pid, "name": name_el if el else name_en, "value": value, **level(lv, lang)})

    bcs = bcs_from_answers(q.get("ribs", "ok"), q.get("waist", "slight"))
    res["bcs"] = bcs
    add("bcs", "Σωματική κατάσταση (βάρος)", "Body condition", f"{bcs}/9", bcs_level(bcs))

    add("dental", "Στόμα & δόντια", "Mouth & teeth", "", dental_level(q.get("dental", "mild")))
    mins = q.get("active_min", 30)
    add("activity", "Δραστηριότητα", "Activity", f"{int(mins)} min/{'ημέρα' if el else 'day'}", activity_level(sp, mins))
    add("prevention", "Πρόληψη (εμβόλια, παράσιτα, check-up)", "Prevention (vaccines, parasites, check-up)", "",
        prevention_level(q.get("vaccines_ok"), q.get("parasites_ok"), q.get("checkup_12m")))

    srr = (breath or {}).get("bpm")
    if srr:
        lv = srr_level(srr)
        res["srr"] = srr
        add("srr", "Αναπνοή στον ύπνο/ηρεμία", "Resting breathing", f"{srr} /min", lv)
        if lv == "severe":
            res["alerts"].append(
                "🚨 Αναπνοές ≥40 το λεπτό σε ηρεμία: κάλεσε τον κτηνίατρο ΣΗΜΕΡΑ (πιθανή καρδιακή ή πνευμονική αιτία). Αν υπάρχει δύσπνοια, ανοιχτό στόμα ή μώβιες/γκρίζες ούλες, πήγαινε αμέσως σε επείγοντα."
                if el else
                "🚨 Breathing at 40 or more per minute at rest: call your vet TODAY (possible heart or lung cause). If there is laboured breathing, open-mouth breathing or blue/grey gums, go to an emergency clinic now.")
        elif lv == "limit":
            res["alerts"].append(
                "⚠️ Αναπνοές 35–39 το λεπτό σε ηρεμία: μέτρα ξανά αύριο στον ύπνο. Αν μένει >30, κλείσε ραντεβού με τον κτηνίατρο."
                if el else
                "⚠️ Resting breathing 35-39 per minute: count again tomorrow while asleep. If it stays above 30, book a vet visit.")

    hr = (pulse or {}).get("bpm")
    if hr:
        add("hr", "Σφυγμοί ηρεμίας", "Resting pulse", f"~{hr} bpm", hr_level(sp, hr, weight))

    scores = [p["score"] for p in res["pillars"]]
    res["score"] = round(100 * (sum(scores) / len(scores)) / 4.0) if scores else 0

    # notes & plan ------------------------------------------------------------
    if sp not in SUPPORTED:
        res["notes"].append("Ο έλεγχος μακροζωίας είναι σχεδιασμένος για σκύλους, γάτες και κουνέλια." if el
                            else "The longevity check is designed for dogs, cats and rabbits.")
    if bcs >= 7:
        res["plan"].append("⚖️ " + ("Πιο αδύνατο = πιο μακρύ: στη μελέτη Purina οι αδύνατοι Λαμπραντόρ έζησαν ~1,8 χρόνια περισσότερο. Στόχος βάρους με τον κτηνίατρο και μετρημένη δόση τροφής."
                                   if el else "Leaner lives longer: in the Purina study lean Labradors lived ~1.8 years more. Set a target weight with your vet and measure each meal."))
    elif bcs <= 3:
        res["plan"].append("⚖️ " + ("Το βάρος είναι χαμηλό: έλεγχος από κτηνίατρο για παράσιτα, δόντια, θυρεοειδή/νεφρούς πριν αυξήσεις την τροφή."
                                   if el else "Weight is low: ask your vet to check for parasites, teeth, thyroid and kidneys before simply feeding more."))
    if q.get("dental") in ("tartar", "bad"):
        res["plan"].append("🦷 " + ("Η στοματική νόσος συνδέεται με καρδιά και νεφρά: καθαρισμός από κτηνίατρο και καθημερινό βούρτσισμα."
                                   if el else "Dental disease is linked to heart and kidney problems: a vet dental clean and daily brushing."))
    if activity_level(sp, mins) in ("severe", "limit", "neutral"):
        res["plan"].append("🚶 " + (("Στόχος 40–60 λεπτά δραστηριότητας την ημέρα, σε 2 βόλτες + παιχνίδι.") if sp == "dog" else
                                   ("Στόχος 25–40 λεπτά παιχνιδιού την ημέρα, σε μικρές συνεδρίες.")) if el else
                           ("🚶 Aim for 40-60 minutes of activity a day: two walks plus play." if sp == "dog"
                            else "🚶 Aim for 25-40 minutes of play a day in short sessions."))
    if not (q.get("vaccines_ok") and q.get("parasites_ok") and q.get("checkup_12m")):
        res["plan"].append("💉 " + ("Συμπλήρωσε εμβόλια, αντιπαρασιτική αγωγή και ετήσιο check-up (στα γηρατειά ανά 6 μήνες)."
                                   if el else "Catch up on vaccines, parasite prevention and a yearly check-up (every 6 months for seniors)."))
    if res["stage_key"] in ("senior", "geriatric"):
        res["plan"].append("🩺 " + ("Ηλικιωμένο κατοικίδιο: check-up ανά 6 μήνες με εξετάσεις αίματος και πίεση."
                                   if el else "Senior pet: a check-up every 6 months with blood tests and blood pressure."))
    if not srr:
        res["plan"].append("🫁 " + ("Μέτρησε αναπνοές στον ύπνο: είναι ο πιο χρήσιμος δείκτης καρδιάς στο σπίτι."
                                   if el else "Count sleeping breaths: the single most useful heart check you can do at home."))
    res["plan"].append("📅 " + ("Επανάλαβε τον έλεγχο κάθε 3 μήνες για να δεις τάση." if el else "Repeat the check every 3 months to see the trend."))
    return res
