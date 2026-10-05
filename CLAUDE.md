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
