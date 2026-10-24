"""Tests for followups.py with an in-memory fake of the Supabase query builder (no network):  python3 -I dev/test_followups.py"""
import os, sys
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import followups as fu

class Q:
    def __init__(s, db, name): s.t, s.f, s.op, s.pl, s.lim = db[name], [], "select", None, None
    def select(s, *_): s.op = "select"; return s
    def insert(s, row): s.op, s.pl = "insert", row; return s
    def update(s, pl): s.op, s.pl = "update", pl; return s
    def delete(s): s.op = "delete"; return s
    def eq(s, k, v): s.f.append((k, "eq", v)); return s
    def lte(s, k, v): s.f.append((k, "lte", v)); return s
    def limit(s, n): s.lim = n; return s
    def _m(s, r): return all((r.get(k) == v) if o == "eq" else (r.get(k) <= v) for k, o, v in s.f)
    def execute(s):
        hit = [r for r in s.t if s._m(r)]
        if s.op == "insert": s.t.append({"id": len(s.t) + 1, "attempts": 0, **s.pl}); return type("R", (), {"data": [s.pl]})
        if s.op == "update": [r.update(s.pl) for r in hit]
        if s.op == "delete": [s.t.remove(r) for r in hit]
        return type("R", (), {"data": hit[: s.lim] if s.lim else hit})
class DB:
    def __init__(s): s.d = {"followups": []}
    def table(s, n): return Q(s.d, n)

fails = 0
def check(name, cond):
    global fails; fails += (not cond); print(("OK   " if cond else "FAIL ") + name)

A = ZoneInfo("Europe/Athens")
noon = datetime(2026, 10, 26, 9, 0, tzinfo=A).astimezone(timezone.utc)           # 09:00 Athens
check("URGENT is due 6h later (15:00 local)", fu.due_time("URGENT", noon).astimezone(A).hour == 15)
check("SELF_CARE is due 24h later", fu.due_time("SELF_CARE", noon) - noon == timedelta(hours=24))
late = datetime(2026, 10, 26, 19, 0, tzinfo=A).astimezone(timezone.utc)          # +6h = 01:00 -> push to 08:00 next day
d = fu.due_time("URGENT", late).astimezone(A)
check("quiet hours: 01:00 moves to 08:00 same morning", (d.hour, d.minute) == (8, 0) and d.day == 27)
eve = datetime(2026, 10, 26, 16, 30, tzinfo=A).astimezone(timezone.utc)          # +6h = 22:30 -> 08:00 next day
d = fu.due_time("URGENT", eve).astimezone(A)
check("quiet hours: 22:30 moves to 08:00 next day", (d.hour, d.day) == (8, 27))
check("EMERGENCY gets no reminder (it already says go now)", fu.due_time("EMERGENCY") is None and fu.build_row("a@b.gr", {"name": "Rex"}, "EMERGENCY", "en") is None)
check("no email, no row", fu.build_row("", {"name": "Rex"}, "URGENT", "en") is None)

db = DB()
check("schedule inserts one pending row", fu.schedule(db, "a@b.gr", {"name": "Rex", "species_key": "dog"}, "URGENT", "el") and len(db.d["followups"]) == 1)
fu.schedule(db, "a@b.gr", {"name": "Rex", "species_key": "dog"}, "SELF_CARE", "el")
check("newer verdict replaces the open reminder", len(db.d["followups"]) == 1 and db.d["followups"][0]["level"] == "SELF_CARE")
fu.schedule(db, "a@b.gr", {"name": "Mia", "species_key": "cat"}, "URGENT", "en")
check("different pet gets its own reminder", len(db.d["followups"]) == 2)
row = db.d["followups"][0]
check("row holds no symptom text", set(row) <= {"id", "attempts", "user_email", "pet_name", "species", "level", "lang", "due_at", "status"})

for r in db.d["followups"]: r["due_at"] = (datetime.now(timezone.utc) - timedelta(minutes=1)).isoformat()
out = []
sent, failed = fu.run_due(db, lambda to, s, t: out.append((to, s, t)), "https://app.example")
check("due rows are sent once each", sent == 2 and failed == 0 and len(out) == 2)
check("rows marked sent", all(r["status"] == "sent" for r in db.d["followups"]))
check("second run sends nothing", fu.run_due(db, lambda *a: out.append(a)) == (0, 0) and len(out) == 2)
check("Greek mail in Greek, English in English", "Πώς είναι" in out[0][1] and "How is" in out[1][1])
check("mail has link, go-now line and no symptom detail", "https://app.example" in out[0][2] and "αμέσως" in out[0][2])

db2 = DB(); fu.schedule(db2, "a@b.gr", {"name": "Rex"}, "URGENT", "en")
db2.d["followups"][0]["due_at"] = "2000-01-01T00:00:00+00:00"
def boom(*a): raise OSError("smtp down")
check("failure goes back to pending and retries", fu.run_due(db2, boom) == (0, 1) and db2.d["followups"][0]["status"] == "pending")
fu.run_due(db2, boom); fu.run_due(db2, boom)
check("after 3 attempts it is marked failed, not retried forever", db2.d["followups"][0]["status"] == "failed")

db3 = DB(); fu.schedule(db3, "a@b.gr", {"name": "Rex"}, "URGENT", "en"); fu.cancel(db3, "a@b.gr", "Rex")
db3.d["followups"][0]["due_at"] = "2000-01-01T00:00:00+00:00"
check("cancelled reminder is never sent", fu.run_due(db3, lambda *a: 1 / 0) == (0, 0))
check("not-yet-due rows are left alone", (lambda d: (fu.schedule(d, "x@y.gr", {"name": "Z"}, "URGENT", "en"), fu.run_due(d, lambda *a: 1 / 0))[1])(DB()) == (0, 0))
print("\nall passed" if not fails else f"\nFAILED: {fails}")
sys.exit(1 if fails else 0)
