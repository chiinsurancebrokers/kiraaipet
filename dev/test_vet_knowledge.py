"""Tests for vet_knowledge.py (no deps):  python3 -I dev/test_vet_knowledge.py"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import vet_knowledge as vk

fails = 0
def check(name, cond):
    global fails; fails += (not cond); print(("OK   " if cond else "FAIL ") + name)
def ids(sp, text): return [t for t, _x, _u in vk.relevant(sp, [text])]

check("chocolate topic", "chocolate" in ids("dog", "he ate dark chocolate"))
check("Greek chocolate", "chocolate" in ids("dog", "έφαγε σοκολάτα"))
check("snakebite (EN + EL)", "snakebite" in ids("dog", "a viper bit him") and "snakebite" in ids("dog", "τον δάγκωσε φίδι"))
check("lily -> plants", "plants" in ids("cat", "chewed a lily leaf"))
check("flea drops -> insecticide", "insecticide" in ids("cat", "put flea drops on her"))
check("bleach -> corrosives", "corrosives" in ids("dog", "he drank bleach"))
check("avocado reaches birds", "avocado" in ids("bird", "ate avocado"))
check("species filter: grapes are a dog topic", "grapes" not in ids("rabbit", "ate grapes"))
check("no topic for an ordinary message", ids("dog", "he is limping a bit since yesterday") == [])
check("'environment' does not trigger iron", "decongestant_vitamin" not in ids("dog", "new environment at home"))
check("limit respected", len(vk.relevant("dog", ["chocolate grapes xylitol dough bleach plant snake flea salt heat"], limit=3)) == 3)
blk = vk.prompt_block("dog", ["he ate chocolate"])
check("block has guardrails + facts", "never tell the owner to make the pet vomit" in blk and "theobromine" in blk)
check("empty block when nothing matches", vk.prompt_block("dog", ["limping"]) == "")
check("block stays small (< 3500 chars for 4 topics)", len(vk.prompt_block("dog", ["chocolate grapes xylitol dough bleach plant snake"])) < 3500)
check("every topic has an MSD page and text", all(u.startswith("https://www.msdvetmanual.com/") and len(x) > 80 for _t, _r, _s, x, u in [(a, b, c, d, e) for a, b, c, d, e in vk._COMPILED]))
print("\nall passed" if not fails else f"\nFAILED: {fails}")
sys.exit(1 if fails else 0)
