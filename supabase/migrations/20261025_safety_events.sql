-- Safety event log: codes only. No owner text, no names, no e-mail, no user id.
create table if not exists public.safety_events (
  id            bigint generated always as identity primary key,
  kind          text not null check (kind in ('rules_raised_ai','extraction_or_profile_rescue','ai_failed','ai_only_emergency','outcome_ok','outcome_worse')),
  species       text not null default '' check (char_length(species) <= 20),
  floor_level   text not null default '' check (char_length(floor_level) <= 12),
  ai_level      text not null default '' check (char_length(ai_level) <= 12),
  keyword_level text not null default '' check (char_length(keyword_level) <= 12),
  rules         text not null default '' check (char_length(rules) <= 200),
  created_at    timestamptz not null default now()
);
create index if not exists safety_events_kind_time on public.safety_events (kind, created_at desc);

alter table public.safety_events enable row level security;
-- the app may only ADD rows (anon or signed in); nobody can read them except the service role used by the report worker
create policy safety_events_insert on public.safety_events for insert to anon, authenticated with check (true);

-- keep 12 months
select cron.schedule('purge-safety-events', '29 3 * * *', $$delete from public.safety_events where created_at < now() - interval '12 months'$$);

-- follow-up outcome ("he is fine" / "still unwell") chosen from the e-mail link, written by the followup-outcome edge function
alter table public.followups add column if not exists outcome text check (outcome in ('ok', 'worse'));
alter table public.followups add column if not exists outcome_at timestamptz;
