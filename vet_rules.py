"""Deterministic veterinary safety rules for PetsAIHealth.

These rules are a SAFETY FLOOR under the nurse chat, not a replacement for it:
they can only RAISE the urgency of a final triage verdict, never lower it.
The LLM still reads the owner's free text and decides; this module catches
well-known red flags (toxins, GDV, urinary blockage, egg binding ...) with
the same answer every time and a traceable rule id + source.

Matching is done on accent-stripped, lower-cased text (final sigma folded to
sigma), so Greek and English wording both work. Patterns below are therefore
written WITHOUT accents and with plain sigma.

Sources: pages of the MSD (Merck) Veterinary Manual, paraphrased, never quoted.
Rules with basis="policy" come from the app's existing nurse prompt and have
no MSD page attached yet: they need review by a veterinarian.

Levels use the app's own tags: EMERGENCY > URGENT > SELF_CARE.
"""
import re
import unicodedata
from dataclasses import dataclass, field

RANK = {"SELF_CARE": 0, "URGENT": 1, "EMERGENCY": 2}

MSD = "https://www.msdvetmanual.com/"
SRC = {
    "gdv": MSD + "digestive-system/diseases-of-the-stomach-and-intestines-in-small-animals/gastric-dilation-and-volvulus-in-small-animals",
    "chocolate": MSD + "toxicology/food-hazards/chocolate-toxicosis-in-animals",
    "xylitol": "https://www.merckvetmanual.com/toxicology/food-hazards/xylitol-toxicosis-in-dogs",
    "grape": MSD + "toxicology/food-hazards/grape-raisin-and-tamarind-vitis-spp-tamarindus-spp-toxicosis-in-dogs",
    "glycol": "https://www.merckvetmanual.com/toxicology/ethylene-glycol-toxicosis/ethylene-glycol-toxicosis-in-animals",
    "lily": MSD + "toxicology/poisonous-plants/houseplants-and-ornamentals-toxic-to-animals",
    "urethral": "https://www.merckvetmanual.com/urinary-system/urolithiasis-in-small-animals/urethral-obstruction-in-small-animals",
    "analgesics": MSD + "toxicology/toxicoses-from-human-analgesics/toxicoses-from-human-analgesics-in-animals",
    "rodenticide": MSD + "toxicology/rodenticide-poisoning/anticoagulant-rodenticide-poisoning-in-animals",
    "rabbit_gi": MSD + "all-other-pets/rabbits/digestive-disorders-of-rabbits",
    "bird_repro": MSD + "exotic-and-laboratory-animals/pet-birds/reproductive-diseases-of-pet-birds",
    "bird_owner": "https://www.merckvetmanual.com/bird-owners/disorders-and-diseases-of-birds/reproductive-disorders-of-pet-birds",
    "reptile": "https://www.merckvetmanual.com/all-other-pets/reptiles/disorders-and-diseases-of-reptiles",
    # pet-owner section pages
    "snake": MSD + "special-pet-topics/poisoning/snakebite",
    "metaldehyde": MSD + "special-pet-topics/poisoning/metaldehyde-poisoning",
    "insecticide": MSD + "special-pet-topics/poisoning/insecticide-poisoning",
    "food": MSD + "special-pet-topics/poisoning/food-hazards",
    "household": MSD + "special-pet-topics/poisoning/household-hazards",
    "otc": MSD + "special-pet-topics/poisoning/poisoning-from-human-over-the-counter-drugs",
    "rx": MSD + "special-pet-topics/poisoning/poisonings-from-human-prescription-drugs",
    "plants": MSD + "special-pet-topics/poisoning/plants-poisonous-to-animals",
    "salt": MSD + "special-pet-topics/poisoning/salt-poisoning",
    "emergency": MSD + "special-pet-topics/emergencies/what-to-do-in-a-dog-or-cat-emergency",
    "dog_gi": MSD + "dog-owners/digestive-disorders-of-dogs/disorders-of-the-stomach-and-intestines-in-dogs",
    "gp_common": MSD + "all-other-pets/guinea-pigs/common-health-problems-of-guinea-pigs",
    "gp_nutrition": MSD + "all-other-pets/guinea-pigs/nutritional-problems-of-guinea-pigs",
    "ferret_emerg": MSD + "all-other-pets/ferrets/emergencies-of-ferrets",
    "hamster": MSD + "all-other-pets/hamsters/disorders-and-diseases-of-hamsters",
    "cases": MSD + "pages-with-widgets/case-studies",
}


def norm(text):
    """Lower-case, strip diacritics, fold final sigma."""
    if not text:
        return ""
    s = unicodedata.normalize("NFD", text.lower())
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return s.replace("ς", "σ")


@dataclass
class Rule:
    id: str
    species: tuple          # () = every species
    level: str
    all_of: tuple           # every regex must match
    en: str
    el: str
    source: str = ""
    basis: str = "msd"      # "msd" or "policy"
    exclude: str = ""       # if this matches, the rule does not fire
    immediate: bool = False  # clear immediate danger: nurse may skip the question cycle
    neg_guard: bool = False  # exposure rule: ignore clauses where the owner says it did NOT happen ("didn't eat the grapes")


@dataclass
class Hit:
    id: str
    level: str
    en: str
    el: str
    source: str
    basis: str
    immediate: bool = False


@dataclass
class Result:
    level: str = ""
    hits: list = field(default_factory=list)


def _r(*patterns):
    return tuple(re.compile(p, re.S) for p in patterns)


# ---- shared fragments ------------------------------------------------------
_SEIZ = (r"seizur|convuls|paddl|thrash|epilep|\bfitting\b|"
         r"σπασμ|επιληπ|σπαρταρ")
_LONG = (r"(lasted|lasting|for|going|διαρκεσ\w*|εδω και|ηδη) .{0,10}(\b([5-9]|[1-9]\d)|five|six|seven|eight|nine|ten|fifteen|twenty|πεντε|εξι|εφτα|οκτω|εννια|δεκα|δεκαπεντε|εικοσι) ?(min|λεπτ)|half an hour|several minutes|more than (five|5)|still (seizing|having|fitting)|"
         r"won'?t stop|not stopping|cluster|repeat|again and again|one after another|second seizure|third seizure|"
         r"πολλα λεπτα|δεν σταματ|ξανα και ξανα|επαναλαμβαν|πολλαπλ|διαρκουν")
_GUMS_BAD = (r"(pale|white|blue|bluish|grey|gray|purple|cyan|muddy|brown)\w*.{0,15}gums?|"
             r"gums?.{0,25}(pale|white|blue|bluish|grey|gray|purple|cyan|muddy)|"
             r"(χλωμ|ασπρ|μπλε|γαλαζ|γκρι|μωβ)\w*.{0,15}ουλα|ουλα.{0,25}(χλωμ|ασπρ|μπλε|γαλαζ|γκρι|μωβ)")
_INGEST = (r"\b(ate|eaten|eats|eating|swallowed?|ingest\w*|chew\w*|nibbl\w*|licked|lapped|drank|drunk|stole|stolen|took|taken|gave|given)\b|got into|got hold of|"
           r"εφαγε|φαει|καταπι|μασησε|μασουλ|τσιμπ|γλειψ|ηπιε|εκλεψε|πηρε|εδωσα")

