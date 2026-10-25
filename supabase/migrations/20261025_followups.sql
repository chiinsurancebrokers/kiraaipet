-- One-time "how is your pet now?" email after an URGENT / SELF_CARE verdict. Strictly opt-in: a row exists only
-- because the owner pressed the reminder button; `consent_at` records when. No symptoms or chat text are stored.
create table if not exists public.followups (
  id          uuid primary key default gen_random_uuid(),
  user_email  text not null,
  pet_name    text,
  species     text,
  level       text not null check (level in ('URGENT', 'SELF_CARE')),
  lang        text not null default 'el' check (lang in ('el', 'en')),
  due_at      timestamptz not null,
  status      text not null default 'pending' check (status in ('pending', 'sending', 'sent', 'cancelled', 'failed')),
  attempts    int  not null default 0,
  consent_at  timestamptz not null default now(),
  sent_at     timestamptz,
  created_at  timestamptz not null default now()
);

create index if not exists followups_due_idx on public.followups (status, due_at);
-- one open reminder per owner and pet: a newer verdict replaces the older one
create unique index if not exists followups_one_open on public.followups (user_email, (coalesce(pet_name, '')))
  where status = 'pending';

alter table public.followups enable row level security;

-- the signed-in owner manages only their own rows; the worker uses the service role (bypasses RLS)
create policy followups_select on public.followups for select using (user_email = (auth.jwt() ->> 'email'));
create policy followups_insert on public.followups for insert with check (user_email = (auth.jwt() ->> 'email'));
create policy followups_update on public.followups for update using (user_email = (auth.jwt() ->> 'email'));
create policy followups_delete on public.followups for delete using (user_email = (auth.jwt() ->> 'email'));

-- sent / cancelled rows are not kept: purge after 30 days (needs pg_cron, already used for purge-pet-records)
select cron.schedule('purge-followups', '23 3 * * *',
  $$delete from public.followups where status in ('sent', 'cancelled', 'failed') and created_at < now() - interval '30 days'$$);
