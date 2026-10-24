# PetsAIHealth (kiraaipet)

Streamlit app (single file `app.py`) for pet parents in Greece: nurse chat → vet report, plus tools
(vitals/breathing, photo, labs, longevity, diary, vets, insurance). Greek-first, English supported.

- UI layer: `petify_ui.py` (CSS + HTML builders), `petify_art.py` (SVG scenes), `pet_longevity.py`, `petscan_component.py`.
- Flow: landing (with sign-in at the end) → profile (4 steps) → Home → nurse chat → report. Router is at the bottom of `app.py`.
- Insurance: only EFG Eurolife “My Happy Pet” programmes; contracted network list is `_EUROLIFE_NETWORK` in `app.py`.
- Local preview: `streamlit run dev/harness.py --server.port 8504`, then `?t=<screen>` (add `&s=N` for intake step,
  `&chat=1|emerg` for a seeded chat, `&ins=1` for a selected Eurolife programme). No AI keys locally.
- Deploys: Railway project “pet ai nurse”; `web-staging` follows branch `design/petify-layout`, `web` follows `main`.
- Brand name is “PetsAIHealth” (no apostrophe; file names stay lowercase).
- Plans: free = 3 symptom checks/month (counted in Supabase `usage_events`, kind `triage_check`); “PetsAIHealth Plus” 4,99€/mo
  (49,99€/yr) unlocks every other service (`PAID_SCREENS`). Entitlement = row in `subscriptions` with plan `plus` (legacy `insurance` also counts).
  Checkout links: env `STRIPE_CHECKOUT_MONTHLY` / `STRIPE_CHECKOUT_YEARLY` (app appends `prefilled_email` + `client_reference_id`).
  Stripe → access: Supabase edge function `stripe-webhook` (source in `supabase/functions/`, signing secret lives in Supabase Vault via `get_stripe_webhook_secret()`) writes `subscriptions`.
  Pets: free = 1 pet, profile locked; Plus = unlimited pets (switch/edit/add on Home). Profiles saved encrypted in `user_pets`. `PLUS_PAYWALL=off` disables gating.
  Harness: `&plus=0|1`, `&used=N` (needs fake SUPABASE env to turn the paywall on).

  Landing: plan cards have the CTAs (`pl_free`/`pl_plus`); the sign-in form appears only after one is pressed (`_login_plan`; Plus → paywall page after login).
  Eurolife waiting period: pet profile stores `policy_start` + `policy_number` (intake step 4 for Plus users, or Insurance screen); `waiting_status()` (45 days) feeds the coverage prompt, policy chat and the banner.
  Stripe return: Payment Links redirect to `<app>/?paid=1` (currently the web-staging URL; repoint both links to `web` when going live). `render_paid_page` re-checks the subscription. Account page (`screen=account`, 👤 in nav): plan, renewal, Stripe Billing Portal (`STRIPE_SECRET_KEY` + `subscriptions.stripe_customer_id`) and log out.
  Billing agent: chat on the Account page (`render_billing_agent`, `_BILLING_SYSTEM`) answers about price/upgrade/invoices/cancel and only *shows* action buttons (Stripe checkout or Stripe portal); it never cancels or charges by itself.
  Webhook events enabled in Stripe: checkout.session.completed, invoice.paid, customer.subscription.updated/deleted, charge.refunded (full refund ends access now). Subscription check is cached 2 min per session. A refund does not cancel the Stripe subscription: cancel it too, or it renews.
  Pet archive (Plus): `pet_records` table (Fernet payload, `expires_at` = +6 months; pg_cron job `purge-pet-records` daily 03:17 UTC + purge on every read). `save_record()` is called after report / lab / photo / vitals; `history_context()` is appended in `petainurse_system()` (nurse, report, recs), the lab analysis and the second opinion. Screen `history` (📁 on Home for Plus); OPT-IN: nothing is stored until the user says yes (pref `history_consent` in `user_prefs`: None=not asked, True, False; consent card on Home + Archive screen); privacy page lists it and the GDPR delete wipes it. Only result *texts* are stored, never files/photos.

  Safety rules (`vet_rules.py`): deterministic floor under the nurse chat. `evaluate(species_key, owner_texts, pet)` checks everything the owner wrote (Greek + English,
  accent-insensitive) against ~31 rules + a dose-aware chocolate calculator, each tied to an MSD Veterinary Manual page (rules with `basis="policy"` come from the nurse prompt and still need vet review).
  Wired in `_send_to_petainurse`: hits are appended to the nurse system prompt as alerts, and a FINAL `[TRIAGE: ...]` verdict below the rule floor is raised (with a one-line note). It never lowers a level and never
  ends the 6-question cycle early. Edit/add rules in `RULES`; run `python3 -I dev/test_vet_rules.py` (62 cases, no deps). Add a regression case for every rule you change.

  Extra layers (`vet_safety.py`, all can only RAISE a level): (2) an LLM fact-extraction call turns the owner's words into facts that are fed to the same rules (skipped when the keyword rules already reach EMERGENCY; cached per message set); (3) if the AI call fails the owner gets `fallback_reply()` (URGENT, or the rule floor), never an error or an all-clear; (4) `profile_hits()` age/condition floors (puppy, senior, diabetes, kidney, heart, rabbit anorexia); (5) `safety_net()` "go now if" list appended to every URGENT/SELF_CARE verdict; (6) `log_event("safety_disagreement", ...)` records codes only (kinds: rules_raised_ai, extraction_or_profile_rescue, ai_failed, ai_only_emergency): review weekly in Railway logs; (7) `vitals_hits()` floors from breaths/min, SpO2, temp, heart rate (policy basis, vet to confirm limits); owner text has `[TRIAGE:]`/`[TOOL:]` lookalikes stripped. Tests: `dev/test_vet_safety.py` (no deps) and `dev/e2e_safety.py` (needs app requirements); both run in `.github/workflows/safety.yml`. Not built: scheduled follow-up reminder after a verdict (needs consent + scheduler).