RULES = [
    # ---------------------------------------------------------------- dogs
    Rule("DOG-GDV", ("dog",), "EMERGENCY",
         _r(r"(swollen|bloat|distend|balloon|drum|hard|tight)\w*.{0,40}(belly|abdomen|stomach|tummy)|"
            r"(belly|abdomen|stomach|tummy).{0,40}(swollen|bloat|distend|balloon|drum|hard|tight)|"
            r"φουσκ|πρησ|σκληρ\w* κοιλι|κοιλι\w*.{0,30}(σκληρ|τεντωμ|φουσκ|πρησ)|στομαχ\w*.{0,30}(φουσκ|πρησ)",
            r"retch|unproductive|nothing (comes|came) (up|out)|trying to (throw up|vomit)|dry heav|drool|restless|pacing|"
            r"ξερομ|ξερατ|ξερασ|θελει να (κανει εμετο|ξερασει)|δεν βγαινει τιποτα|σιελορ|σαλια|ανησυχ|βηματιζ"),
         "Swollen belly with retching or restlessness can be gastric torsion (GDV): it needs treatment within hours.",
         "Φουσκωμένη κοιλιά με ξερατά ή ανησυχία μπορεί να είναι στροφή στομάχου: χρειάζεται θεραπεία μέσα σε ώρες.",
         SRC["gdv"], "msd", immediate=True),
    Rule("DOG-XYLITOL", ("dog",), "EMERGENCY",
         _r(r"xylitol|ξυλιτολ|(sugar|ζαχαρ\w*)[- ]?free (gum|candy|mint)|χωρις ζαχαρη.{0,25}(τσιχλ|καραμελ)|"
            r"τσιχλ\w* χωρις ζαχαρη"),
         "Xylitol can drop a dog's blood sugar within 30 minutes and later damage the liver.",
         "Η ξυλιτόλη μπορεί να ρίξει το σάκχαρο του σκύλου μέσα σε 30 λεπτά και αργότερα να βλάψει το συκώτι.",
         SRC["xylitol"], "msd", immediate=True),
    Rule("DOG-GRAPES", ("dog",), "EMERGENCY",
         _r(r"grape|raisin|sultana|currant|σταφυλ|σταφιδ|κορινθιακ"),
         "No safe amount of grapes or raisins is known for dogs: kidney failure can follow, and early treatment matters.",
         "Δεν υπάρχει γνωστή ασφαλής ποσότητα σταφυλιού ή σταφίδας για σκύλους: μπορεί να ακολουθήσει νεφρική ανεπάρκεια και η έγκαιρη θεραπεία μετράει.",
         SRC["grape"], "msd", exclude=r"grape.{0,3}flavo|flavo.{0,10}grape|grape.?seed|γευση σταφυλ|σταφυλ\w* γευση",
         immediate=True),
    # ---------------------------------------------------------------- cats
    Rule("CAT-LILY", ("cat",), "EMERGENCY",
         _r(r"\blil(y|ies)\b|lilium|daylil|hemerocallis|easter lil|tiger lil|κρινο|κρινου|κρινοι|ημεροκαλλ"),
         "True lilies and daylilies can cause acute kidney failure in cats, even from a small amount; early treatment gives the best outcome.",
         "Οι αληθινοί κρίνοι και οι ημεροκαλλίδες μπορούν να προκαλέσουν οξεία νεφρική ανεπάρκεια στις γάτες, ακόμη και από μικρή ποσότητα· η έγκαιρη θεραπεία δίνει το καλύτερο αποτέλεσμα.",
         SRC["lily"], "msd", exclude=r"peace lil|calla|spathiph|σπαθιφυλλ|arum|αρον", immediate=True),
    Rule("CAT-FLOWERS", ("cat",), "URGENT",
         _r(r"bouquet|flowers?|petals?|ανθοδεσμ|λουλουδ|πεταλ",
            r"chew|nibbl|ate|eat|licked|τσιμπ|εφαγε|μασ|γλειψ"),
         "A cat that chewed flowers may have eaten a lily: find out which flowers they were and call a vet today.",
         "Γάτα που μάσησε λουλούδια μπορεί να έφαγε κρίνο: βρες ποια λουλούδια ήταν και κάλεσε κτηνίατρο σήμερα.",
         SRC["lily"], "msd", exclude=r"peace lil|calla|spathiph|σπαθιφυλλ"),
    Rule("CAT-URETHRAL", ("cat",), "EMERGENCY",
         _r(r"strain|squat|trying to (pee|urinate|wee)|(going|goes|went|visiting|visits).{0,25}(litter|box|tray)|keeps going to the (litter|box|tray)|"
            r"litter|προσπαθει να ουρησει|(πηγαινει|παει|ξαναπηγαινει).{0,25}(αμμο|λεκανη)|λεκανη|αμμο",
            r"nothing|no urine|not producing|only (a |the )?(few |tiny )?(drop|dribble|bit)|just (a )?(drop|dribble)|"
            r"drops? .{0,12}(two|few)|can'?t (pee|urinate|wee)|unable to (pee|urinate)|"
            r"δεν (βγαινει|βγαζει|ουρει|καταφερνει)|σταγον|καθολου ουρ|τιποτα|ελαχιστο ουρο"),
         "Straining to urinate with little or no urine can be a urethral blockage, which can be fatal within about 2 to 3 days and is an emergency.",
         "Προσπάθεια για ούρηση με λίγα ή καθόλου ούρα μπορεί να είναι απόφραξη της ουρήθρας, που μπορεί να είναι θανατηφόρα σε περίπου 2-3 μέρες και είναι επείγον.",
         SRC["urethral"], "msd", immediate=True),
    Rule("CAT-PARACETAMOL", ("cat",), "EMERGENCY",
         _r(r"paracetamol|acetaminophen|tylenol|panadol|depon|ντεπον|παρακεταμολ"),
         "Cats are very sensitive to paracetamol: toxic effects can start at low doses and affect the blood within hours.",
         "Οι γάτες είναι πολύ ευαίσθητες στην παρακεταμόλη: τοξικά αποτελέσματα μπορεί να ξεκινήσουν με μικρές δόσεις και να επηρεάσουν το αίμα μέσα σε ώρες.",
         SRC["analgesics"], "msd", immediate=True),
    # ------------------------------------------------------ dogs and cats
    Rule("DC-NSAID", ("dog", "cat"), "URGENT",
         _r(r"ibuprofen|nurofen|advil|naproxen|aleve|brufen|ιβουπροφ|νουροφεν|ναπροξ|μπρουφεν",
            _INGEST),
         "Human anti-inflammatory pills (ibuprofen, naproxen) can cause stomach ulcers and kidney damage in dogs and cats: call a vet today.",
         "Τα ανθρώπινα αντιφλεγμονώδη (ιβουπροφαίνη, ναπροξένη) μπορεί να προκαλέσουν έλκη στομάχου και νεφρική βλάβη σε σκύλους και γάτες: κάλεσε κτηνίατρο σήμερα.",
         SRC["analgesics"], "msd"),
    Rule("DC-ANTIFREEZE", ("dog", "cat"), "EMERGENCY",
         _r(r"antifreeze|anti-freeze|ethylene glycol|coolant|αντιψυκτικ|αιθυλενογλυκολ|ψυκτικ\w* υγρ"),
         "Antifreeze (ethylene glycol) is deadly, and treatment only works well if it starts before the kidneys fail.",
         "Το αντιψυκτικό (αιθυλενογλυκόλη) είναι θανατηφόρο και η θεραπεία δουλεύει καλά μόνο αν ξεκινήσει πριν αποτύχουν τα νεφρά.",
         SRC["glycol"], "msd", immediate=True),
    Rule("DC-RODENTICIDE", ("dog", "cat"), "URGENT",
         _r(r"rat poison|rodenticide|mouse poison|warfarin|brodifacoum|bromadiolone|ποντικοφαρμακ|φαρμακο για ποντικ|δολωμα|ραδεντ|βρωμαδιολον",
            _INGEST),
         "Rat poison stops blood clotting and bleeding shows up days later; a vet can act before that if the pet is seen soon.",
         "Το ποντικοφάρμακο σταματά την πήξη του αίματος και η αιμορραγία φαίνεται μέρες αργότερα· ο κτηνίατρος μπορεί να δράσει πριν, αν δει το ζώο νωρίς.",
         SRC["rodenticide"], "msd"),
    Rule("DC-RODENTICIDE-BLEED", ("dog", "cat"), "EMERGENCY",
         _r(r"rat poison|rodenticide|mouse poison|warfarin|brodifacoum|bromadiolone|ποντικοφαρμακ|φαρμακο για ποντικ|δολωμα|ραδεντ|βρωμαδιολον",
            r"blood|bleed|bruis|nosebleed|black stool|αιμα|αιμορραγ|μελανιασ|μαυρα κοπρανα"),
         "Possible rat poison plus any bleeding is an emergency.",
         "Πιθανό ποντικοφάρμακο μαζί με οποιαδήποτε αιμορραγία είναι επείγον.",
         SRC["rodenticide"], "msd", immediate=True),
    # -------------------------------------------------------------- rabbits
    Rule("RAB-STASIS", ("rabbit",), "URGENT",
         _r(r"not eating|stopped eating|won'?t eat|no appetite|hasn'?t eaten|refus\w* (food|hay|pellet)|no (poop|droppings|faeces|feces)|"
            r"fewer (poop|droppings)|not pooping|(hasn.?t|haven.?t|not|stopped) (pooped|pooping|passed (any )?(poop|droppings|stool))|"
            r"δεν τρωει|σταματησε να τρωει|δεν (κανει|βγαζει) κοπρανα|λιγοτερα κοπρανα|χωρις κοπρανα|δεν τρωει τιποτα"),
         "A rabbit that stops eating or pooping needs a vet promptly: gut stasis can become life-threatening, so do not wait and see.",
         "Κουνέλι που σταματά να τρώει ή να κάνει κόπρανα χρειάζεται κτηνίατρο άμεσα: η στάση του εντέρου μπορεί να γίνει απειλητική για τη ζωή, μην περιμένεις.",
         SRC["rabbit_gi"], "msd"),
    Rule("RAB-STASIS-SEVERE", ("rabbit",), "EMERGENCY",
         _r(r"not eating|stopped eating|won'?t eat|no appetite|hasn'?t eaten|no (poop|droppings|faeces|feces)|not pooping|(hasn.?t|haven.?t|not|stopped) (pooped|pooping|passed (any )?(poop|droppings|stool))|δεν τρωει|σταματησε να τρωει|χωρις κοπρανα|δεν (κανει|βγαζει) κοπρανα",
            r"bloat|swollen|lethar|cold|weak|grind|hunched|collaps|φουσκ|πρησ|ληθαργ|κρυο|αδυναμ|τριξιμο δοντι|κουλουριασμ"),
         "A rabbit that stopped eating and is bloated, cold, weak or in pain needs a vet right now.",
         "Κουνέλι που σταμάτησε να τρώει και είναι φουσκωμένο, κρύο, αδύναμο ή πονάει χρειάζεται κτηνίατρο τώρα.",
         SRC["rabbit_gi"], "msd", immediate=True),
    Rule("RAB-DIARRHEA", ("rabbit",), "URGENT",
         _r(r"diarrh|watery (stool|poop)|διαρροια|νερουλ\w* κοπρανα"),
         "Diarrhoea in a rabbit, at any age, is serious and needs a vet.",
         "Η διάρροια σε κουνέλι, σε οποιαδήποτε ηλικία, είναι σοβαρή και χρειάζεται κτηνίατρο.",
         SRC["rabbit_gi"], "msd"),
    Rule("RAB-DIARRHEA-YOUNG", ("rabbit",), "EMERGENCY",
         _r(r"diarrh|watery (stool|poop)|διαρροια|νερουλ\w* κοπρανα",
            r"baby|young|weeks? old|kit\b|just weaned|weaned|μωρο|μικρο|εβδομαδ|απογαλακτ"),
         "Sudden severe diarrhoea in a young rabbit can kill quickly: go to a vet now.",
         "Ξαφνική έντονη διάρροια σε νεαρό κουνέλι μπορεί να σκοτώσει γρήγορα: πήγαινε σε κτηνίατρο τώρα.",
         SRC["rabbit_gi"], "msd", immediate=True),
    # ---------------------------------------------------------------- birds
    Rule("BIRD-EGGBOUND", ("bird",), "EMERGENCY",
         _r(r"\begg|laying|lay an egg|gravid|αυγ|ωοτοκ",
            r"strain|floor|fluff|tail[- ]?bob|swollen|distend|weak|lethar|sitting|φουσκ|πρηξ|δυσκολ|κουναει την ουρα|πατωμα|ληθαργ|αδυναμ|κατω"),
         "A bird with signs of being egg-bound (on the cage floor, straining, swollen belly, weak) is an emergency.",
         "Πουλί με σημεία εγκλωβισμένου αυγού (στο πάτωμα του κλουβιού, πίεση, φουσκωμένη κοιλιά, αδυναμία) είναι επείγον.",
         SRC["bird_repro"], "msd", immediate=True),
    Rule("BIRD-TAILBOB", ("bird",), "EMERGENCY",
         _r(r"tail[- ]?bob|tail.{0,12}bobbing|bobbing.{0,12}tail|κουναει την ουρα|κουνιεται η ουρα|ουρα.{0,15}πανω κατω|labou?red breath|δυσκολια.{0,10}αναπν"),
         "Tail bobbing or laboured breathing in a bird means it is struggling to breathe: go to an avian vet now.",
         "Το κούνημα της ουράς ή η δύσκολη αναπνοή σε πουλί σημαίνει ότι δυσκολεύεται να αναπνεύσει: πήγαινε σε κτηνίατρο πουλιών τώρα.",
         SRC["bird_owner"], "msd", immediate=True),
    Rule("BIRD-REPTILE-PROLAPSE", ("bird", "reptile"), "EMERGENCY",
         _r(r"prolaps|tissue (protrud|sticking|hanging)|(protrud|sticking out|hanging out).{0,20}(vent|cloaca)|προπτωσ|προβαλλ\w*.{0,20}(αμαρα|κλοακ)"),
         "Tissue or organs protruding from the vent need immediate veterinary care.",
         "Ιστός ή όργανα που προβάλλουν από την κλοάκα χρειάζονται άμεση κτηνιατρική φροντίδα.",
         SRC["bird_owner"] + " | " + SRC["reptile"], "msd", immediate=True),
    # ------------------------------------------------------------- reptiles
    Rule("REP-RESP", ("reptile",), "URGENT",
         _r(r"open[- ]?mouth|mouth open|nasal discharge|runny nose|bubbl\w* (at|from) (the )?(nose|mouth)|wheez|labou?red breath|"
            r"ανοιχτο στομα|εκκριση απο τη μυτη|φταρνισ|συριγμ"),
         "Open-mouth breathing or nasal discharge in a reptile can mean a respiratory infection: see a reptile vet promptly.",
         "Αναπνοή με ανοιχτό στόμα ή ρινική έκκριση σε ερπετό μπορεί να σημαίνει λοίμωξη αναπνευστικού: δες κτηνίατρο ερπετών άμεσα.",
         SRC["reptile"], "msd"),
    Rule("REP-EGGS", ("reptile",), "URGENT",
         _r(r"\begg|gravid|retained|laying|αυγ|ωοτοκ",
            r"strain|not laying|can'?t lay|stuck|swollen|lethar|weak|δυσκολ|δεν γεννα|κολλησ|φουσκ|ληθαργ|αδυναμ"),
         "A reptile that cannot lay its eggs may be egg-bound (dystocia): this needs a vet, and surgery is often necessary.",
         "Ερπετό που δεν μπορεί να γεννήσει τα αυγά του μπορεί να έχει δυστοκία: χρειάζεται κτηνίατρο και συχνά χειρουργείο.",
         SRC["reptile"], "msd"),
    Rule("REP-NEURO", ("reptile",), "URGENT",
         _r(r"star ?gazing|twisted neck|head tilt|loss of (movement|control)|can'?t (move|walk)|κεφαλι.{0,12}γυρισμεν|δεν μπορει να περπατ|δεν κουναει"),
         "A twisted neck, stargazing or loss of movement in a reptile can mean a neurological problem or metabolic bone disease: see a vet promptly.",
         "Στριμμένος λαιμός ή απώλεια κίνησης σε ερπετό μπορεί να σημαίνει νευρολογικό πρόβλημα ή μεταβολική νόσο των οστών: δες κτηνίατρο άμεσα.",
         SRC["reptile"], "msd"),
    # ------------------------------------------------------- every species
    Rule("ALL-SEIZURE-LONG", (), "EMERGENCY",
         _r(_SEIZ, _LONG),
         "A seizure lasting about 5 minutes or more, or repeating, is an emergency.",
         "Σπασμός που διαρκεί περίπου 5 λεπτά ή περισσότερο, ή που επαναλαμβάνεται, είναι επείγον.",
         "", "policy", immediate=True),
    Rule("ALL-SEIZURE", (), "URGENT",
         _r(_SEIZ),
         "Any seizure needs a vet check today.",
         "Κάθε σπασμός χρειάζεται εξέταση από κτηνίατρο σήμερα.",
         "", "policy"),
    Rule("ALL-GUMS", ("dog", "cat", "rabbit", "other"), "EMERGENCY",
         _r(_GUMS_BAD),
         "Pale, white, blue or grey gums can mean shock, blood loss or lack of oxygen: go to a vet now.",
         "Χλωμά, λευκά, μπλε ή γκρίζα ούλα μπορεί να σημαίνουν σοκ, απώλεια αίματος ή έλλειψη οξυγόνου: πήγαινε σε κτηνίατρο τώρα.",
         "", "policy", immediate=True),
    Rule("ALL-BREATH", ("dog", "cat", "rabbit", "bird", "other"), "EMERGENCY",
         _r(r"gasping|struggling to breathe|can'?t breathe|cannot breathe|not breathing|blue tongue|"
            r"δεν μπορει να αναπνε|δεν αναπνε|ασφυξ|δυσκολια στην αναπνο|αγωνια.{0,15}αναπν"),
         "Struggling to breathe is an emergency.",
         "Η δυσκολία στην αναπνοή είναι επείγον.",
         "", "policy", immediate=True),
    Rule("CAT-OPENMOUTH", ("cat",), "EMERGENCY",
         _r(r"open[- ]?mouth.{0,15}breath|breath\w*.{0,15}open[- ]?mouth|mouth open|panting|ανοιχτο στομα.{0,15}αναπν|αναπν\w*.{0,15}ανοιχτο στομα|λαχανιαζ"),
         "Open-mouth breathing or panting in a cat is an emergency.",
         "Αναπνοή με ανοιχτό στόμα ή λαχάνιασμα σε γάτα είναι επείγον.",
         "", "policy", immediate=True),
    Rule("ALL-COLLAPSE", (), "EMERGENCY",
         _r(r"collaps|unconscious|unresponsive|not responding|won'?t wake|fainted|passed out|can'?t stand|cannot stand|fell over|"
            r"καταρρευσ|λιποθυμ|αναισθητ|δεν ανταποκρινεται|δεν μπορει να σταθει|επεσε κατω"),
         "Collapse, fainting or being unable to stand is an emergency.",
         "Κατάρρευση, λιποθυμία ή αδυναμία να σταθεί είναι επείγον.",
         "", "policy", immediate=True),
    Rule("ALL-TRAUMA-BLEED", (), "EMERGENCY",
         _r(r"hit by (a )?(car|vehicle)|run over|road accident|car accident|fell (from|off).{0,20}(balcony|window|roof|height|tree)|fall from|"
            r"bleeding (heavily|a lot|profusely)|won'?t stop bleeding|bleeding (that )?won'?t stop|"
            r"αυτοκινητ.{0,15}(χτυπ|παρεσυρ)|παρασυρθηκε|τροχαι|επεσε απο.{0,15}(μπαλκον|παραθυρ|ταρατσ|υψος)|δεν σταματαει το αιμα|αιμορραγ\w*.{0,20}δεν σταματ"),
         "A road accident, a fall from height or bleeding that will not stop is an emergency, even if the pet looks fine.",
         "Τροχαίο, πτώση από ύψος ή αιμορραγία που δεν σταματά είναι επείγον, ακόμη κι αν το ζώο φαίνεται καλά.",
         "", "policy", immediate=True),
    Rule("ALL-HEATSTROKE", (), "EMERGENCY",
         _r(r"heat ?stroke|overheat|left in (the |a )?(hot )?car|hot car|θερμοπληξ|υπερθερμ|κλειδωμεν\w* (στο )?αυτοκινητ"),
         "Heatstroke or overheating is an emergency.",
         "Η θερμοπληξία ή η υπερθέρμανση είναι επείγον.",
         "", "policy", immediate=True),
    Rule("ALL-EYE-PROPTOSIS", (), "EMERGENCY",
         _r(r"eye.{0,15}(popped|out of (the )?socket|bulging out|proptos)|προεκβολ\w* οφθαλμ|ματι.{0,15}εβγηκε|ματι.{0,20}εξω απο"),
         "An eye out of its socket is an emergency.",
         "Μάτι που έχει βγει από την κόγχη είναι επείγον.",
         "", "policy", immediate=True),
    Rule("MAM-DYSTOCIA", ("dog", "cat", "rabbit"), "EMERGENCY",
         _r(r"(labou?r|giving birth|whelping|queening).{0,40}(hours?|no (puppy|kitten)|stuck|green discharge)|straining.{0,40}(no (puppy|kitten)|stuck|green discharge|in labou?r|pregnant)|"
            r"τοκετ.{0,30}(ωρες|κολλησε|πρασιν)|γεννα\w*.{0,30}(ωρες|κολλησε)"),
         "Prolonged or stalled labour is an emergency.",
         "Παρατεταμένος ή σταματημένος τοκετός είναι επείγον.",
         "", "policy", immediate=True),
    # ================= added from the MSD pet-owner pages (food, household, drugs, plants, bites, emergencies)
    Rule("DC-SNAKEBITE", ("dog", "cat"), "EMERGENCY",
         _r(r"snake|viper|adder|\bφιδι|οχι[αά]|οχια", r"\bbit(e|es|ten)?\b|bitten|fang|strike|struck|δαγκ|τσιμπ"),
         "A snakebite is an emergency: keep the pet calm and still, go to a vet immediately, and do not cut, suck, ice or tie the wound.",
         "Δάγκωμα φιδιού είναι επείγον: κράτα το ζώο ήρεμο και ακίνητο, πήγαινε αμέσως σε κτηνίατρο και μην κόψεις, μην ρουφήξεις, μην βάλεις πάγο και μην δέσεις την πληγή.",
         SRC["snake"], "msd", immediate=True),
    Rule("DC-METALDEHYDE", ("dog", "cat"), "EMERGENCY",
         _r(r"metaldehyde|μεταλδεϋδ|μεταλδευδ|(slug|snail|σαλιγκαρ|γυμνοσαλιγκ)\w*.{0,25}(bait|pellet|poison|killer|δολωμ|φαρμακ|χαπακ|κοκκ)|(δολωμ|φαρμακ|bait|pellet)\w*.{0,20}(σαλιγκαρ|γυμνοσαλιγκ|slug|snail)", _INGEST),
         "Slug and snail bait (metaldehyde) causes tremors, fever and seizures and needs intensive treatment: go to a vet now.",
         "Το δόλωμα για σαλιγκάρια και γυμνοσάλιαγκες (μεταλδεΰδη) προκαλεί τρέμουλο, πυρετό και σπασμούς και θέλει εντατική θεραπεία: πήγαινε σε κτηνίατρο τώρα.",
         SRC["metaldehyde"], "msd", immediate=True),
    Rule("DC-POISON-BAIT", ("dog", "cat"), "EMERGENCY",
         _r(r"poison(ed)? bait|strychnine|aldicarb|methomyl|carbamate|organophosph|στρυχνιν|αλντικαρμπ|μεθομυλ|οργανοφωσφ|"
            r"δηλητηριασμεν\w*.{0,15}(δολωμ|φαγητ|κρεας|λουκανικ|κεφτε)"),
         "Suspected poisoned bait or an insecticide (carbamate, organophosphate, strychnine) can cause drooling, tremors, breathing trouble and seizures within hours: go to a vet now.",
         "Πιθανό δηλητηριασμένο δόλωμα ή εντομοκτόνο (καρβαμιδικό, οργανοφωσφορικό, στρυχνίνη) μπορεί να προκαλέσει σάλια, τρέμουλο, δύσπνοια και σπασμούς μέσα σε ώρες: πήγαινε σε κτηνίατρο τώρα.",
         SRC["insecticide"], "msd", immediate=True),
    Rule("CAT-DOGFLEA", ("cat",), "EMERGENCY",
         _r(r"permethrin|περμεθριν|dog (flea|tick|spot|pipette|drops|treatment|collar|product)|(for|made for) dogs|σταγονες.{0,12}σκυλ|αντιπαρασιτικ\w*.{0,12}σκυλ|για σκυλους|για σκυλο",
            r"appl|put|used|gave|on (my|the|her|him|our) cat|εβαλα|εφαρμοσα|χρησιμοποιησα|στη γατα|στον γατο|στη γατουλα"),
         "Dog flea products (permethrin) can cause tremors and seizures in cats: wash the product off now with mild dish soap and lukewarm water, keep the cat warm, and go to a vet immediately.",
         "Τα αντιπαρασιτικά για σκύλους (περμεθρίνη) μπορεί να προκαλέσουν τρέμουλο και σπασμούς στις γάτες: ξέπλυνε αμέσως το προϊόν με ήπιο απορρυπαντικό πιάτων και χλιαρό νερό, κράτα τη γάτα ζεστή και πήγαινε αμέσως σε κτηνίατρο.",
         SRC["insecticide"], "policy", immediate=True),
    Rule("DC-BATTERY", ("dog", "cat"), "EMERGENCY",
         _r(r"batter(y|ies)|button cell|coin cell|μπαταρι", _INGEST),
         "A swallowed battery (especially a flat button or lithium cell) can burn the throat and stomach within hours: go to a vet now and do not make the pet vomit.",
         "Μια μπαταρία που καταπίθηκε (ιδίως κουμπί ή λιθίου) μπορεί να κάψει τον οισοφάγο και το στομάχι μέσα σε ώρες: πήγαινε σε κτηνίατρο τώρα και μην προκαλέσεις εμετό.",
         SRC["household"], "msd", immediate=True),
    Rule("DC-CORROSIVE", ("dog", "cat"), "URGENT",
         _r(r"drain (cleaner|opener|unblocker)|bleach|dishwasher (tablet|detergent|pod|powder)|toilet (cleaner|bowl cleaner)|oven cleaner|caustic|corrosive|limescale|"
            r"χλωριν|αλευκαντικ|μπλιτσ|καθαριστικ\w*.{0,12}(αποχετευσ|τουαλετ|φουρν|πλυντηρι)|αποφρακτικ|καυστικ", _INGEST),
         "Swallowed drain, toilet or dishwasher cleaner and bleach can burn the mouth, throat and stomach, sometimes hours later: call a vet now, give only water or milk, and do not induce vomiting.",
         "Καθαριστικά αποχέτευσης, τουαλέτας ή πλυντηρίου πιάτων και χλωρίνη που καταπίθηκαν μπορεί να κάψουν στόμα, λαιμό και στομάχι, ακόμη και ώρες αργότερα: κάλεσε κτηνίατρο τώρα, δώσε μόνο νερό ή γάλα και μην προκαλέσεις εμετό.",
         SRC["household"], "msd"),
    Rule("DC-ALCOHOL", ("dog", "cat"), "URGENT",
         _r(r"alcohol|\bbeer|\bwine|vodka|whisk|\brum\b|ouzo|tsipouro|raki\b|liqueur|antiseptic spray|αλκοολ|μπυρα|κρασι|βοτκα|ουισκι|ουζο|τσιπουρο|ρακη",
            r"drank|drunk|lapped|licked|\bate\b|swallow|ηπιε|ηπιαν|γλειψ|καταπι|ποτισ|εφαγε"),
         "Alcohol can cause vomiting, wobbliness, low body temperature and slow breathing within 30 to 60 minutes: call a vet now.",
         "Το αλκοόλ μπορεί να προκαλέσει εμετό, αστάθεια, χαμηλή θερμοκρασία και αργή αναπνοή μέσα σε 30 έως 60 λεπτά: κάλεσε κτηνίατρο τώρα.",
         SRC["household"], "msd"),
    Rule("DC-OTC-STIMULANT", ("dog", "cat"), "URGENT",
         _r(r"pseudoephedrine|ephedrine|ephedra|sudafed|decongestant|oxymetazoline|xylometazoline|naphazoline|tetrahydrozoline|nasal spray|eye drops for redness|guarana|"
            r"aspirin|ασπιριν|ψευδοεφεδριν|εφεδριν|ρινικο σπρει|αποσυμφορητικ", _INGEST),
         "Cold and flu medicines (decongestants), aspirin and stimulant supplements can cause a racing heart, tremors, seizures or bleeding in pets: call a vet or poison line now.",
         "Φάρμακα για το κρυολόγημα (αποσυμφορητικά), ασπιρίνη και διεγερτικά συμπληρώματα μπορεί να προκαλέσουν ταχυκαρδία, τρέμουλο, σπασμούς ή αιμορραγία: κάλεσε κτηνίατρο ή κέντρο δηλητηριάσεων τώρα.",
         SRC["otc"], "msd"),
    Rule("DC-RX-HUMAN", ("dog", "cat"), "URGENT",
         _r(r"antidepress|prozac|fluoxetine|sertraline|zoloft|citalopram|escitalopram|venlafaxine|amitriptyline|beta[- ]?blocker|propranolol|metoprolol|atenolol|bisoprolol|"
            r"amlodipine|diltiazem|verapamil|lisinopril|enalapril|ramipril|losartan|baclofen|cyclobenzaprine|zolpidem|alprazolam|xanax|diazepam|lorazepam|valium|"
            r"sleeping (pill|tablet|aid)|sedative|tranquili[sz]er|adhd|ritalin|adderall|amphetamine|methylphenidate|vitamin d|cholecalciferol|calcipotriene|calcipotriol|psoriasis|"
            r"iron (pill|tablet|supplement)|ferrous|blood pressure (pill|tablet|medic)|heart (pill|tablet|medic)|"
            r"αντικαταθλιπτ|ηρεμιστικ|υπνωτικ|βιταμινη d|σιδηρ|ψωριασ|χαπι\w*.{0,12}(πιεση|καρδια|υπνο|ηρεμ)|βηταλυτικ|ριταλιν", _INGEST),
         "Human prescription drugs (antidepressants, heart and blood-pressure pills, sleeping pills, ADHD drugs, vitamin D or iron) can cause heart rhythm problems, seizures or kidney damage, sometimes after a delay: call a vet or poison line now.",
         "Τα ανθρώπινα συνταγογραφούμενα φάρμακα (αντικαταθλιπτικά, χάπια για καρδιά και πίεση, υπνωτικά, φάρμακα ΔΕΠΥ, βιταμίνη D ή σίδηρος) μπορεί να προκαλέσουν αρρυθμίες, σπασμούς ή νεφρική βλάβη, ενίοτε με καθυστέρηση: κάλεσε κτηνίατρο ή κέντρο δηλητηριάσεων τώρα.",
         SRC["rx"], "msd"),
    Rule("DC-FLUOROURACIL", ("dog", "cat"), "EMERGENCY",
         _r(r"fluorouracil|5-?fu\b|efudex|carac\b|φθοριουρακιλ|φλουορουρακιλ", _INGEST),
         "5-fluorouracil skin cream can kill a dog even in small amounts, with vomiting then seizures within hours: go to a vet immediately.",
         "Η κρέμα 5-φθοριουρακίλης μπορεί να σκοτώσει σκύλο ακόμη και σε μικρή ποσότητα, με εμετό και μετά σπασμούς μέσα σε ώρες: πήγαινε αμέσως σε κτηνίατρο.",
         SRC["rx"], "msd", immediate=True),
    Rule("DC-PLANT-SEVERE", ("dog", "cat"), "EMERGENCY",
         _r(r"oleander|πικροδαφν|\byew\b|ταξοσ|lily of the valley|κρινακι.{0,12}κοιλαδ|castor (bean|oil plant)|\bricin|κικινο|azalea|rhododendron|αζαλεα|ροδοδενδρ|"
            r"mistletoe|ιξοσ|autumn crocus|colchicum|κολχικ", _INGEST),
         "Oleander, yew, lily of the valley, azalea, castor bean, mistletoe and autumn crocus are dangerous to the heart, gut or breathing and can kill quickly: go to a vet now.",
         "Η πικροδάφνη, ο ίταμος, το κρινάκι της κοιλάδας, η αζαλέα, η καστορέλαιο-φυτό (κικίνος), το γκι και το φθινοπωρινό κρόκο είναι επικίνδυνα για καρδιά, έντερο ή αναπνοή και μπορούν να σκοτώσουν γρήγορα: πήγαινε σε κτηνίατρο τώρα.",
         SRC["plants"], "msd", immediate=True),
    Rule("DC-PLANT-OTHER", ("dog", "cat"), "URGENT",
         _r(r"foxglove|διγιταλ|sago|cycad|coontie|κυκασ|dieffenbachia|dumb ?cane|philodendron|caladium|ντιφενμπαχ|φιλοδενδρ|καλαδι|"
            r"marijuana|cannabis|hashish|\bthc\b|κανναβ|μαριχουαν|χασισ|jerusalem cherry|cyclamen|κυκλαμιν", _INGEST),
         "This plant (or cannabis) can cause heart or liver problems, mouth and throat swelling, or poisoning signs within hours: call a vet today, sooner if breathing, wobbling or vomiting starts.",
         "Αυτό το φυτό (ή η κάνναβη) μπορεί να προκαλέσει καρδιακά ή ηπατικά προβλήματα, πρήξιμο σε στόμα και λαιμό ή σημεία δηλητηρίασης μέσα σε ώρες: κάλεσε κτηνίατρο σήμερα, νωρίτερα αν αρχίσει δύσπνοια, αστάθεια ή εμετός.",
         SRC["plants"], "msd"),
    Rule("DOG-BREADDOUGH", ("dog",), "URGENT",
         _r(r"\bdough\b|ζυμη|ζυμαρι|προζυμ", _INGEST),
         "Raw yeast dough swells in the stomach and makes alcohol: it can twist the stomach or cause staggering and seizures, so call a vet today and watch for a swollen belly or retching.",
         "Η ωμή ζύμη με μαγιά φουσκώνει στο στομάχι και παράγει αλκοόλ: μπορεί να στρίψει το στομάχι ή να προκαλέσει ζάλη και σπασμούς, οπότε κάλεσε κτηνίατρο σήμερα και πρόσεξε φουσκωμένη κοιλιά ή ξερομάρισμα.",
         SRC["food"], "msd"),
    Rule("BIRD-AVOCADO", ("bird",), "EMERGENCY",
         _r(r"avocado|guacamole|αβοκαντο", _INGEST),
         "Avocado can kill pet birds within 48 hours by damaging the heart: go to an avian vet now.",
         "Το αβοκάντο μπορεί να σκοτώσει πουλιά μέσα σε 48 ώρες βλάπτοντας την καρδιά: πήγαινε τώρα σε κτηνίατρο πουλιών.",
         SRC["food"], "msd", immediate=True),
    Rule("DC-SALT", ("dog", "cat"), "URGENT",
         _r(r"salt dough|play ?dough|rock salt|too much salt|(a lot|lots|bag|handful|pack) of salt|ζυμαρι.{0,12}αλατ|πολυ αλατι|αλατι.{0,12}(παλαμ|πακετο|σακουλ)", _INGEST),
         "A large amount of salt (salt dough, rock salt) can cause vomiting, tremors and seizures: call a vet now and give water only in small sips.",
         "Μεγάλη ποσότητα αλατιού (ζύμη αλατιού, χονδρό αλάτι) μπορεί να προκαλέσει εμετό, τρέμουλο και σπασμούς: κάλεσε κτηνίατρο τώρα και δώσε νερό μόνο σε μικρές γουλιές.",
         SRC["salt"], "msd"),
    Rule("DC-CHOKING", ("dog", "cat"), "EMERGENCY",
         _r(r"\bchok(e|es|ed|ing)\b|something stuck in (his|her|the|its) throat|stuck in (his|her|the|its) throat|πνιγεται|πνιγηκε|κολλησε.{0,15}λαιμο|σφηνωσε.{0,15}λαιμο"),
         "A choking pet can stop breathing: check the mouth without putting your fingers in, give firm thumps between the shoulder blades, and go to a vet at once.",
         "Ένα ζώο που πνίγεται μπορεί να σταματήσει να αναπνέει: κοίταξε το στόμα χωρίς να βάλεις τα δάχτυλα μέσα, δώσε δυνατά χτυπήματα ανάμεσα στις ωμοπλάτες και πήγαινε αμέσως σε κτηνίατρο.",
         SRC["emergency"], "msd", exclude=r"choke (chain|collar|leash)|chok\w* collar|κολαρο στραγγαλ", immediate=True),
    Rule("DC-BLOODY-GI", ("dog", "cat"), "URGENT",
         _r(r"(bloody|blood in|with blood|blood\b).{0,20}(diarrh|stool|poo|vomit|faeces|feces|vomit)|(diarrh|stool|poo|vomit|faeces|feces).{0,20}(blood|bloody|bloodstain)|coffee[- ]?ground|"
            r"αιμα.{0,20}(διαρρο|κοπρανα|εμετ)|(διαρροι|κοπρανα|εμετ\w*|εξεμεσ\w*).{0,20}(αιμα|αιματ)|αιματηρ|ματωμεν"),
         "Blood in vomit or diarrhoea can mean haemorrhagic gastroenteritis, parvovirus or an obstruction, and dehydration can set in fast: see a vet today.",
         "Αίμα στον εμετό ή στη διάρροια μπορεί να σημαίνει αιμορραγική γαστρεντερίτιδα, παρβοϊό ή απόφραξη και η αφυδάτωση έρχεται γρήγορα: δες κτηνίατρο σήμερα.",
         SRC["dog_gi"], "msd", exclude=r"rat poison|rodenticide|ποντικοφαρμακ"),
    Rule("DOG-PARVO", ("dog",), "EMERGENCY",
         _r(r"parvo|παρβο|(puppy|pup\b|κουταβ|\b\d+ ?(weeks?|εβδομαδ)).{0,60}(bloody|blood|αιμα|αιματ)",
            r"vomit|diarrh|lethar|bloody|blood|sick|εμετ|διαρρο|ληθαργ|αιμα"),
         "A puppy or unvaccinated dog with vomiting and bloody diarrhoea may have parvovirus, which can kill within hours without treatment: go to a vet now and keep them away from other dogs.",
         "Ένα κουτάβι ή αεμβολίαστος σκύλος με εμετό και αιματηρή διάρροια μπορεί να έχει παρβοϊό, που μπορεί να σκοτώσει μέσα σε ώρες χωρίς θεραπεία: πήγαινε τώρα σε κτηνίατρο και κράτα τον μακριά από άλλους σκύλους.",
         SRC["dog_gi"], "msd", exclude=r"vaccinated for parvo|εμβολιασμεν\w* για παρβο|parvo (shot|vaccine|vaccination)", immediate=True),
    Rule("DC-FOREIGN-BODY", ("dog", "cat"), "URGENT",
         _r(r"\bsock|stocking|\bstring\b|\byarn|\bthread|tinsel|needle|ribbon|hair ?tie|rubber band|corn ?cob|fishing (line|hook)|"
            r"καλτσα|κλωστη|βελονα|κορδελα|λαστιχακι|καλαμποκι.{0,8}(ροκα|στελεχοσ)|πετονι|αγκιστρι", _INGEST),
         "A swallowed sock, string, needle, ribbon or corn cob can block or cut the gut: call a vet today, do not pull anything hanging out, and go now if vomiting, belly pain or retching starts.",
         "Κάλτσα, κλωστή, βελόνα, κορδέλα ή ρόκα καλαμποκιού που καταπίθηκε μπορεί να φράξει ή να κόψει το έντερο: κάλεσε κτηνίατρο σήμερα, μην τραβήξεις κάτι που κρέμεται και πήγαινε αμέσως αν αρχίσει εμετός, πόνος ή ξερομάρισμα.",
         SRC["dog_gi"], "msd"),
    # ============ small mammals ("other": guinea pig, hamster, ferret, rat, mouse, chinchilla) from the MSD all-other-pets pages
    Rule("OTH-NOEAT", ("other",), "URGENT",
         _r(r"not eating|stopped eating|won'?t eat|no appetite|hasn'?t eaten|refus\w* (food|hay|pellet)|off (his|her) food|no food|"
            r"δεν τρωει|σταματησε να τρωει|δεν εφαγε|χωρις ορεξη|δεν θελει φαγητο"),
         "A small pet (guinea pig, hamster, ferret, rat) that stops eating needs a vet promptly: they dehydrate and decline fast, and some die suddenly.",
         "Ένα μικρό κατοικίδιο (ινδικό χοιρίδιο, χάμστερ, κουνάβι, αρουραίος) που σταματά να τρώει χρειάζεται κτηνίατρο άμεσα: αφυδατώνεται και χειροτερεύει γρήγορα και μερικά πεθαίνουν ξαφνικά.",
         SRC["gp_common"], "msd"),
    Rule("OTH-RESP", ("other",), "URGENT",
         _r(r"wheez|nasal discharge|runny nose|eye discharge|sneez|breathing (fast|heavily|hard|noisily)|noisy breathing|"
            r"συριγμ|ρινικ\w* εκκριση|εκκριση απο τη μυτη|φταρνισ|γρηγορη αναπνο|βαρια αναπνο"),
         "Wheezing, sneezing, nose or eye discharge or fast breathing in a small pet can be pneumonia, a leading cause of death in guinea pigs and hamsters: see a vet promptly.",
         "Συριγμός, φτέρνισμα, έκκριση από μύτη ή μάτια ή γρήγορη αναπνοή σε μικρό κατοικίδιο μπορεί να είναι πνευμονία, κύρια αιτία θανάτου στα ινδικά χοιρίδια και τα χάμστερ: δες κτηνίατρο άμεσα.",
         SRC["gp_common"] + " | " + SRC["hamster"], "msd"),
    Rule("OTH-DIARRHEA", ("other",), "URGENT",
         _r(r"diarrh|wet tail|watery (stool|poop)|runny (stool|poop)|διαρροια|υγρη ουρα|νερουλ\w* κοπρανα"),
         "Diarrhoea (wet tail) in a small pet is serious: dehydration and rapid decline are common, and giving antibiotics that were not prescribed can make it worse.",
         "Η διάρροια (υγρή ουρά) σε μικρό κατοικίδιο είναι σοβαρή: αφυδάτωση και γρήγορη επιδείνωση είναι συχνές και αντιβιοτικά που δεν έχουν συνταγογραφηθεί μπορούν να το χειροτερέψουν.",
         SRC["hamster"] + " | " + SRC["ferret_emerg"], "msd"),
    Rule("OTH-DIARRHEA-YOUNG", ("other",), "EMERGENCY",
         _r(r"diarrh|wet tail|watery (stool|poop)|διαρροια|υγρη ουρα|νερουλ\w* κοπρανα",
            r"baby|young|juvenile|weeks? old|just weaned|weaned|new ?born|μωρο|μικρο|νεαρο|εβδομαδ|απογαλακτ"),
         "Diarrhoea in a young hamster or other young small pet (proliferative ileitis, Tyzzer disease) can kill within a day or two: go to a vet now.",
         "Διάρροια σε νεαρό χάμστερ ή άλλο νεαρό μικρό κατοικίδιο (εντερίτιδα, νόσος Tyzzer) μπορεί να σκοτώσει μέσα σε μία με δύο μέρες: πήγαινε σε κτηνίατρο τώρα.",
         SRC["hamster"], "msd", immediate=True),
    Rule("OTH-PROLAPSE", ("other", "dog", "cat", "rabbit"), "EMERGENCY",
         _r(r"prolaps|(intestine|bowel|rectum|gut).{0,20}(sticking|protrud|hanging|coming) out|(sticking|protrud|hanging) out.{0,20}(bottom|anus|rectum)|"
            r"προπτωσ|εντερο.{0,15}εξω|προβαλλ\w*.{0,15}(πρωκτ|ορθο)"),
         "Intestine or rectum protruding from the bottom (prolapse) is an emergency needing immediate veterinary care.",
         "Έντερο ή ορθό που προβάλλει από τον πρωκτό (πρόπτωση) είναι επείγον και χρειάζεται άμεση κτηνιατρική φροντίδα.",
         SRC["hamster"] + " | " + SRC["ferret_emerg"], "msd", immediate=True),
    Rule("OTH-FERRET-NEURO", ("other",), "EMERGENCY",
         _r(r"ferret|κουναβι",
            r"seiz|convuls|staggering|dragging|can'?t walk|weak|lethar|collaps|pawing at (the |his |her )?mouth|drool|"
            r"σπασμ|τρικλιζ|σερν|δεν περπατ|αδυναμ|ληθαργ|σαλια"),
         "A ferret that is weak, staggering, dragging its back legs, drooling or having seizures may have low blood sugar (insulinoma) or another emergency: see a vet immediately.",
         "Ένα κουνάβι που είναι αδύναμο, τρικλίζει, σέρνει τα πίσω πόδια, σαλιώνει ή έχει σπασμούς μπορεί να έχει χαμηλό σάκχαρο (ινσουλίνωμα) ή άλλο επείγον: πήγαινε αμέσως σε κτηνίατρο.",
         SRC["ferret_emerg"], "msd", immediate=True),
    Rule("OTH-FERRET-GI", ("other",), "URGENT",
         _r(r"ferret|κουναβι",
            r"vomit|retch|stopped (eating|pooping|defecating)|no (poop|stool|droppings)|black (tarry )?stool|tarry|choking|cough|"
            r"εμετ|ξερατ|δεν κανει κοπρανα|μαυρα κοπρανα|βηχ"),
         "A ferret that vomits, stops eating or passing stool, or has black tarry stool may have a blockage or bleeding and dehydrates quickly: see a vet today.",
         "Ένα κουνάβι που κάνει εμετό, σταματά να τρώει ή να κάνει κόπρανα ή έχει μαύρα κόπρανα μπορεί να έχει απόφραξη ή αιμορραγία και αφυδατώνεται γρήγορα: δες κτηνίατρο σήμερα.",
         SRC["ferret_emerg"], "msd"),
    Rule("OTH-GP-SCURVY", ("other",), "URGENT",
         _r(r"guinea ?pig|cavy|χοιριδι\w* ινδι|ινδικ\w* χοιριδι",
            r"swollen (joint|leg|paw)|limping|lame|bleeding gums?|rough coat|bruis|πρηγμεν\w* (αρθρ|ποδ)|κουτσαιν|ματωνουν|ουλα.{0,10}αιμα|μελανιασ"),
         "Swollen joints, limping, bleeding gums or bruising in a guinea pig suggest vitamin C deficiency (scurvy), which can be fatal if untreated: see a vet promptly.",
         "Πρησμένες αρθρώσεις, κουτσαμάρα, αιμορραγία στα ούλα ή μελανιές σε ινδικό χοιρίδιο παραπέμπουν σε έλλειψη βιταμίνης C (σκορβούτο), που μπορεί να είναι θανατηφόρο χωρίς θεραπεία: δες κτηνίατρο άμεσα.",
         SRC["gp_nutrition"], "msd"),
    # ============ gaps found by running real MSD case-study presentations through the rules (policy: need vet sign-off)
    Rule("ALL-NEURO", ("dog", "cat", "rabbit", "other"), "URGENT",
         _r(r"head ?press|pressing (his|her|its|the) head|disorient|circling|walking in circles|stumbl|unsteady|ataxi|wobbl|staggering|can'?t walk straight|lost (his|her) balance|head tilt|"
            r"πιεζει το κεφαλι|κεφαλι.{0,12}(τοιχο|γωνια)|ζαλισμεν|γυριζει κυκλους|γυρναει κυκλους|τρικλιζ|χανει την ισορροπι|γερνει το κεφαλι"),
         "Head pressing, disorientation, circling, stumbling or a head tilt point to a brain or balance problem: see a vet today, and go now if it comes with seizures or collapse.",
         "Πίεση του κεφαλιού, αποπροσανατολισμός, κυκλικές κινήσεις, τρικλίσματα ή γερμένο κεφάλι παραπέμπουν σε πρόβλημα εγκεφάλου ή ισορροπίας: δες κτηνίατρο σήμερα και πήγαινε αμέσως αν συνοδεύεται από σπασμούς ή κατάρρευση.",
         "", "policy"),
    Rule("CAT-ABDOMEN", ("cat",), "URGENT",
         _r(r"(swollen|distended|bloated|enlarged|big|fat)\w* .{0,10}(belly|abdomen|tummy|stomach)|(belly|abdomen|tummy|stomach).{0,20}(swollen|distended|bloated|enlarged)|φουσκωμεν\w* κοιλι|κοιλι\w*.{0,15}(πρησμεν|φουσκωμεν)",
            r"letharg|weight loss|losing weight|not eating|poor appetite|reduced appetite|no appetite|weak|ληθαργ|αδυνατισ|χασε βαρος|δεν τρωει|αδυναμ"),
         "A swollen belly with lethargy, weight loss or poor appetite in a cat can mean fluid (for example from FIP), organ disease or a tumour: see a vet within the day.",
         "Φουσκωμένη κοιλιά με λήθαργο, απώλεια βάρους ή κακή όρεξη σε γάτα μπορεί να σημαίνει υγρό (π.χ. από FIP), νόσο οργάνου ή όγκο: δες κτηνίατρο μέσα στην ημέρα.",
         SRC["cases"], "policy"),
    Rule("DC-GI-PERSISTENT", ("dog", "cat"), "URGENT",
         _r(r"vomit|throw(ing)? up|threw up|diarrh|εμετ|ξερασ|διαρρο",
            r"(for|since|over|last|past) .{0,12}(\b([2-9]|\d\d)\b ?(days?|μερ)|several days|few days|days|couple of days)|\b([2-9]|\d\d)\b ?(days?|μερες)|several days|few days|for days|μερες|εδω και μερες|3 με 4|3-4"),
         "Vomiting or diarrhoea lasting two days or more, especially with poor appetite or drinking, dehydrates a pet and can hide kidney, liver or gut disease: see a vet today.",
         "Εμετός ή διάρροια που κρατά δύο μέρες ή περισσότερο, ιδίως με κακή όρεξη ή χωρίς νερό, αφυδατώνει το ζώο και μπορεί να κρύβει νεφρική, ηπατική ή εντερική νόσο: δες κτηνίατρο σήμερα.",
         SRC["dog_gi"] + " | " + SRC["cases"], "policy",
         exclude=r"\bonce\b|one time|only once|just once|\bago\b|μια φορα|μονο μια|πριν απο"),
    Rule("DC-HEMATURIA", ("dog", "cat"), "URGENT",
         _r(r"blood in (his|her|the|their)? ?(urine|pee|wee)|bloody (urine|pee|wee)|(urine|pee|wee) .{0,12}(blood|bloody|red|pink)|red urine|pink urine|αιμα στα ουρα|αιματουρ|ουρα.{0,12}(αιμα|κοκκιν|ροζ)|κοκκινα ουρα"),
         "Blood in the urine can come from a bladder infection, stones, or a tumour, and a blockage can follow: see a vet today, and go now if there is straining with little or no urine.",
         "Αίμα στα ούρα μπορεί να οφείλεται σε κυστίτιδα, πέτρες ή όγκο και μπορεί να ακολουθήσει απόφραξη: δες κτηνίατρο σήμερα και πήγαινε αμέσως αν υπάρχει προσπάθεια ούρησης με λίγα ή καθόλου ούρα.",
         SRC["cases"], "policy"),
    Rule("DC-LAME-SEVERE", ("dog", "cat"), "URGENT",
         _r(r"won'?t (put|bear) (any )?weight|not (putting|bearing) (any )?weight|can'?t (put|bear) (any )?weight|three[- ]legged|on three legs|holding (up )?(a |his |her |the )?(front |back |hind )?(leg|paw|limb)|carrying (a |his |her |the )?(leg|paw)|"
            r"yelp\w*.{0,40}(leg|limb|paw|jump|fell)|fell .{0,30}(then|and) .{0,20}(lame|limp)|severely lame|"
            r"δεν πατα|τρια ποδια|σηκωνει το ποδι|κρατα ψηλα το ποδι|κουτσαιν\w* πολυ|πολυ κουτσ|ουρλιαζ.{0,30}ποδι"),
         "Not putting weight on a leg, holding it up, or yelping with a sudden severe limp can mean a fracture, a torn ligament or a bone problem: see a vet today.",
         "Αν δεν πατά το πόδι, το κρατά ψηλά ή ουρλιάζει με ξαφνικό σοβαρό κούτσαμα, μπορεί να είναι κάταγμα, ρήξη συνδέσμου ή πρόβλημα στο οστό: δες κτηνίατρο σήμερα.",
         SRC["emergency"], "msd"),
    # ---- from the second batch of MSD case studies (M009-M021); policy basis unless noted: a vet must confirm
    Rule("DC-CANT-WALK", ("dog", "cat"), "EMERGENCY",
         _r(r"(can'?t|cannot|unable to|not able to|won'?t be able to|couldn'?t) (walk|stand|get up|use (his|her) (back|hind|rear) legs)|paraly[sz]|dragging (his|her) (back|hind|rear) (legs?|end)|"
            r"δεν μπορει (πλεον )?να (περπατησ|σηκωθ|σταθ)|ακινητοποιηθηκε|παραλυσ|σερνει τα (πισω )?ποδια"),
         "A pet that suddenly cannot walk or stand can have a spinal, nerve, heart or poisoning emergency: go to a vet now.",
         "Ζώο που ξαφνικά δεν μπορεί να περπατήσει ή να σταθεί μπορεί να έχει επείγον πρόβλημα σπονδυλικής στήλης, νεύρων, καρδιάς ή δηλητηρίαση: πήγαινε σε κτηνίατρο αμέσως.",
         SRC["cases"], "policy", immediate=True),
    Rule("DC-NOSEBLEED", ("dog", "cat", "rabbit"), "EMERGENCY",
         _r(r"nose ?bleed|epistaxis|blood (spray\w*|comes?|coming|pour\w*|drip\w*|runs?|running|squirt\w*) .{0,20}nose|bleed\w* (from|out of) (his|her|the|its) nose|blood from (his|her|the|its) nose|"
            r"αιμορραγι\w* απο (τη|την) μυτη|αιμα απο (τη|την) μυτη|μυτη.{0,15}(αιμορραγ|αιματ)"),
         "Heavy or repeated nosebleeds can mean a clotting problem, poisoning, a tumour or a nasal infection: go to a vet now.",
         "Έντονη ή επαναλαμβανόμενη ρινορραγία μπορεί να οφείλεται σε διαταραχή πήξης, δηλητηρίαση, όγκο ή λοίμωξη της μύτης: πήγαινε σε κτηνίατρο αμέσως.",
         SRC["cases"], "policy", immediate=True),
    Rule("DC-JAUNDICE", ("dog", "cat"), "URGENT",
         _r(r"yellow\w* (skin|gums?|eyes?|whites|ears?)|(skin|gums?|eyes?|whites|ears?).{0,20}yellow|jaundic|icter|"
            r"κιτρινο (δερμα|ματια|ουλα)|(δερμα|ματια|ουλα).{0,20}κιτριν|κιτρινισ|ικτερ"),
         "Yellow skin, gums or eyes (jaundice) means a liver, gallbladder or blood problem: see a vet today.",
         "Κίτρινο δέρμα, ούλα ή μάτια (ίκτερος) δείχνει πρόβλημα στο συκώτι, στη χολή ή στο αίμα: δες κτηνίατρο σήμερα.",
         SRC["cases"], "policy"),
    Rule("DC-ANOREXIA-LONG", ("dog", "cat"), "URGENT",
         _r(r"(not|n'?t|never|stopped|refus\w*) .{0,16}(eat|eaten|eating|food)\b",
            r"(for|since|over|more than|nearly|almost) .{0,10}(24 ?(hours|hrs|h)|a day|one day|two days|\b([2-9]|\d\d)\b ?days|a week|week|weeks)|a week|\d+ days|24 hours"),
         "A dog or cat that has not eaten for a day or more, especially with lethargy, vomiting or pain, should be seen by a vet today.",
         "Σκύλος ή γάτα που δεν έχει φάει για μία μέρα ή περισσότερο, ιδίως με ληθαργικότητα, εμετό ή πόνο, πρέπει να εξεταστεί από κτηνίατρο σήμερα.",
         SRC["cases"], "policy", exclude=r"\b(just|only) (a|one) (meal|bite)|fasting|fasted|surgery|before (the )?(op|operation|surgery)"),
    Rule("DC-WOUND-NONHEAL", ("dog", "cat", "rabbit", "other"), "URGENT",
         _r(r"not healing|won'?t heal|isn'?t healing|aren'?t healing|(wound|bite|bites|abscess|sore)s?.{0,50}(infected|pus|oozing|smell\w*|swollen|getting worse|worse)|"
            r"δεν γιατρευ|δεν κλεινει|πληγ\w*.{0,30}(πυο|μολυσμ|χειροτερ|βρωμ)"),
         "A wound or bite that is not healing, or is swollen, oozing or smelly, is infected until proven otherwise: see a vet today.",
         "Πληγή ή δάγκωμα που δεν επουλώνεται ή είναι πρησμένο, τρέχει ή μυρίζει θεωρείται μολυσμένο μέχρι να αποδειχθεί το αντίθετο: δες κτηνίατρο σήμερα.",
         SRC["cases"], "policy"),
    Rule("DC-LUMP-OPEN", ("dog", "cat", "rabbit", "other"), "URGENT",
         _r(r"(lumps?|swellings?|bumps?|masses|mass|growths?|tumou?rs?).{0,90}(burst|ruptur|\bopen\b|opened|oozing|draining|bleeding|discharg|ulcerat)|(burst|ruptured|opened).{0,20}(lumps?|swellings?|growths?)|"
            r"(εξογκωμα|εξογκωματα|κομποι|ογκο\w*|μαζα|μπαλιτσα).{0,40}(εσπασ|ανοιξ|αιμορραγ|τρεχ|πυο)"),
         "A lump that has opened, bleeds or oozes can be infected or a tumour: see a vet within the day.",
         "Εξόγκωμα που άνοιξε, αιμορραγεί ή τρέχει μπορεί να είναι μολυσμένο ή όγκος: δες κτηνίατρο μέσα στην ημέρα.",
         SRC["cases"], "policy"),
    Rule("DOG-URINARY-STRAIN", ("dog",), "URGENT",
         _r(r"strain\w* to (pee|urinate|wee)|strain\w* .{0,6}(pee|urinat|wee)|(pee|urinat|wee)\w* .{0,6}straining|trying to (pee|urinate|wee)|cannot (pee|urinate)|can'?t (pee|urinate)|"
            r"προσπαθει να ουρησει|δυσκολευεται να ουρησει|ουρα.{0,12}(σταγον|δυσκολ)"),
         "A dog straining to urinate can have stones, a blocked urethra, a prostate problem or a tumour: see a vet today, and go now if no urine comes out at all.",
         "Σκύλος που δυσκολεύεται να ουρήσει μπορεί να έχει πέτρες, απόφραξη ουρήθρας, πρόβλημα προστάτη ή όγκο: δες κτηνίατρο σήμερα και πήγαινε αμέσως αν δεν βγαίνει καθόλου ούρο.",
         SRC["cases"], "policy"),
    Rule("DC-YOUNG-GI", ("dog", "cat"), "URGENT",
         _r(r"puppy|\bpup\b|kitten|κουταβ|γατακ|\b([1-9]|1[0-9]|2[0-4]) ?[- ]?(weeks?|εβδομαδ)[- ]?(old|ων|ης)?|\b([1-5]) ?[- ]?(months?|μην\w*)[- ]?(old|ων|ης)?|young|new ?born",
            r"vomit|diarrh|letharg|not eating|poor appetite|reduced appetite|soft stool|yellow stool|εμετ|διαρρο|ληθαργ|δεν τρωει|αδυναμ|μαλακα κοπρανα"),
         "A puppy or kitten with vomiting, diarrhoea, lethargy or poor appetite can crash within hours (low blood sugar, dehydration, parvovirus, parasites): see a vet today.",
         "Ένα κουτάβι ή γατάκι με εμετό, διάρροια, λήθαργο ή κακή όρεξη μπορεί να χειροτερέψει μέσα σε ώρες (χαμηλό σάκχαρο, αφυδάτωση, παρβοϊός, παράσιτα): δες κτηνίατρο σήμερα.",
         SRC["dog_gi"] + " | " + SRC["cases"], "policy"),
]

