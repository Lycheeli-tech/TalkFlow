alter table public.users
  add column program_completed_at timestamptz;

alter table public.sessions
  add column current_step smallint not null default 0,
  add column completion_ready boolean not null default false;
