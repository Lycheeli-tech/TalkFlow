alter table public.users
  add column xp integer not null default 0 check (xp >= 0),
  add column current_streak smallint not null default 0 check (current_streak >= 0),
  add column last_completed_date date;