# exposure rules: ignore clauses where the owner says it did not happen
_GUARDED = {"DOG-XYLITOL", "DOG-GRAPES", "CAT-LILY", "CAT-FLOWERS", "CAT-PARACETAMOL", "DC-NSAID", "DC-ANTIFREEZE", "DC-RODENTICIDE",
            "DC-RODENTICIDE-BLEED", "DC-SNAKEBITE", "DC-METALDEHYDE", "DC-POISON-BAIT", "CAT-DOGFLEA", "DC-BATTERY", "DC-CORROSIVE",
            "DC-ALCOHOL", "DC-OTC-STIMULANT", "DC-RX-HUMAN", "DC-FLUOROURACIL", "DC-PLANT-SEVERE", "DC-PLANT-OTHER", "DOG-BREADDOUGH",
            "BIRD-AVOCADO", "DC-SALT"}
for _rule in RULES:
    if _rule.id in _GUARDED:
        _rule.neg_guard = True

# rules (plus the chocolate calculator, id DC-CHOCOLATE) that mean "the pet was exposed to a poison": used for the hand-off card
TOXIN_IDS = _GUARDED | {"DC-CHOCOLATE"}
BAIT_IDS = {"DC-POISON-BAIT", "DC-METALDEHYDE", "DC-RODENTICIDE"}


