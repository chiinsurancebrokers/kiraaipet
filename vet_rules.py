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
_INGEST = (r"\b(ate|eaten|eats|eating|swallowed?|ingest\w*|chew\w*|nibbl\w*|licked|stole|stolen|took|taken|gave|given)\b|got into|got hold of|"
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
         _r(r"(labou?r|giving birth|whelping|queening|straining).{0,40}(hours?|no (puppy|kitten)|stuck|green discharge)|"
            r"τοκετ.{0,30}(ωρες|κολλησε|πρασιν)|γεννα\w*.{0,30}(ωρες|κολλησε)"),
         "Prolonged or stalled labour is an emergency.",
         "Παρατεταμένος ή σταματημένος τοκετός είναι επείγον.",
         "", "policy", immediate=True),
]


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


def evaluate(species_key, user_texts, profile=None):
    """Check every owner message of the current chat. Returns Result."""
    text = norm(" \n ".join(t for t in (user_texts or []) if t))
    sp = species_key or "other"
    hits = []
    if not text.strip():
        return Result()
    for r in RULES:
        if r.species and sp not in r.species:
            continue
        if r.exclude and re.search(r.exclude, text):
            continue
        if all(p.search(text) for p in r.all_of):
            hits.append(Hit(r.id, r.level, r.en, r.el, r.source, r.basis, r.immediate))
    if sp in ("dog", "cat"):
        lvl, mgkg, note = chocolate_assessment(text, _weight_kg(text, profile))
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
