---
description: Pre-launch checklist for a change or the whole app
argument-hint: <feature or "app">
---
Run a launch check for $ARGUMENTS and report pass/fail per item:
1. Tests: python3 -I dev/test_vet_rules.py, test_vet_safety.py, test_rule_samples.py, test_html_escape.py, test_followups.py.
2. Phone check at 390px for the changed screens (use dev/harness.py).
3. Terms page and privacy page match what the app really stores; OPERATOR_* env vars set.
4. Stripe links point at the production domain; webhook events enabled.
5. Safety: vet-review status of policy rules stated honestly; kill switch VET_FLOOR documented.
6. Monitoring/logs reachable; rollback = redeploy previous commit.
End with GO / NO-GO and the top 3 blockers.
