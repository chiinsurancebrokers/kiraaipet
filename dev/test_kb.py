"""Tests for kb.py / kb_vet.py (no deps):  python3 -I dev/test_kb.py"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import kb, kb_vet

fails = 0
def check(name, cond):
    global fails; fails += (not cond); print(("OK   " if cond else "FAIL ") + name)
def ids(sp, texts, alert=()):
    return [f.chunk.id for f in kb_vet.retrieve(sp, texts, alert)[1]]

# text handling
check("fold: accents + final sigma", kb.fold("Κουρασμένος ΣΚΎΛΟΣ") == "κουρασμενοσ σκυλοσ")
check("stem: English forms meet", kb.stem("vomiting") == kb.stem("vomited") == kb.stem("vomit"))
check("stem: oe/e spellings meet", kb.stem("diarrhoea") == kb.stem("diarrhea"))
check("Greek word reaches English terms", kb.stem("vomit") in kb.expand("έκανε εμετό"))

# corpus
cs = kb_vet.chunks()
check("corpus: unique ids", len({c.id for c in cs}) == len(cs))
check("corpus: every chunk has text and a label", all(c.text.strip() and c.title for c in cs))
check("corpus: rule chunks carry the MSD url when the rule has one", any(c.source.startswith("https://") for c in cs if c.id.startswith("rule:")))

# retrieval quality (labelled: Greek and English)
check("GI (EL) finds persistent vomiting/diarrhoea guidance", "rule:DC-GI-PERSISTENT" in ids("dog", ["3 εμετούς, 1 διάρροια, αρνείται φαγητό, είναι κουρασμένος"]))
check("bloat (EL) finds GDV", "rule:DOG-GDV" in ids("dog", ["έχει κοιλιά φουσκωμένη και προσπαθεί να κάνει εμετό χωρίς να βγάζει τίποτα"]))
check("cat cannot pee (EL) finds urethral blockage", "rule:CAT-URETHRAL" in ids("cat", ["δεν μπορεί να κατουρήσει και πηγαίνει συνέχεια στην άμμο"]))
check("English GI finds persistent GI guidance", "rule:DC-GI-PERSISTENT" in ids("dog", ["vomiting twice and diarrhoea for two days, not eating"]))
check("chocolate (EL) still gets its topic", "topic:chocolate" in ids("dog", ["έφαγε σοκολάτα"]))
check("ordinary non-pet message retrieves nothing", ids("dog", ["ποιος είναι ο πρωθυπουργός"]) == [])
check("'πρωθυπουργός' no longer triggers the urine topic", "topic:urine_block" not in ids("dog", ["ποιος είναι ο πρωθυπουργός"]))
check("species filter: rabbit guidance not given for a dog", not any(i.startswith("rule:RAB-") for i in ids("dog", ["δεν τρώει και δεν κάνει κόπρανα"])))
check("rules that already fired as alerts are not repeated", "rule:DC-GI-PERSISTENT" not in ids("dog", ["3 εμετούς, 1 διάρροια, αρνείται φαγητό, είναι κουρασμένος"], alert=("DC-GI-PERSISTENT",)))
check("deterministic: same input, same output", ids("dog", ["έχει διάρροια"]) == ids("dog", ["έχει διάρροια"]))

# prompt block + citations
blk, found = kb_vet.retrieve("dog", ["3 εμετούς, 1 διάρροια, αρνείται φαγητό"])
check("block tags every chunk [S1]..", all(f"[S{i}]" in blk for i in range(1, len(found) + 1)) and found)
check("block marks unreviewed guidance", "pending clinician review" in blk)
check("block keeps the first-aid guardrails", "never tell the owner to make the pet vomit" in blk)
check("block stays small (< 4500 chars)", len(blk) < 4500)
out = kb.cite("Μην του δώσεις φαγητό για 4-6 ώρες [S1]. Παρακολούθησε το χρώμα των ούλων [S9].", found, "el")
check("cite: tags removed from the text", "[S" not in out)
check("cite: only cited, valid chunks are listed", out.count("Πηγές:") == 1 and found[0].chunk.title in out)
check("cite: no sources line when nothing was cited", kb.cite("Απλή ερώτηση;", found, "el") == "Απλή ερώτηση;")
check("cite: policy chunks are named, never linked", "()" not in kb.cite("x [S1]", [kb.Found(kb.Chunk("a", "t", "Policy"), 1, 1)], "en"))

# kill switch
os.environ["KB_RAG"] = "off"
check("KB_RAG=off keeps only the old keyword topics", all(i.startswith("topic:") for i in ids("dog", ["3 εμετούς, 1 διάρροια, αρνείται φαγητό"])))
del os.environ["KB_RAG"]

print(f"\n{fails} failed"); sys.exit(1 if fails else 0)
