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
    ("cat", "hasn't eaten for 2 days", None, "URGENT"),
    ("dog", "ate a few grapes an hour ago", None, "EMERGENCY"),
    ("dog", "had a seizure that lasted 5 minutes", None, "EMERGENCY"),
    ("dog", "licking paw a lot, red between toes", None, None),
    ("cat", "she is very lethargic and her gums look pale", None, "EMERGENCY"),
    ("dog", "licked a crumb of chocolate cake off the floor, she's 30 kg", None, None),
    ("cat", "he peed outside the box twice and is drinking much more water than usual", None, "URGENT"),
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
    # --- rules added from the MSD pet-owner pages
    ("dog", "a viper bit my dog on the leg while hiking", None, "EMERGENCY"),
    ("dog", "τον δάγκωσε φίδι στο πόδι", None, "EMERGENCY"),
    ("cat", "we saw a snake in the garden but the cat is fine", None, None),
    ("dog", "she ate slug pellets from the garden shed", None, "EMERGENCY"),
    ("dog", "έφαγε δόλωμα για σαλιγκάρια", None, "EMERGENCY"),
    ("dog", "I think someone left poisoned bait in the park and he ate a sausage there", None, "EMERGENCY"),
    ("dog", "έφαγε δηλητηριασμένο κεφτέ στον δρόμο", None, "EMERGENCY"),
    ("cat", "I put the dog flea drops on my cat by mistake", None, "EMERGENCY"),
    ("cat", "έβαλα σταγόνες για σκύλους στη γάτα", None, "EMERGENCY"),
    ("cat", "I put the cat flea drops on the cat, now she is licking", None, None),
    ("dog", "he swallowed a button battery", None, "EMERGENCY"),
    ("dog", "the remote battery is dead and the dog is playing", None, None),
    ("dog", "he drank some bleach from the bucket", None, "URGENT"),
    ("cat", "έφαγε χλωρίνη", None, "URGENT"),
    ("dog", "she licked up a glass of wine", None, "URGENT"),
    ("dog", "he ate my sudafed tablets", None, "URGENT"),
    ("dog", "ate two of my sertraline pills", None, "URGENT"),
    ("dog", "έφαγε χάπια για την πίεση", None, "URGENT"),
    ("dog", "he got into the 5-fluorouracil cream and ate it", None, "EMERGENCY"),
    ("dog", "chewed an oleander branch in the garden", None, "EMERGENCY"),
    ("cat", "μάσησε πικροδάφνη", None, "EMERGENCY"),
    ("dog", "ate some of the azalea", None, "EMERGENCY"),
    ("dog", "he chewed the dieffenbachia leaf", None, "URGENT"),
    ("dog", "ate a cannabis edible", None, "URGENT"),
    ("dog", "he ate the raw bread dough I left to rise", None, "URGENT"),
    ("dog", "we baked bread today and he is sleeping", None, None),
    ("bird", "my parrot ate some avocado", None, "EMERGENCY"),
    ("bird", "my parrot ate some seeds and chirps", None, None),
    ("dog", "he ate a lot of salt dough from the craft table", None, "URGENT"),
    ("dog", "he is choking on something, pawing at his mouth", None, "EMERGENCY"),
    ("dog", "we use a choke chain on walks and he walks well", None, None),
    ("dog", "there is blood in his diarrhea since this morning", None, "URGENT"),
    ("cat", "έκανε εμετό με αίμα", None, "URGENT"),
    ("dog", "my 10 week old puppy has vomiting and bloody diarrhea", None, "EMERGENCY"),
    ("dog", "he was vaccinated for parvo last week and is playing", None, None),
    ("dog", "he swallowed a sock yesterday", None, "URGENT"),
    ("cat", "η γάτα κατάπιε κλωστή", None, "URGENT"),
    ("dog", "he ate rat poison and has bloody diarrhea", None, "EMERGENCY"),
    # --- negation guard: exposure that did NOT happen must not fire; uncertainty must
    ("dog", "he did not eat the grapes, I checked the bowl", None, None),
    ("dog", "δεν έφαγε σταφίδες", None, None),
    ("dog", "I'm not sure but I think he ate grapes", None, "EMERGENCY"),
    ("dog", "he didn't eat the chocolate, only the wrapper, he's 20kg", None, None),
    ("dog", "he did not eat anything but he ate grapes earlier", None, "EMERGENCY"),
    ("dog", "he ate grapes and has no vomiting so far", None, "EMERGENCY"),
    ("cat", "she never touched the lily, it is out of reach", None, None),
    ("dog", "he wasn't bitten by the snake, it ran away", None, None),
    ("dog", "he is playing and did not get into the rat poison", None, None),
    ("dog", "didn't eat xylitol gum", None, None),
    # --- small mammals ("other")
    ("other", "my guinea pig has stopped eating since this morning", None, "URGENT"),
    ("other", "το ινδικό χοιρίδιο δεν τρώει", None, "URGENT"),
    ("other", "my hamster has wet tail and he is only 5 weeks old", None, "EMERGENCY"),
    ("other", "my hamster has diarrhea", None, "URGENT"),
    ("other", "my guinea pig is wheezing and has a runny nose", None, "URGENT"),
    ("other", "my ferret is weak and dragging his back legs", None, "EMERGENCY"),
    ("other", "το κουνάβι σέρνει τα πίσω πόδια", None, "EMERGENCY"),
    ("other", "my ferret has been vomiting and has black tarry stool", None, "URGENT"),
    ("other", "my guinea pig has swollen joints and is limping", None, "URGENT"),
    ("other", "his rectum is sticking out", None, "EMERGENCY"),
    ("other", "my hamster is running on the wheel and eating well", None, None),
    ("dog", "he is not eating and has diarrhea", None, None),     # small-mammal rules never fire on dogs
    # --- gaps found by running real MSD case-study presentations through the rules
    ("cat", "he is pressing his head against the wall and is disoriented", None, "URGENT"),
    ("dog", "he keeps circling and stumbling", None, "URGENT"),
    ("cat", "belly is swollen and she has lost weight and is lethargic", None, "URGENT"),
    ("cat", "she is playing and her belly looks a bit round after dinner", None, None),
    ("cat", "she has been vomiting for 3 to 4 days and is not drinking", None, "URGENT"),
    ("dog", "he vomited once two days ago and is fine since", None, None),
    ("dog", "diarrhea for several days", None, "URGENT"),
    ("dog", "there is blood in his urine", None, "URGENT"),
    ("cat", "αίμα στα ούρα της γάτας", None, "URGENT"),
    ("dog", "he fell while jumping, yelped and now won't put weight on his leg", None, "URGENT"),
    ("dog", "limping slightly on the back leg since yesterday", None, None),
    ("dog", "our 2 month old puppy is lethargic and vomited after the dewormer", None, "URGENT"),
    ("dog", "our puppy is playful and eating well", None, None),
    ("dog", "ο σκύλος κρατάει ψηλά το πόδι και δεν πατάει", None, "URGENT"),
    # second MSD case batch
    ("dog", "she woke up and cannot walk at all", None, "EMERGENCY"),
    ("dog", "he struggles to walk a bit after the long hike", None, None),
    ("dog", "severe nosebleed, blood sprays from his nose when he sneezes", None, "EMERGENCY"),
    ("cat", "her gums and skin look yellow", None, "URGENT"),
    ("dog", "he has not wanted to eat for a week", None, "URGENT"),
    ("dog", "he skipped breakfast before the surgery, not eating since last night", None, None),
    ("dog", "bite wounds from a fight are not healing", None, "URGENT"),
    ("dog", "a lump on her side has burst open and is oozing", None, "URGENT"),
    ("dog", "he is straining to urinate since this morning", None, "URGENT"),
    ("dog", "σηκωθηκε και δεν μπορει να περπατησει", None, "EMERGENCY"),
    ("cat", "κιτρινο δερμα και ουλα", None, "URGENT"),
    # MSD veterinary emergency-medicine pages
    ("dog", "a stick went into his eye and it is punctured", None, "EMERGENCY"),
    ("cat", "her eye is red and cloudy and she keeps it closed", None, "URGENT"),
    ("dog", "he suddenly went blind and is bumping into furniture", None, "URGENT"),
    ("dog", "my cat scratched her eye yesterday", None, "URGENT"),
    ("dog", "he fell down the stairs but is walking fine", None, "URGENT"),
    ("dog", "got bitten in a fight and the neck is swollen", None, "EMERGENCY"),
    ("dog", "the bite wound on his leg is clean and he is playful", None, "URGENT"),
    ("cat", "το ματι ειναι κοκκινο και θολο", None, "URGENT"),
    # MSD urinary + musculoskeletal pages
    ("dog", "he squats and strains but only a few drops come out", None, "EMERGENCY"),
    ("dog", "he has not peed since yesterday morning", None, "EMERGENCY"),
    ("dog", "she has blood in her urine and is vomiting and very weak", None, "EMERGENCY"),
    ("cat", "she keeps peeing outside the litter box in small amounts", None, "URGENT"),
    ("cat", "he peed normally this morning and is playful", None, None),
    ("dog", "the bone is sticking out of the skin on his leg", None, "EMERGENCY"),
    ("dog", "I think his leg is broken, it is dangling", None, "URGENT"),
    ("dog", "his knee is hot and swollen and he suddenly went lame this morning", None, "URGENT"),
    ("dog", "his knee has been swollen for two months, he walks fine", None, None),
    ("dog", "after exercise his legs went stiff and rigid and his urine is dark brown", None, "EMERGENCY"),
    ("cat", "her neck is drooping and she is suddenly weak", None, "URGENT"),
    # MSD toxicology pages
    ("dog", "he ate a handful of macadamia nuts", None, "URGENT"),
    ("dog", "he did not eat any macadamia nuts", None, None),
    ("cat", "she ate a piece of raw onion", None, "URGENT"),
    ("dog", "he swallowed a mothball", None, "URGENT"),
    ("cat", "she licked tea tree oil that spilled on the floor", None, "EMERGENCY"),
    ("dog", "he licked some essential oil that spilled", None, "URGENT"),
    ("dog", "he ate bromethalin rat bait but seems fine", None, "EMERGENCY"),
    ("dog", "he ate a cannabis edible gummy", None, "URGENT"),
    ("dog", "he pulled weeds in the garden with me", None, None),
    ("cat", "she chewed a nicotine patch", None, "URGENT"),
    ("dog", "he bit into a laundry pod", None, "URGENT"),
    ("dog", "there was a house fire and we got him out", None, "EMERGENCY"),
    ("bird", "my bird was near a non-stick pan that overheated and smoked", None, "EMERGENCY"),
    ("dog", "τσιγαρο εφαγε ο σκυλος", None, "URGENT"),
    # MSD quiz check
    ("dog", "his breathing is noisy and high-pitched when he breathes in", None, "URGENT"),
    ("cat", "she has a wheeze when she breathes", None, "URGENT"),
    ("dog", "he is panting after a walk, normal breathing otherwise", None, None),
    ("dog", "he has been vomiting and has diarrhea, many times since last night", None, "URGENT"),
    ("dog", "he vomited once and has soft stool, still playful", None, None),
    # full MSD quiz sweep
    ("dog", "she whelped 2 weeks ago and is trembling and panting and restless", None, "EMERGENCY"),
    ("dog", "she is panting after her walk, no puppies, she is fine", None, None),
    ("cat", "my cat is breathing fast even while sleeping", None, "URGENT"),
    ("cat", "my cat is purring and sleeping calmly", None, None),
    ("dog", "he has a goose honk cough that is getting worse", None, "URGENT"),
    ("dog", "he vomits everything, even water, since this morning", None, "URGENT"),
    ("dog", "he is drinking much more and has lost weight but eats a lot", None, "URGENT"),
    ("dog", "he drinks more water in summer, nothing else is different", None, None),
    ("cat", "she is ravenous all day but losing weight", None, "URGENT"),
    ("dog", "he yelps when I touch his neck and will not move his head", None, "URGENT"),
    ("dog", "he is a bit stiff after a long hike and ate well", None, None),
    # MSD reproductive pages
    ("dog", "she is not spayed, had a heat last month, now has pus discharge and is lethargic and drinking a lot", None, "EMERGENCY"),
    ("dog", "she is unspayed and has a yellow pus-like discharge but is bright and eating", None, "URGENT"),
    ("dog", "she is in heat with a bloody discharge, bright and eating", None, None),
    ("dog", "she gave birth yesterday and has a foul smelling discharge", None, "EMERGENCY"),
    ("dog", "she is nursing and one mammary gland is hard, hot and painful", None, "URGENT"),
    ("dog", "he is scratching his anal gland area", None, None),
    ("dog", "she has been pushing for more than 30 minutes and no puppy has come", None, "EMERGENCY"),
    ("dog", "she is 75 days pregnant and no signs of labour", None, "EMERGENCY"),
    ("dog", "his penis is stuck out of the sheath and swollen", None, "EMERGENCY"),
    ("dog", "his erection will not go down for hours", None, "EMERGENCY"),
    ("dog", "his scrotum is swollen and hot", None, "EMERGENCY"),
    ("dog", "she aborted her puppies last night", None, "URGENT"),
    ("dog", "there is pink tissue bulging from her vulva", None, "URGENT"),
    ("dog", "ο σκυλος εχει πρησμενο οσχεο", None, "EMERGENCY"),
    # MSD digestive / respiratory / circulatory / neuro pass
    ("dog", "he ate a chicken bone and is drooling and gagging", None, "EMERGENCY"),
    ("cat", "our kitten is vomiting and won't eat, not vaccinated", None, "EMERGENCY"),
    ("cat", "my cat has not eaten since yesterday", None, "URGENT"),
    ("dog", "his belly is swollen and hard since the surgery last week", None, "EMERGENCY"),
    ("dog", "she has black tarry stool", None, "URGENT"),
    ("dog", "his anus area is red and swollen and draining pus", None, "URGENT"),
    ("dog", "she keeps regurgitating food and now has a cough", None, "EMERGENCY"),
    ("dog", "he inhaled vomit last night but seems fine", None, "URGENT"),
    ("dog", "she won't lie down and is breathing fast", None, "EMERGENCY"),
    ("dog", "he has noisy harsh breathing and gums look blue", None, "EMERGENCY"),
    ("cat", "our kitten is sneezing with a runny nose and won't eat", None, "URGENT"),
    ("cat", "suddenly cannot use her back legs and they feel cold", None, "EMERGENCY"),
    ("dog", "he fainted this morning but is fine now", None, "EMERGENCY"),
    ("dog", "there are tiny red spots on her gums", None, "URGENT"),
    ("dog", "he suddenly went blind overnight", None, "URGENT"),
    ("dog", "stiff neck and fever and not eating", None, "EMERGENCY"),
    ("dog", "found a tick and now her back legs are wobbly", None, "EMERGENCY"),
    ("dog", "he has a stiff jaw and spasms after a deep puncture wound", None, "EMERGENCY"),
    ("other", "my ferret is straining to pee", None, "EMERGENCY"),
    ("bird", "the budgie is fluffed up on the cage floor", None, "EMERGENCY"),
    ("dog", "my dog is bright and eating and has one small tick on his ear", None, None),
    ("dog", "he is happy, eating well and has a normal bowel movement", None, None),
    ("dog", "she had ticks last week and now has dark urine, pale gums and is weak", None, "EMERGENCY"),
    ("dog", "the vet said heartworm and he coughs and tires easily", None, "URGENT"),
    ("reptile", "my tortoise is stargazing with its neck twisted", None, "URGENT"),
    # MSD eye/ear/endocrine pass
    ("dog", "his eye popped out of the socket after a fight", None, "EMERGENCY"),
    ("dog", "her left eye is red and cloudy and she is squinting and pawing at it", None, "EMERGENCY"),
    ("dog", "I saw tiny white worms moving on his eye", None, "URGENT"),
    ("dog", "her ear flap is swollen like a balloon after shaking her head", None, "URGENT"),
    ("dog", "he has an ear infection and now a head tilt, is lethargic and not eating", None, "EMERGENCY"),
    ("dog", "a grass seed is stuck in his ear and he keeps shaking his head and crying", None, "URGENT"),
    ("dog", "he is diabetic and has started vomiting and won't eat", None, "EMERGENCY"),
    ("dog", "we gave a double dose of insulin by mistake", None, "EMERGENCY"),
    ("dog", "he has Addison's disease and is vomiting", None, "EMERGENCY"),
    ("cat", "I gave her a Fleet enema for constipation", None, "EMERGENCY"),
    ("dog", "she keeps rubbing her face and her ears twitch", None, "URGENT"),
    ("dog", "my diabetic dog gets insulin twice a day and is eating well and playing", None, None),
    # MSD first-aid / skin / pharmacology pass
    ("dog", "he ate a wild mushroom on our walk but seems fine", None, "EMERGENCY"),
    ("dog", "we put shop bought mushrooms in the pasta and he ate a bit", None, None),
    ("dog", "she fell into the pool and went under water for a minute", None, "EMERGENCY"),
    ("cat", "the kitten chewed a live phone charger cable", None, "EMERGENCY"),
    ("dog", "he found it cold to the touch, wet and weak after the snow", None, "EMERGENCY"),
    ("dog", "she was stung by a wasp on the face and the muzzle is swollen", None, "URGENT"),
    ("dog", "his face is swollen and he is vomiting and drooling after the vaccine", None, "EMERGENCY"),
    ("dog", "he swam in a stagnant pond and is lethargic and not eating", None, "URGENT"),
    ("dog", "a bat bit the dog in the garden", None, "URGENT"),
    ("dog", "he got a burn on his paw from the hot pavement and the pad is red and raw", None, "URGENT"),
    ("dog", "there are maggots in the wound on his back", None, "EMERGENCY"),
    ("rabbit", "the vet gave amoxicillin tablets to my rabbit and now he is bloated", None, "EMERGENCY"),
    ("rabbit", "I used a fipronil flea spot-on on my rabbit", None, "EMERGENCY"),
    ("dog", "our collie got ivermectin horse paste and is stumbling and drooling", None, "EMERGENCY"),
    # MSD immune / infectious pass
    ("dog", "he had a tick two weeks ago and now has a fever and is lethargic", None, "URGENT"),
    ("dog", "scaly skin with hair loss on his ears and face and he is losing weight", None, "URGENT"),
    ("cat", "my cat has a swollen belly, lost weight and has a fever", None, "EMERGENCY"),
    ("cat", "our newborn kitten is cold and not nursing", None, "EMERGENCY"),
    ("dog", "the 3 week old puppy is crying nonstop and weak", None, "EMERGENCY"),
    ("bird", "my budgie has eye discharge, fluffed feathers and green droppings and is sleepy", None, "EMERGENCY"),
    ("dog", "he is a 3 year old dog who is playful and eating, one tick found and removed", None, None),
    # MSD exotic / small pet pass
    ("rabbit", "my rabbit is in the hot sun on the balcony and lying stretched out, breathing fast", None, "EMERGENCY"),
    ("other", "my guinea pig has trouble breathing and is wheezing", None, "EMERGENCY"),
    ("rabbit", "she is on antibiotics and now has diarrhoea", None, "EMERGENCY"),
    ("other", "my hamster has a wet tail and is hunched and not eating", None, "EMERGENCY"),
    ("bird", "I overheated a non-stick pan and the bird is near", None, "EMERGENCY"),
    ("bird", "the parrot has tremors and clenched feet", None, "EMERGENCY"),
    ("reptile", "my tortoise has bubbles at the nose and an open mouth", None, "EMERGENCY"),
    ("other", "my hedgehog feels cold and is not moving", None, "EMERGENCY"),
    ("rabbit", "my rabbit is hopping around happily, eating hay and it is a cool day", None, None),
    ("dog", "her gums are yellow and she collapsed this morning", None, "EMERGENCY"),
    ("cat", "κιτρινα ουλα και δεν σηκωνεται", None, "EMERGENCY"),
    ("dog", "his eyes look a bit yellow but he is playing and eating", None, "URGENT"),
    ("dog", "my dog was bitten by another dog on the leg", None, "URGENT"),
    ("cat", "η γατα δαγκωθηκε, υπαρχει δαγκωμα στο ποδι", None, "URGENT"),
    ("dog", "he bit into his chew toy", None, None),
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
# act-now bypass: fixed emergency message for clear life-threatening statements only
def _hits(sp, txt):
    return vr.act_now_hits(vr.evaluate(sp, [txt]))
