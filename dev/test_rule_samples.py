"""One English and one Greek owner message per rule must fire that rule; near-miss messages must not.
Run:  python3 -I dev/test_rule_samples.py   (no deps). Samples live in dev/rule_samples.json."""
import json, os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
import vet_rules as vr

S = {x["id"]: x for x in json.load(open(os.path.join(ROOT, "dev", "rule_samples.json"), encoding="utf-8"))}
ids = [r.id for r in vr.RULES]
bad = []
for i in ids:
    if i not in S:
        bad.append(f"{i}: no sample"); continue
    x = S[i]; sp = x["species"]
    prof = {"weight": 5} if i == "DC-CHOCOLATE" else {}
    for lang in ("en", "el"):
        if i not in [h.id for h in vr.evaluate(sp, [x[lang]], prof).hits]:
            bad.append(f"{i}: {lang} sample does not fire: {x[lang][:70]}")
    for k in ("neg", "neg_el"):
        if x.get(k) and i in [h.id for h in vr.evaluate(sp, [x[k]], prof).hits]:
            bad.append(f"{i}: {k} near miss fires: {x[k][:70]}")
for i in S:
    if i not in ids: bad.append(f"{i}: sample for unknown rule")
print(f"{len(ids)} rules, {len(S)} samples, {len(bad)} problems")
for b in bad: print("  ", b)
sys.exit(1 if bad else 0)
