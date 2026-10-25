# PetsAIHealth — AI Vet Nurse for pet parents in Greece

AI nurse chat that asks about the symptoms, explains how urgent they are and prepares a report for the vet, plus tools
(vitals, photo, lab results, longevity, diary, vet finder, insurance). Greek first, English supported. Built on Claude
(Anthropic) with references from the MSD Veterinary Manual. It supports your vet and does not replace them.

## Safety layers

The AI does not decide alone. A deterministic floor sits under the chat and can only **raise** the urgency, never lower it:

- **178 rules** (Greek and English, dogs, cats, rabbits, birds, reptiles, small pets) written from MSD Veterinary Manual pages
  (`vet_rules.py`). Each rule has a source or is marked `policy` (written by us, still waiting for a veterinarian to review it).
- **Immediate emergency message** for a short list of clear life-threatening situations (collapse, blue gums, breathing trouble,
  confirmed toxins, blocked urethra, snakebite...): the app shows a fixed "go to a vet now" message with the nearest 24h clinic
  links without waiting for the AI.
- Owner's own words are also read by a second AI call that extracts facts for the same rules, with age, condition and vitals
  floors, and a fail-safe: if the AI is down the owner gets an urgent message, never an error or an all-clear.
- Opt-in follow-up reminder email after an urgent or mild verdict (no symptoms in the mail).
- Code-only safety log (rule ids, no text or personal data) reviewed weekly.

Status: the rules are **not yet reviewed by a veterinarian**. `dev/rule_audit_notes.md` lists the points for the reviewer.

```
python3 -I dev/test_vet_rules.py        # 283 cases
python3 -I dev/test_rule_samples.py     # one English + one Greek message per rule, plus near misses
python3 -I dev/test_vet_safety.py
python3 -I dev/test_vet_knowledge.py
python3 -I dev/run_vet_benchmark.py     # labelled seed cases (not clinically validated)
python3 -I dev/e2e_safety.py            # real chat handler, AI faked
```

## Benchmark

[![VetTriageBench-45](https://img.shields.io/badge/VetTriageBench--45-v1.0-blue)](https://github.com/chiinsurancebrokers/VetTriageBench-45)

VetTriageBench-45 is an open benchmark of 45 dog and cat vignettes. These results are for the **AI model alone** (no safety
rules), run on the models and date shown, so they do not describe the app as it runs today. The 45 answers were drafted with
AI help and checked against the MSD manual but not yet validated by a team of vets. Not a clinical study.

| Model | Accuracy (95% CI) | Unsafe undertriage |
|---|---|---|
| claude-sonnet-4-6 | 73.3% [59–84%] | 0% |
| gpt-4o | 80.0% [66–89%] | 2.2% |

→ [Full results & methodology](https://github.com/chiinsurancebrokers/VetTriageBench-45)

## References

- Semigran et al. BMJ 2015;351:h3480
- Ruys et al. J Vet Emerg Crit Care 2012;22:303-312
- Groesser et al. J Vet Emerg Crit Care 2025. doi:10.1111/vec.70068
- Wong et al. Vet Record 2026;198(2):e46-e53
- MSD Veterinary Manual — msdvetmanual.com

See `CLAUDE.md` for developer notes (screens, plans, deploys, safety details).