assert any(h.id == "ALL-COLLAPSE" for h in _hits("dog", "he just collapsed and will not wake")), "collapse should bypass"
assert any(h.id == "DOG-GRAPES" for h in _hits("dog", "she ate a handful of grapes an hour ago")), "grapes should bypass"
assert not _hits("dog", "he is vomiting since this morning but bright and eating"), "mild vomiting must not bypass"
assert not _hits("dog", "she did not eat the grapes"), "negated exposure must not bypass"
assert not _hits("dog", "my dog was bitten by another dog on the leg"), "URGENT-only rules must not bypass"
_r1 = vr.act_now_reply(_hits("dog", "he just collapsed and will not wake"), "en")
assert _r1.startswith("🚨") and "do not wait for me" in _r1
_r2 = vr.act_now_reply(_hits("dog", "he just collapsed and will not wake"), "el")
assert _r2.startswith("🚨") and "ΑΜΕΣΩΣ" in _r2
for _i in vr.ACT_NOW:
    if _i != "DC-CHOCOLATE":
        assert any(r.id == _i and r.level == "EMERGENCY" for r in vr.RULES), "ACT_NOW id is not an EMERGENCY rule: " + _i
# every rule has both languages and msd rules have a source
for rule in vr.RULES:
    assert rule.en and rule.el, rule.id
    assert rule.level in ("URGENT", "EMERGENCY"), rule.id
    assert rule.basis == "policy" or rule.source.startswith("http"), rule.id
print(f"\n{len(CASES)} cases, {fails} failures, {len(vr.RULES)} rules + chocolate calculator")
sys.exit(1 if fails else 0)
