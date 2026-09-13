-- ADR-032: ephemeral Practice aggregates, not Course or Legacy history.
create table public.practice_runs (
  id uuid primary key,
  user_id uuid not null references public.users(id) on delete cascade,
  idempotency_key varchar(128) not null,
  revision integer not null default 0 check (revision >= 0),
  payload jsonb not null,
  expires_at timestamptz not null,
  unique (user_id, idempotency_key),
  check (jsonb_array_length(payload->'question_ids') in (3,5)),
  check ((payload->>'current_position')::integer >= 0
    and (payload->>'current_position')::integer < jsonb_array_length(payload->'question_ids')),
  check (payload->>'status' in ('ACTIVE','PAUSED','GENERATING')),
  check ((payload->>'user_id')::uuid = user_id and (payload->>'id')::uuid = id)
);
create index practice_runs_owner_expiry_idx on public.practice_runs(user_id, expires_at);
create index practice_runs_expiry_idx on public.practice_runs(expires_at);
alter table public.practice_runs enable row level security;
revoke all on public.practice_runs from public, authenticated;
grant select on public.practice_runs to authenticated;
create policy "Users read only active owned Practice Runs" on public.practice_runs
  for select to authenticated using ((select auth.uid()) = user_id and expires_at > statement_timestamp());

-- No FK to the temporary Run or user: deletion/cascade must not erase the cleanup obligation.
create table public.practice_audio_cleanup_jobs (
  storage_path text primary key,
  user_id uuid not null,
  attempts integer not null default 0,
  next_attempt_at timestamptz not null default now()
);
alter table public.practice_audio_cleanup_jobs enable row level security;
revoke all on public.practice_audio_cleanup_jobs from public, authenticated;

create function public.queue_deleted_practice_audio() returns trigger
language plpgsql security definer set search_path = public as $$
begin
  insert into public.practice_audio_cleanup_jobs(storage_path,user_id)
    select answer->>'audio_path', old.user_id
    from jsonb_array_elements(old.payload->'answers') as answer
    where answer->>'audio_path' is not null
    on conflict (storage_path) do nothing;
  return old;
end;
$$;
revoke all on function public.queue_deleted_practice_audio() from public;
create trigger practice_audio_before_delete before delete on public.practice_runs
  for each row execute function public.queue_deleted_practice_audio();
