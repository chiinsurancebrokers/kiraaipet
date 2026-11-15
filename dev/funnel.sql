-- PetsAIHealth launch funnel. Run in the Supabase SQL editor (service role / dashboard: bypasses RLS). Counts only, no emails.
-- Events come from usage_events: login, session_start, triage_check, followup_offer_shown, followup_consent (app.py: track_event).
-- Events only exist from the release that added track_event; earlier users show up through triage_check only.
-- Change the 30-day window below if needed.

with ev as (
  select lower(user_email) as u, kind, created_at
  from public.usage_events
  where created_at > now() - interval '30 days'
), first_seen as (
  select u, min(created_at) as t0 from ev group by u
), per_user as (
  select f.u,
    bool_or(e.kind = 'triage_check')                                       as did_check,
    bool_or(e.kind = 'followup_offer_shown')                               as saw_offer,
    bool_or(e.kind = 'followup_consent')                                   as consented,
    -- return = a session on a later calendar day than the first time we saw the user
    bool_or(e.kind in ('session_start', 'login') and e.created_at::date > f.t0::date) as returned
  from first_seen f join ev e using (u)
  group by f.u
)
select
  count(*)                                         as signed_up,
  count(*) filter (where did_check)                as first_check,
  count(*) filter (where saw_offer)                as saw_followup_offer,
  count(*) filter (where consented)                as opted_in,
  count(*) filter (where returned)                 as returned_later_day,
  round(100.0 * count(*) filter (where did_check) / nullif(count(*), 0), 1)               as pct_checked,
  round(100.0 * count(*) filter (where consented) / nullif(count(*) filter (where saw_offer), 0), 1) as pct_opt_in_of_offered,
  round(100.0 * count(*) filter (where returned) / nullif(count(*), 0), 1)                as pct_returned
from per_user;

-- Follow-up mail results (outcome comes from the one-tap links in the mail; more reliable than open tracking)
select status, level, coalesce(outcome, '-') as outcome, count(*) as n
from public.followups
group by 1, 2, 3
order by 1, 2, 3;