# ---- chocolate (dose-aware, from MSD figures) --------------------------------
_CHOC = re.compile(r"chocolat|\bchoc\b|cocoa|brownie|hershey|cadbury|lindt|milka|toblerone|kit ?kat|snickers|"
                   r"σοκολατ|κακαο|μπρουνι|μιλκα|παυλιδη|γαλαξια|λινδτ")
_TRACE = re.compile(r"crumb|lick|tiny|trace|a taste|just a (bite|bit|taste)|small bit|ψιχουλ|γλειψ|μια δαγκι|μικρο κομματακι")
_GRAMS = re.compile(r"(\d+(?:[.,]\d+)?) ?(?:g\b|gr\b|gram|γρ\b|γραμ)")
_WEIGHT = re.compile(r"(\d+(?:[.,]\d+)?) ?(?:kg|kilo|κιλ)")
# methylxanthines in mg per gram of chocolate (MSD)
_MGPG = (("cocoa powder|κακαο σκονη|σκονη κακαο", 28.5), ("baker|unsweetened|κουβερτουρα|ανευ ζαχαρης", 15.5),
         ("dark|semi|bitter|μαυρη|bittersweet|hershey", 5.5), ("milk|γαλακτος|milka|μιλκα|cadbury", 2.3),
         ("white|λευκη", 0.1))
