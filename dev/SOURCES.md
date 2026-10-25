# Source register — PetsAIHealth (pets)

Rule for every rule: **a source URL and a vet sign-off** (`reviewed_by`). Paraphrase and cite; check the licence before reuse.

| Source | Use | Note |
|---|---|---|
| ESCCAP guidelines | ticks, fleas, worms, leishmania; fits Greece better than MSD | free; **first target for the Greek parasite rules** |
| WSAVA guidelines | vaccination, nutrition, pain, dental | free |
| ISFM consensus statements | cats | free |
| AAHA | some free guidelines | check each |
| RECOVER (ACVECC) | CPR and triage | evidence-based |
| ASPCA Animal Poison Control | toxic plant and food lists | free |
| FEDIAF | EU pet nutrition | free |
| VetCompass (Royal Veterinary College) | what dogs and cats actually present with; check rule thresholds | open-access papers |
| WikiVet | background | **CC BY-NC-ND 3.0** (read on the site footer): no commercial use, no adaptation: cite and link only. Earlier note said CC BY-SA; corrected. |
| PMC open access | citations | free |
| MSD Vet Manual | current base of `vet_rules.py` | paraphrase only |

Next step: map ESCCAP tick/leishmania pages to rules (DOG-TICK-FEVER, DOG-LEISHMANIA, DC-TICK-PARALYSIS) and add the source URL to each; vet reviews every `basis="policy"` rule.

## ESCCAP GL3 (ectoparasites) — read and applied
Read: https://www.esccap.org/uploads/docs/cgqtqpf1_0720_ESCCAP_GL3__English_v19_1p.pdf (general to southern Europe; no Greece-only data).
- Brown dog tick (*Rhipicephalus sanguineus*) is the main southern-Europe tick; it carries *Ehrlichia canis*, *Babesia vogeli*, *Hepatozoon canis*, *Rickettsia conorii*. Lyme (*Ixodes*) is mainly a northern problem. → `vet_knowledge.py` "ticks" topic updated (removal: tool, no oil/alcohol/ether; remove ticks promptly; cats get ticks; no dog-only permethrin on cats).
- Sand flies (*Phlebotomus*) transmit *Leishmania infantum*; prevention = repellent insecticides all season, keep dogs indoors after dusk. The guideline lists no clinical signs (see ESCCAP GL5, not yet read) → `DOG-LEISHMANIA` signs still rest on MSD.
- Still to do: read GL5 (vector-borne diseases) for signs and the cat section; GL1/GL5 worms and heartworm (*Dirofilaria*), which the rules do not cover yet.
- This is still not vet-reviewed.

## What was actually read (2026-10-25) — licence terms and findings
| Source | Read | Result that changes how we use it |
|---|---|---|
| ESCCAP GL5 (vector-borne, 2024) | full PDF | © ESCCAP, all rights reserved, redistribution needs written permission: **paraphrase and cite, never copy**. Facts used: leishmaniosis endemic in southern Europe, Greece needs year-round sand-fly protection, season April–November, repellent collars/spot-ons, permethrin never on cats; heartworm (*D. immitis*) endemic in southern Europe incl. Greece, monthly preventives May–late November, test first; signs of babesiosis, ehrlichiosis, anaplasmosis. Now in `vet_knowledge.py` topic `med_parasites`. |
| ESCCAP GL3 (ectoparasites) | PDF | see section above |
| WSAVA guidelines | list page + 2024 vaccination PDF | © WSAVA, all rights reserved. Core vaccines dog: distemper, adenovirus, parvovirus; cat: panleukopenia, calicivirus, herpesvirus; rabies/leptospirosis/FeLV conditional; last puppy/kitten dose at 16+ weeks. No leishmania vaccine mention in the part read. Not used in rules yet. |
| FEDIAF nutritional guidelines 2025 | download page | Free to download, but **commercial use prohibited without FEDIAF's written permission**. Cross-check only; do not copy tables into the product. |
| ASPCA toxic plants | list page | © ASPCA, all rights reserved, no licence stated. Use as a cross-check of our plant rules; do not copy the list. |
| VetCompass (RVC) | landing page | Publishes open research via a Learn Zone library; no reuse terms on the page. Not yet used to check thresholds. |
| AAFP / ISFM / AAHA | AAFP guidelines list | List found (2024 NSAIDs in cats, 2022 antimicrobial stewardship, 2021 life stage, 2020 vaccination, 2015 pain...). Free-download status and reuse terms unknown: not read. |
| RECOVER | search + eScholarship abstract | Found the 2024 BLS guidelines abstract (favours bag-mask over mouth-to-nose when not intubated; continuous compressions). Full text/licence not read. |
| WikiVet | main page footer | CC BY-NC-ND 3.0: cite/link only, never paraphrase into the product. |
| AAHA | 2021 feline life-stage page | © AAHA; downloads may be members only; page text says routine wellness exams (young adult, 7-10 mature, >10 senior) and vaccines; nothing on pain or symptom triage. Terms of Use page not read. |

### Cross-check of existing rules against ESCCAP GL5 (for the vet)
- DOG-LEISHMANIA: signs match (skin, nails, weight loss, nosebleed, drinking/peeing more). ESCCAP also lists swollen lymph nodes, eye inflammation and lameness; the trigger does not include swollen lymph nodes or eye signs yet.
- DC-HEARTWORM-SIGNS exists (MSD); ESCCAP adds that cats can die suddenly and that Greece is endemic. No change made.
- DOG-TICK-FEVER: ESCCAP babesiosis signs include jaundice and "rusty" urine, ehrlichiosis includes petechiae, nosebleeds, blood in urine or stool; consistent with the rule's "go now" signs.
- Still not vet-reviewed.

### Retry (same day)
- Europe PMC blocked by robots.txt; PMC article pages show a reCAPTCHA; RECOVER 2012 full text still not read (only the 2024 BLS abstract).
- AAHA: only the life-stage page read (see table). Free-download status for other AAHA/AAFP guidelines still unknown.
