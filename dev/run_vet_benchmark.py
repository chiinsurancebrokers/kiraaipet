"""Score the deterministic safety floor against a labelled case file.

    python3 -I dev/run_vet_benchmark.py [dev/vet_cases.jsonl]

Each line: {id, species, lang, text, weight_kg, truth, needs_rule, reviewed_by, note}
  truth        EMERGENCY | URGENT | SELF_CARE (the correct triage level)
  needs_rule   true when a deterministic rule is expected to reach `truth`; false when the rule must stay silent (SELF_CARE)
               or the case is for the AI to judge (note "ai-only": reported, never fails the run)
  reviewed_by  null for the seed set written from MSD pages (NOT clinically validated); a vet's name once labelled

The floor only raises, so it is scored on two things:
  UNDER  = needs_rule and the floor is below truth       (a missed red flag)      -> fails the run
  OVER   = the floor is above truth                      (a false alarm)           -> fails the run
Exit code 1 on any UNDER or OVER. Cases with note "ai-only" are listed as AI-dependent and do not affect the exit code.
"""
import json, os, sys
from collections import defaultdict
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
import vet_rules as vr
import vet_safety as vs

path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "dev", "vet_cases.jsonl")
cases = [json.loads(l) for l in open(path, encoding="utf8") if l.strip()]
rank = vr.RANK
stats = defaultdict(lambda: {"n": 0, "exact": 0, "under": 0, "over": 0, "ai_only": 0})
bad = []
for c in cases:
    prof = {"weight": c["weight_kg"]} if c.get("weight_kg") else {}
    res, _raw = vs.evaluate_all(c["species"], [c["text"]], prof, None, None)
    got = res.level or "SELF_CARE"
    t = c["truth"]
    st = stats[c["species"]]
    st["n"] += 1
    if c.get("note") == "ai-only":
        st["ai_only"] += 1
        continue
    if got == t:
        st["exact"] += 1
    if rank[got] > rank[t]:
        st["over"] += 1; bad.append(("OVER ", c, got, [h.id for h in res.hits]))
    elif c["needs_rule"] and rank[got] < rank[t]:
        st["under"] += 1; bad.append(("UNDER", c, got, [h.id for h in res.hits]))
    elif rank[got] < rank[t]:
        pass  # AI judges this one
print(f"{'species':9}{'cases':>6}{'exact':>7}{'under':>7}{'over':>6}{'ai-only':>9}")
tot = defaultdict(int)
for sp, st in sorted(stats.items()):
    print(f"{sp:9}{st['n']:6}{st['exact']:7}{st['under']:7}{st['over']:6}{st['ai_only']:9}")
    for k, v in st.items(): tot[k] += v
print(f"{'ALL':9}{tot['n']:6}{tot['exact']:7}{tot['under']:7}{tot['over']:6}{tot['ai_only']:9}")
reviewed = sum(1 for c in cases if c.get("reviewed_by"))
print(f"\nclinically reviewed cases: {reviewed} of {len(cases)}" + ("   (seed set only: NOT a clinical validation)" if not reviewed else ""))
for tag, c, got, ids in bad:
    print(f"{tag} {c['id']} truth={c['truth']} got={got} {ids} :: {c['text'][:80]}")
sys.exit(1 if bad else 0)