_BIG = re.compile(r"\bbag\b|\bbox\b|\bpacks?\b|packets?|\bbars\b|whole|\blots?\b|many|several|πακετ|κουτι|ολοκληρ|πολλ")
_MID = re.compile(r"\bbar\b|squares?|pieces?|cake|brownie|πλακα|κομματ|τουρτα")


def _weight_kg(text, profile):
    w = (profile or {}).get("weight")
    try:
        w = float(str(w).replace(",", ".")) if w not in (None, "", 0) else None
    except ValueError:
        w = None
    if w and w > 0:
        return w
    m = _WEIGHT.search(text)
    return float(m.group(1).replace(",", ".")) if m else None


def chocolate_assessment(text, weight_kg=None):
    """Return (level or '', mg_per_kg or None, note) from normalized text."""
    if not _CHOC.search(text):
        return "", None, ""
    grams = None
    gm = _GRAMS.search(text)
    explicit = bool(gm)
    if gm:
        grams = float(gm.group(1).replace(",", "."))
    elif _TRACE.search(text):
        return "", None, "trace"
    elif _BIG.search(text):
        grams = 100.0
    elif _MID.search(text):
        grams = 40.0
    mgpg = 5.5  # unknown type: assume dark chocolate (the safer guess)
    for pat, val in _MGPG:
        if re.search(pat, text):
            mgpg = val
            break
    if grams is None or not weight_kg:
        return "URGENT", None, "unknown amount or weight"
    mgkg = grams * mgpg / weight_kg
    if explicit:
        lvl = "EMERGENCY" if mgkg >= 40 else "URGENT" if mgkg >= 20 else ""
    else:
        lvl = "EMERGENCY" if mgkg >= 40 else "URGENT"
    return lvl, mgkg, "explicit amount" if explicit else "assumed amount"


