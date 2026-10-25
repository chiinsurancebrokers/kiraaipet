"""Tests for the flag, hand-off, event log and outcome links (no deps, no network):  python3 -I dev/test_vet_extras.py"""
import os, sys
from datetime import datetime, timedelta, timezone
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import vet_rules as vr, vet_safety as vs, safety_events as se, followups as fu

fails = 0
def check(name, cond):
    global fails; fails += (not cond); print(("OK   " if cond else "FAIL ") + name)

# kill switch
check("flag: unset/empty/on are ON", vs.flag(None) and vs.flag("") and vs.flag("on") and vs.flag("ON") and vs.flag("true"))
check("flag: off/0/false/no/disabled are OFF", not any(vs.flag(v) for v in ("off", "OFF", "0", "false", "No", "disabled", " off ")))

# negation guard
check("negation: 'did not eat grapes' is silent", vr.evaluate("dog", ["he did not eat the grapes"]).level == "")
check("negation: Greek", vr.evaluate("dog", ["δεν έφαγε σταφίδες"]).level == "")
check("negation: uncertainty still fires", vr.evaluate("dog", ["not sure, maybe he ate grapes"]).level == "EMERGENCY")
check("negation: later real exposure after 'but' still fires", vr.evaluate("dog", ["he did not eat the chocolate but he ate grapes"]).level == "EMERGENCY")
check("negation does not touch symptom rules", vr.evaluate("rabbit", ["he is not eating and has no droppings"]).level == "URGENT")
check("negation: chocolate calculator respects it", vr.evaluate("dog", ["he didn't eat the chocolate, only the wrapper"], {"weight": 5}).level == "")

# hand-off
h = vs.handoff(["DC-SNAKEBITE"], "en")
check("hand-off for a toxin hit points to a vet and the vet finder", "vet" in h["text"].lower() and h["show_vets"] and h["bait_text"] == "")
b = vs.handoff(["DC-POISON-BAIT", "DC-RODENTICIDE"], "en")
check("bait hit adds the official report lines", vs.NECCA_PHONE in b["bait_text"] and vs.ABUSE_LINE in b["bait_text"])
check("hand-off in Greek", "κτηνίατρο" in vs.handoff(["DOG-GRAPES"], "el")["text"])
check("no hand-off for non-toxin rules", vs.handoff(["DOG-GDV", "ALL-COLLAPSE"], "en") == {} and vs.handoff([], "en") == {})
check("chocolate counts as a toxin", bool(vs.handoff(["DC-CHOCOLATE"], "en")))
check("every guarded rule exists", all(any(r.id == i for r in vr.RULES) for i in vr._GUARDED))

# events
class Tbl:
    def __init__(s, rows): s.rows = rows
    def insert(s, r): s.r = r; return s
    def execute(s): s.rows.append(s.r)
class SB:
    def __init__(s): s.rows = []
    def table(s, n): assert n == "safety_events"; return Tbl(s.rows)
sb = SB()
check("record keeps whitelisted code fields only", se.record(sb, {"kind": "rules_raised_ai", "species": "dog", "floor": "EMERGENCY", "ai": "SELF_CARE", "rules": "DOG-XYLITOL", "owner_text": "secret", "email": "a@b.gr"})
      and set(sb.rows[0]) == {"kind", "species", "floor_level", "ai_level", "keyword_level", "rules"})
check("record ignores unknown kinds and never raises", not se.record(sb, {"kind": "x"}) and not se.record(None, {"kind": "ai_failed"}) and not se.record(object(), {"kind": "ai_failed"}))

now = datetime(2026, 10, 25, tzinfo=timezone.utc)
iso = lambda d: (now - timedelta(days=d)).isoformat()
rows = [{"kind": "ai_failed", "rules": "", "created_at": iso(1)}] * 6 + [{"kind": "rules_raised_ai", "rules": "DOG-GRAPES,DC-CHOCOLATE", "created_at": iso(2)}] * 12 \
     + [{"kind": "rules_raised_ai", "rules": "DOG-GRAPES", "created_at": iso(9)}] * 3 + [{"kind": "outcome_worse", "rules": "", "created_at": iso(3)}] * 4 \
     + [{"kind": "outcome_ok", "rules": "", "created_at": iso(3)}] * 1 + [{"kind": "ai_failed", "rules": "", "created_at": "garbage"}]
sm = se.summarize(rows, now)
check("summary windows", sm["current"]["ai_failed"] == 6 and sm["previous"]["rules_raised_ai"] == 3 and sm["current"]["rules_raised_ai"] == 12)
check("top rules counted", sm["top_rules"]["rules_raised_ai"][0] == ("DOG-GRAPES", 12))
al = se.alerts(sm)
check("alerts: outage, doubled kind, worse > ok", len(al) == 3 and any("AI failures" in a for a in al) and any("jumped" in a for a in al) and any("worse" in a for a in al))
check("no alerts on a quiet week", se.alerts(se.summarize([], now)) == [])
check("report text names alerts", "ALERTS:" in se.format_report(sm) and "rules_raised_ai" in se.format_report(sm))

# outcome links
row = {"id": "11111111-2222", "lang": "en", "pet_name": "Rex", "level": "URGENT"}
tok = fu.outcome_token(row["id"], "ok", "s3cret")
check("token is per outcome and per secret", tok != fu.outcome_token(row["id"], "worse", "s3cret") and tok != fu.outcome_token(row["id"], "ok", "other") and len(tok) == 32)
lk = fu.outcome_links(row, "https://x.supabase.co/functions/v1/followup-outcome", "s3cret")
check("links carry id, outcome and token", "o=ok" in lk["ok"] and "o=worse" in lk["worse"] and tok in lk["ok"])
check("no links when not configured", fu.outcome_links(row, "", "s") == {} and fu.outcome_links(row, "https://x", "") == {})
subj, body = fu.compose(row, "https://app", lk)
check("mail contains both links, still no symptoms", lk["ok"] in body and lk["worse"] in body and "vomit" not in body.lower())
check("mail without links is unchanged", "one tap" not in fu.compose(row, "https://app")[1])
check("Greek mail has the links too", "Είναι καλύτερα" in fu.compose({**row, "lang": "el"}, "", lk)[1])

print("\nall passed" if not fails else f"\nFAILED: {fails}")
sys.exit(1 if fails else 0)
