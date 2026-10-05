# Pets’health (kiraaipet)

Streamlit app (single file `app.py`) for pet parents in Greece: nurse chat → vet report, plus tools
(vitals/breathing, photo, labs, longevity, diary, vets, insurance). Greek-first, English supported.

- UI layer: `petify_ui.py` (CSS + HTML builders), `petify_art.py` (SVG scenes), `pet_longevity.py`, `petscan_component.py`.
- Flow: landing (with sign-in at the end) → profile (4 steps) → Home → nurse chat → report. Router is at the bottom of `app.py`.
- Insurance: only EFG Eurolife “My Happy Pet” programmes; contracted network list is `_EUROLIFE_NETWORK` in `app.py`.
- Local preview: `streamlit run dev/harness.py --server.port 8504`, then `?t=<screen>` (add `&s=N` for intake step,
  `&chat=1|emerg` for a seeded chat, `&ins=1` for a selected Eurolife programme). No AI keys locally.
- Deploys: Railway project “pet ai nurse”; `web-staging` follows branch `design/petify-layout`, `web` follows `main`.
- Brand name is “Pets’health” (typographic apostrophe, because a plain one breaks Python strings).
- Plans: free = 3 symptom checks/month (counted in Supabase `usage_events`, kind `triage_check`); “Pets’health Plus” 4,99€/mo
  (49,99€/yr) unlocks every other service (`PAID_SCREENS`). Entitlement = row in `subscriptions` with plan `plus` (legacy `insurance` also counts).
  Checkout links: env `STRIPE_CHECKOUT_MONTHLY` / `STRIPE_CHECKOUT_YEARLY` (app appends `prefilled_email` + `client_reference_id`).
  Stripe → access: Supabase edge function `stripe-webhook` (source in `supabase/functions/`, needs secret `STRIPE_WEBHOOK_SECRET`) writes `subscriptions`.
  Pets: free = 1 pet, profile locked; Plus = unlimited pets (switch/edit/add on Home). Profiles saved encrypted in `user_pets`. `PLUS_PAYWALL=off` disables gating.
  Harness: `&plus=0|1`, `&used=N` (needs fake SUPABASE env to turn the paywall on).