# ---- negation guard (exposure rules only) -----------------------------------------------------------------------
# "he did NOT eat the grapes" must not fire the grape rule, but "I'm not sure he ate grapes" must. A negated clause runs
# from the negation word to the next punctuation or "but/and", so a second, real exposure after "and" is still seen.
_NEG = re.compile(
    r"(?:\b(?:did ?n[o']?t|didn'?t|does ?n[o']?t|doesn'?t|do not|don'?t|never|not|no|without|hasn'?t|has not|haven'?t|have not|wasn'?t|was not|isn'?t|is not)\b|"
    r"\bδεν\b|\bουτε\b|\bμην\b)\s+(?:\w+\s+){0,2}?"
    r"(?:eat\w*|ate|eaten|swallow\w*|chew\w*|touch\w*|get|got|lick\w*|drank|drink\w*|take|took|taken|have|had|been|bit\w*|"
    r"εφαγ\w*|φαει|φαγε|καταπι\w*|μασησ\w*|ακουμπ\w*|ηπι\w*|γλειψ\w*|πηρε|δαγκ\w*|βρηκε)"
    r"[^.;,\n]*?(?=\bbut\b|\band\b|\bhowever\b|\bthough\b|\bthen\b|αλλα|\bκαι\b|ομως|[.;,\n]|$)")
