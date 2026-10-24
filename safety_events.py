"""Safety event log: codes only (no owner text, no names, no e-mail), written to Supabase `safety_events`, plus a weekly report
and spike alerts.

App:    record(sb, fields)           from log_event fields of vet_safety.disagreement() and the follow-up outcome links.
Report: python3 safety_events.py [--days 7] [--alert]    (needs SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY; --alert also needs
        RESEND_API_KEY, FOLLOWUP_FROM, SAFETY_ALERT_TO). Run daily from the same Railway cron service as followups.py.
Kinds:  rules_raised_ai, extraction_or_profile_rescue, ai_failed, ai_only_emergency, outcome_ok, outcome_worse.
"""
import json
import os
import sys
from collections import Counter
from datetime import datetime, timedelta, timezone

KINDS = ("rules_raised_ai", "extraction_or_profile_rescue", "ai_failed", "ai_only_emergency", "outcome_ok", "outcome_worse")


def record(sb, fields):
    """Insert one event. Only whitelisted short code fields are kept. Never raises (logging must not break the chat)."""
    try:
        if sb is None or not fields or fields.get("kind") not in KINDS:
            return False
        row = {"kind": fields["kind"], "species": str(fields.get("species", ""))[:20], "floor_level": str(fields.get("floor", ""))[:12],
               "ai_level": str(fields.get("ai", ""))[:12], "keyword_level": str(fields.get("keyword_only", ""))[:12],
               "rules": str(fields.get("rules", ""))[:200]}
        sb.table("safety_events").insert(row).execute()
        return True
    except Exception:
        return False


def summarize(rows, now=None, days=7):
    """Counts for the last `days` and the `days` before, plus the most frequent rule ids per kind."""
    now = now or datetime.now(timezone.utc)
    cur, prev, rules = Counter(), Counter(), {}
    for r in rows:
        try:
            t = datetime.fromisoformat(str(r["created_at"]).replace("Z", "+00:00"))
        except (KeyError, ValueError):
            continue
        age = now - t
        if age <= timedelta(days=days):
            cur[r["kind"]] += 1
            for rid in filter(None, str(r.get("rules", "")).split(",")):
                rules.setdefault(r["kind"], Counter())[rid] += 1
        elif age <= timedelta(days=2 * days):
            prev[r["kind"]] += 1
    return {"current": dict(cur), "previous": dict(prev), "top_rules": {k: v.most_common(5) for k, v in rules.items()}}


def alerts(summary, min_count=10, ratio=2.0, outage=5):
    """Human-readable alerts: AI outage volume, a kind that doubled week on week, or worsening follow-ups outnumbering recoveries."""
    out, cur, prev = [], summary["current"], summary["previous"]
    if cur.get("ai_failed", 0) >= outage:
        out.append(f"AI failures: {cur['ai_failed']} in the period (users saw the fallback message).")
    for k in ("rules_raised_ai", "ai_only_emergency", "extraction_or_profile_rescue"):
        c, p = cur.get(k, 0), prev.get(k, 0)
        if c >= min_count and c >= ratio * max(p, 1):
            out.append(f"{k} jumped from {p} to {c}: check the rules or the model.")
    ok, worse = cur.get("outcome_ok", 0), cur.get("outcome_worse", 0)
    if worse >= 3 and worse > ok:
        out.append(f"Follow-up replies: {worse} worse vs {ok} fine. Verdicts may be too lenient.")
    return out


def format_report(summary, days=7):
    lines = [f"PetsAIHealth safety report, last {days} days (previous {days} in brackets)"]
    for k in KINDS:
        lines.append(f"  {k:30} {summary['current'].get(k, 0):4}  ({summary['previous'].get(k, 0)})")
    for k, top in summary["top_rules"].items():
        lines.append(f"  top rules for {k}: " + ", ".join(f"{r}x{n}" for r, n in top))
    a = alerts(summary)
    lines.append("ALERTS: " + ("; ".join(a) if a else "none"))
    return "\n".join(lines)


def main(argv):
    days = int(argv[argv.index("--days") + 1]) if "--days" in argv else 7
    need = ("SUPABASE_URL", "SUPABASE_SERVICE_ROLE_KEY")
    if [k for k in need if not os.environ.get(k)]:
        print(json.dumps({"event": "safety_report", "ok": False, "error": "missing env"}))
        return 1
    from supabase import create_client
    sb = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_SERVICE_ROLE_KEY"])
    since = (datetime.now(timezone.utc) - timedelta(days=2 * days)).isoformat()
    rows = sb.table("safety_events").select("kind,rules,created_at").gte("created_at", since).limit(20000).execute().data or []
    summary = summarize(rows, days=days)
    report = format_report(summary, days)
    print(report)
    found = alerts(summary)
    if "--alert" in argv and found and all(os.environ.get(k) for k in ("RESEND_API_KEY", "FOLLOWUP_FROM", "SAFETY_ALERT_TO")):
        import followups
        followups.send_email(os.environ["SAFETY_ALERT_TO"], "PetsAIHealth safety alert", report, os.environ["RESEND_API_KEY"], os.environ["FOLLOWUP_FROM"])
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
