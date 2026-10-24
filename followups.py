"""One-time follow-up email after an URGENT / SELF_CARE verdict (opt-in).

App side:   schedule()  inserts a `followups` row when the owner presses the reminder button.
Worker side: `python3 followups.py` sends the due rows through Resend. Run it every 15-30 minutes as a Railway cron
            service (same repo, start command `python3 followups.py`). Env: SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY,
            RESEND_API_KEY, FOLLOWUP_FROM (e.g. "PetsAIHealth <care@yourdomain>"), APP_URL.
The email never contains symptoms: only the pet's name, the level wording, a link back and the go-now reminder.
"""
import json
import os
import sys
import urllib.request
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

DELAY_HOURS = {"URGENT": 6, "SELF_CARE": 24}
QUIET = (22, 8)                      # no email between 22:00 and 08:00 Athens time
TZ = ZoneInfo("Europe/Athens")
MAX_ATTEMPTS = 3


def due_time(level, now=None):
    """When to send: level delay, moved to 08:00 local if it would land in the quiet hours."""
    if level not in DELAY_HOURS:
        return None
    t = (now or datetime.now(timezone.utc)) + timedelta(hours=DELAY_HOURS[level])
    loc = t.astimezone(TZ)
    if loc.hour >= QUIET[0] or loc.hour < QUIET[1]:
        day = loc.date() + (timedelta(days=1) if loc.hour >= QUIET[0] else timedelta(0))
        loc = datetime(day.year, day.month, day.day, QUIET[1], 0, tzinfo=TZ)
    return loc.astimezone(timezone.utc)


def build_row(email, pet, level, lang, now=None):
    due = due_time(level, now)
    if not email or not due:
        return None
    return {"user_email": email, "pet_name": (pet.get("name") or "")[:60], "species": pet.get("species_key") or "",
            "level": level, "lang": "el" if lang == "el" else "en", "due_at": due.isoformat(), "status": "pending"}


def schedule(sb, email, pet, level, lang):
    """Insert (replacing an older open reminder for the same pet). Returns the due time or None."""
    row = build_row(email, pet, level, lang)
    if not row or sb is None:
        return None
    sb.table("followups").delete().eq("user_email", email).eq("pet_name", row["pet_name"]).eq("status", "pending").execute()
    sb.table("followups").insert(row).execute()
    return row["due_at"]


def cancel(sb, email, pet_name=""):
    sb.table("followups").update({"status": "cancelled"}).eq("user_email", email).eq("pet_name", pet_name or "").eq("status", "pending").execute()


def compose(row, app_url=""):
    """(subject, text) in the owner's language. No clinical detail."""
    name = row.get("pet_name") or ("το κατοικίδιό σου" if row["lang"] == "el" else "your pet")
    link = app_url or "https://petsaihealth.com"
    if row["lang"] == "el":
        subj = f"Πώς είναι τώρα {name};"
        body = (f"Γεια σου! Ζήτησες μια υπενθύμιση για να δούμε πώς είναι {name} μετά τον έλεγχο στην PetsAIHealth.\n\n"
                "Αν τα συμπτώματα συνεχίζονται, επιδεινώνονται ή εμφανίστηκε κάτι νέο, επικοινώνησε με κτηνίατρο σήμερα· "
                "αν δεις δύσκολη αναπνοή, χλωμά ούλα, σπασμό, κατάρρευση ή αδυναμία ούρησης, πήγαινε αμέσως σε κτηνιατρείο.\n\n"
                f"Ξεκίνα νέο έλεγχο: {link}\n\nΑυτό είναι ένα μήνυμα που ζήτησες, δεν θα σου ξαναστείλουμε. Δεν αντικαθιστά κτηνιατρική εξέταση.")
    else:
        subj = f"How is {name} doing now?"
        body = (f"Hi! You asked us to check in on {name} after your PetsAIHealth assessment.\n\n"
                "If the signs continue, get worse, or something new appears, contact a vet today; if you see difficulty breathing, "
                "pale gums, a seizure, collapse or inability to urinate, go to a vet right away.\n\n"
                f"Start a new check: {link}\n\nThis is a one-time message you asked for; we won't send another. It does not replace a vet exam.")
    return subj, body


def _post(url, headers, payload):
    req = urllib.request.Request(url, data=json.dumps(payload).encode(), headers=headers)
    with urllib.request.urlopen(req, timeout=20) as r:
        return r.status


def send_email(to, subject, text, api_key, sender):
    return _post("https://api.resend.com/emails", {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                 {"from": sender, "to": [to], "subject": subject, "text": text})


def run_due(sb, send, app_url="", now=None, limit=50):
    """Send every due reminder once. `send(to, subject, text)` is injected so tests need no network.
    Returns (sent, failed). A row is claimed (pending -> sending) before sending so two workers can't double-send."""
    now = now or datetime.now(timezone.utc)
    rows = (sb.table("followups").select("*").eq("status", "pending").lte("due_at", now.isoformat()).limit(limit).execute().data) or []
    sent = failed = 0
    for row in rows:
        claimed = sb.table("followups").update({"status": "sending", "attempts": row.get("attempts", 0) + 1}) \
            .eq("id", row["id"]).eq("status", "pending").execute().data
        if not claimed:
            continue
        try:
            send(row["user_email"], *compose(row, app_url))
            sb.table("followups").update({"status": "sent", "sent_at": now.isoformat()}).eq("id", row["id"]).execute()
            sent += 1
        except Exception:
            final = row.get("attempts", 0) + 1 >= MAX_ATTEMPTS
            sb.table("followups").update({"status": "failed" if final else "pending"}).eq("id", row["id"]).execute()
            failed += 1
    return sent, failed


def main():
    from supabase import create_client
    need = ("SUPABASE_URL", "SUPABASE_SERVICE_ROLE_KEY", "RESEND_API_KEY", "FOLLOWUP_FROM")
    missing = [k for k in need if not os.environ.get(k)]
    if missing:
        print(json.dumps({"event": "followups_worker", "ok": False, "error": "missing env: " + ",".join(missing)}))
        return 1
    sb = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_SERVICE_ROLE_KEY"])
    key, sender = os.environ["RESEND_API_KEY"], os.environ["FOLLOWUP_FROM"]
    sent, failed = run_due(sb, lambda to, s, t: send_email(to, s, t, key, sender), os.environ.get("APP_URL", ""))
    print(json.dumps({"event": "followups_worker", "ok": failed == 0, "sent": sent, "failed": failed}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