_UNSURE = re.compile(r"\bsure\b|certain|\bknow\b|ξερω|βεβαι|\bthink|believe|νομιζ|maybe|might|perhaps|possib|ισως|wonder|worried|afraid|φοβαμαι|can'?t tell|cannot tell|not clear")


def strip_negated(text):
    """Remove clauses in which the owner says the exposure did NOT happen. Uncertain wording is kept (safer)."""
    def repl(m):
        window = text[max(0, m.start() - 20):m.end()]
        return " " if not _UNSURE.search(window) else m.group(0)
    return _NEG.sub(repl, text)


def evaluate(species_key, user_texts, profile=None):
    """Check every owner message of the current chat. Returns Result."""
    text = norm(" \n ".join(t for t in (user_texts or []) if t))
    sp = species_key or "other"
    hits = []
    if not text.strip():
        return Result()
    tg = strip_negated(text)
    for r in RULES:
        if r.species and sp not in r.species:
            continue
        t = tg if r.neg_guard else text
        if r.exclude and re.search(r.exclude, t):
            continue
        if all(p.search(t) for p in r.all_of):
            hits.append(Hit(r.id, r.level, r.en, r.el, r.source, r.basis, r.immediate))
    if sp in ("dog", "cat"):
        lvl, mgkg, note = chocolate_assessment(tg, _weight_kg(text, profile))
        if lvl:
            if mgkg is not None:
                en = (f"Chocolate: estimated {mgkg:.0f} mg/kg of methylxanthines ({note}); "
                      "about 20 mg/kg can cause mild signs and 40 mg/kg or more can affect the heart.")
                el = (f"Σοκολάτα: εκτιμώμενα {mgkg:.0f} mg/kg μεθυλοξανθινών ({note}); "
                      "περίπου 20 mg/kg προκαλούν ήπια συμπτώματα και 40 mg/kg ή περισσότερο μπορεί να επηρεάσουν την καρδιά.")
            else:
                en = "Chocolate eaten and the amount or weight is unknown: call a vet today and say how much and what kind."
                el = "Έφαγε σοκολάτα και η ποσότητα ή το βάρος είναι άγνωστα: κάλεσε κτηνίατρο σήμερα και πες πόση και τι είδους."
            hits.append(Hit("DC-CHOCOLATE", lvl, en, el, SRC["chocolate"], "msd", lvl == "EMERGENCY"))
    res = Result(hits=hits)
    if hits:
        res.level = max((h.level for h in hits), key=lambda x: RANK[x])
    return res




def outranks(floor_level, ai_level):
    """True when the rule floor is higher than the AI's final level."""
    return bool(floor_level) and RANK.get(floor_level, 0) > RANK.get(ai_level or "SELF_CARE", 0)


def prompt_hints(result):
    """Short English block appended to the nurse system prompt."""
    if not result.hits:
        return ""
    lines = ["SAFETY RULE ALERTS (deterministic checks on the owner's words; ask about these first, "
             "and do not end below the highest level shown):"]
    for h in sorted(result.hits, key=lambda x: -RANK[x.level]):
        flag = " [clear immediate danger: you may skip the question cycle]" if h.immediate and h.level == "EMERGENCY" else ""
        lines.append(f"- {h.id} -> at least {h.level}: {h.en}{flag}")
    return "\n".join(lines)


def floor_note(result, lang="en"):
    """One sentence appended to the reply when the floor overrides the AI level."""
    if not result.hits:
        return ""
    top = sorted(result.hits, key=lambda x: -RANK[x.level])[0]
    head = "⚠️ Κανόνας ασφαλείας: " if lang == "el" else "⚠️ Safety rule: "
    return head + (top.el if lang == "el" else top.en)
