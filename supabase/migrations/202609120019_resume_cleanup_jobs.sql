create table public.document_cleanup_jobs (
  document_id uuid primary key,
  user_id uuid not null references public.users (id) on delete cascade,
  storage_path text not null,
  attempts integer not null default 0 check (attempts >= 0),
  last_error_at timestamptz,
  created_at timestamptz not null default now()
);

alter table public.document_cleanup_jobs enable row level security;
revoke all on public.document_cleanup_jobs from authenticated;
