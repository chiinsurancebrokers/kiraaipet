-- usage_events: stop leaking every user's email + events, allow funnel tracking and GDPR delete.
-- BEFORE: select policy `using (true)` for anon and authenticated = anyone holding the public anon key could read
--         every row (user_email + kind + time); insert policy `with check (true)` let anyone write events for any email
--         (e.g. burn another user's free monthly checks).
-- AFTER:  a signed-in user can read, add and (funnel events only) delete their own rows. `triage_check` rows stay
--         undeletable by the user because they enforce the free monthly quota.
-- The app only touches this table with the signed-in user's token (record_triage_check, triage_used_this_month,
-- track_event, GDPR delete), so nothing in the app needs the old open policies.
-- Review, then run once in the Supabase SQL editor (not applied automatically).

drop policy if exists usage_events_select on public.usage_events;
drop policy if exists usage_events_insert on public.usage_events;
drop policy if exists usage_events_self_select on public.usage_events;
drop policy if exists usage_events_self_insert on public.usage_events;
drop policy if exists usage_events_self_delete_funnel on public.usage_events;

create policy usage_events_self_select on public.usage_events
  for select to authenticated
  using (lower(user_email) = lower((select auth.jwt() ->> 'email')));

create policy usage_events_self_insert on public.usage_events
  for insert to authenticated
  with check (
    lower(user_email) = lower((select auth.jwt() ->> 'email'))
    and kind in ('triage_check', 'login', 'session_start', 'followup_offer_shown', 'followup_consent')
  );

create policy usage_events_self_delete_funnel on public.usage_events
  for delete to authenticated
  using (
    lower(user_email) = lower((select auth.jwt() ->> 'email'))
    and kind <> 'triage_check'
  );

-- Rollback (restores the old open policies; only if something breaks):
--   drop policy usage_events_self_select on public.usage_events;
--   drop policy usage_events_self_insert on public.usage_events;
--   drop policy usage_events_self_delete_funnel on public.usage_events;
--   create policy usage_events_select on public.usage_events for select to anon, authenticated using (true);
--   create policy usage_events_insert on public.usage_events for insert to anon, authenticated with check (true);
