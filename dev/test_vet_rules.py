"""Plain-python tests for vet_rules.py (no pytest needed):  python3 dev/test_vet_rules.py"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import vet_rules as vr

# (species_key, owner text, profile weight kg, expected MINIMUM floor or None for "no floor")
CASES = [
    # --- the 16 benchmark cases (English)
    ("dog", "ate a whole bar of dark chocolate, he's 5kg", None, "EMERGENCY"),
    ("cat", "chewed on a lily leaf", None, "EMERGENCY"),
    ("dog", "ate sugar-free gum, it has xylitol", None, "EMERGENCY"),
    ("cat", "my male cat keeps going to the litter box but nothing comes out, crying", None, "EMERGENCY"),
    ("dog", "belly is swollen and he keeps retching but nothing comes up", None, "EMERGENCY"),
    ("dog", "threw up once this morning, otherwise playful and eating", None, None),
    ("cat", "sneezing a bit for two days, eating normally", None, None),
    ("dog", "limping slightly on back leg since yesterday", None, None),
    ("cat", "hasn't eaten for 2 days", None, None),
    ("dog", "ate a few grapes an hour ago", None, "EMERGENCY"),
    ("dog", "had a seizure that lasted 5 minutes", None, "EMERGENCY"),
    ("dog", "licking paw a lot, red between toes", None, None),
    ("cat", "she is very lethargic and her gums look pale", None, "EMERGENCY"),
    ("dog", "licked a crumb of chocolate cake off the floor, she's 30 kg", None, None),
    ("cat", "he peed outside the box twice and is drinking much more water than usual", None, None),
    ("dog", "my pup got into the pantry and ate a bunch of raisin bread", None, "EMERGENCY"),
    # --- the 7 unseen phrasings that broke the first keyword engine
    ("dog", "he got into the Halloween candy, mostly Hershey's dark squares, around 12 of them, he's 4 kilos", None, "EMERGENCY"),
    ("cat", "she nibbled the petals of the Easter bouquet, the white flowers with orange centers", None, "URGENT"),
    ("dog", "stomach looks like a balloon and he is pacing and drooling, trying to throw up", None, "EMERGENCY"),
    ("cat", "he keeps squatting in the box and only a drop or two, hiding under the bed", None, "EMERGENCY"),
    ("dog", "my dog is shaking and drooling and fell over, legs paddling", None, "EMERGENCY"),
    ("cat", "ate half a leaf of the plant, I think it was a peace lily", None, None),
    ("dog", "ate one grape-flavored chew tablet", None, None),
    # --- Greek
    ("dog", "έφαγε μια ολόκληρη πλάκα μαύρη σοκολάτα", 5, "EMERGENCY"),
    ("cat", "μάσησε φύλλα από κρίνο", None, "EMERGENCY"),
    ("cat", "δεν βγάζει καθόλου ούρα, πηγαίνει συνέχεια στην άμμο", None, "EMERGENCY"),
    ("dog", "φουσκωμένη σκληρή κοιλιά και ξερομάει χωρίς να βγαίνει τίποτα", None, "EMERGENCY"),
    ("rabbit", "δεν τρώει από χθες και έχει φουσκωμένη κοιλιά", None, "EMERGENCY"),
    ("bird", "κάθεται στο πάτωμα του κλουβιού, φουσκωμένη κοιλιά, ψάχνει να γεννήσει αυγό", None, "EMERGENCY"),
    ("dog", "έφαγε σταφίδες", None, "EMERGENCY"),
    ("dog", "έκανε εμετό μία φορά, είναι ζωηρός και τρώει κανονικά", None, None),
    ("cat", "πήρε αντιψυκτικό από το γκαράζ", None, "EMERGENCY"),
    # --- rabbits, birds, reptiles
    ("rabbit", "he stopped eating this morning and has no droppings", None, "URGENT"),
    ("rabbit", "she stopped eating and her belly is bloated and she feels cold", None, "EMERGENCY"),
    ("rabbit", "8 week old baby rabbit with watery diarrhea", None, "EMERGENCY"),
    ("rabbit", "he is eating hay and playing", None, None),
    ("bird", "my budgie is sitting on the cage floor, fluffed up, straining, I think she is trying to lay an egg", None, "EMERGENCY"),
    ("bird", "my cockatiel's tail is bobbing with every breath", None, "EMERGENCY"),
    ("bird", "my parrot is chirping and eating seeds", None, None),
    ("reptile", "my bearded dragon breathes with its mouth open and has bubbles at the nose", None, "URGENT"),
    ("reptile", "tissue is sticking out of her vent", None, "EMERGENCY"),
    ("reptile", "my gecko is basking and not eating for two days", None, None),
    # --- dose awareness
    ("dog", "ate 20 g of milk chocolate", 30, None),
    ("dog", "ate 100 g of dark chocolate", 10, "EMERGENCY"),
    ("dog", "ate 100 g of dark chocolate", 20, "URGENT"),   # 27.5 mg/kg
    ("dog", "ate 60 g of dark chocolate", 20, None),        # 16.5 mg/kg, below the ~20 mg/kg mild-signs level
    ("dog", "ate some chocolate", None, "URGENT"),
    # --- regression: gaps found by a blind phrasing check
    ("dog", "I think my lab ate a pack of Lindt dark bars while we were out, she's 25kg", None, "URGENT"),  # amount unknown: ~22 mg/kg assumed -> call a vet today
    ("cat", "kitty has been to the litter tray ten times in an hour and just cries, nothing is coming out", None, "EMERGENCY"),
    ("rabbit", "my bunny hasn't pooped in a day and is sitting hunched and grinding her teeth", None, "EMERGENCY"),
    ("dog", "pup is convulsing and it has been going for ten minutes", None, "EMERGENCY"),
    ("dog", "my dog stole two Nurofen from the table", None, "URGENT"),
    ("dog", "he licked the plate after my chocolate cake, he's 30kg", None, None),
    # --- other toxins and emergencies
    ("cat", "she swallowed half a paracetamol tablet", None, "EMERGENCY"),
    ("dog", "he ate two ibuprofen tablets", None, "URGENT"),
    ("dog", "he ate rat poison pellets yesterday", None, "URGENT"),
    ("dog", "he ate rat poison and now has blood in his stool", None, "EMERGENCY"),
    ("dog", "she was hit by a car but is walking around", None, "EMERGENCY"),
    ("dog", "left in the car in summer, panting hard, heatstroke", None, "EMERGENCY"),
    ("dog", "he had a short seizure about 20 minutes ago, lasted 30 seconds", None, "URGENT"),
    ("cat", "my cat is breathing with her mouth open", None, "EMERGENCY"),
    ("dog", "the state of the garden is messy, we create a lot of waste", None, None),   # substring traps
]

fails = 0
print(f"{'expect':10}{'got':10} rules fired / text")
for sp, text, w, exp in CASES:
    res = vr.evaluate(sp, [text], {"weight": w} if w else {})
    got = res.level or None
    ok = (got == exp) if exp in (None, "URGENT") else vr.RANK.get(got or "SELF_CARE", 0) >= vr.RANK[exp]
    if not ok:
        fails += 1
    print(f"{str(exp):10}{str(got):10} {'OK ' if ok else 'FAIL'} {[h.id for h in res.hits]}  {text[:60]}")

# invariants
r = vr.evaluate("dog", ["he ate xylitol"], {})
assert vr.outranks(r.level, "URGENT") and not vr.outranks(r.level, "EMERGENCY")
assert not vr.outranks("", "SELF_CARE") and not vr.outranks("URGENT", "EMERGENCY")     # floor never lowers
assert vr.prompt_hints(vr.Result()) == ""
assert "DOG-XYLITOL" in vr.prompt_hints(r) and vr.floor_note(r, "el").startswith("⚠️ Κανόνας")
# every rule has both languages and msd rules have a source
for rule in vr.RULES:
    assert rule.en and rule.el, rule.id
    assert rule.level in ("URGENT", "EMERGENCY"), rule.id
    assert rule.basis == "policy" or rule.source.startswith("http"), rule.id
print(f"\n{len(CASES)} cases, {fails} failures, {len(vr.RULES)} rules + chocolate calculator")
sys.exit(1 if fails else 0)
