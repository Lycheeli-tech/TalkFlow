alter table public.users
  add column current_day smallint not null default 1 check (current_day between 1 and 30),
  add column current_phase text not null default 'BUILD'
    check (current_phase in ('BUILD', 'TRANSFER', 'PERFORM'));

alter table public.sessions
  add column day smallint check (day between 1 and 30),
  add column phase text check (phase in ('BUILD', 'TRANSFER', 'PERFORM')),
  add column duration_plan smallint check (duration_plan in (10, 20, 30, 60)),
  add column topic_family text,
  add column scaffolding_level text check (scaffolding_level in ('HIGH', 'MEDIUM', 'LOW')),
  add column session_plan jsonb;

create index sessions_daily_history_idx
  on public.sessions (user_id, session_type, completed_at desc)
  where session_type = 'DAILY';
