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
| WikiVet | background | CC BY-SA (attribute, share alike) |
| PMC open access | citations | free |
| MSD Vet Manual | current base of `vet_rules.py` | paraphrase only |

Next step: map ESCCAP tick/leishmania pages to rules (DOG-TICK-FEVER, DOG-LEISHMANIA, DC-TICK-PARALYSIS) and add the source URL to each; vet reviews every `basis="policy"` rule.

## ESCCAP GL3 (ectoparasites) — read and applied
Read: https://www.esccap.org/uploads/docs/cgqtqpf1_0720_ESCCAP_GL3__English_v19_1p.pdf (general to southern Europe; no Greece-only data).
- Brown dog tick (*Rhipicephalus sanguineus*) is the main southern-Europe tick; it carries *Ehrlichia canis*, *Babesia vogeli*, *Hepatozoon canis*, *Rickettsia conorii*. Lyme (*Ixodes*) is mainly a northern problem. → `vet_knowledge.py` "ticks" topic updated (removal: tool, no oil/alcohol/ether; remove ticks promptly; cats get ticks; no dog-only permethrin on cats).
- Sand flies (*Phlebotomus*) transmit *Leishmania infantum*; prevention = repellent insecticides all season, keep dogs indoors after dusk. The guideline lists no clinical signs (see ESCCAP GL5, not yet read) → `DOG-LEISHMANIA` signs still rest on MSD.
- Still to do: read GL5 (vector-borne diseases) for signs and the cat section; GL1/GL5 worms and heartworm (*Dirofilaria*), which the rules do not cover yet.
- This is still not vet-reviewed.
