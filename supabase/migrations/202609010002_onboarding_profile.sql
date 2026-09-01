alter table public.users
  add column target_role text,
  add column primary_goal text not null default 'english_interview';

create table public.source_documents (
  id uuid primary key,
  user_id uuid not null references public.users (id) on delete cascade,
  source_type text not null check (source_type in ('resume_pdf', 'background_text')),
  filename text,
  raw_text text not null,
  parse_status text not null default 'ready'
    check (parse_status in ('ready', 'extracted', 'failed')),
  candidate_profile jsonb,
  extractor_version text,
  created_at timestamptz not null default now()
);

create table public.profiles (
  user_id uuid primary key references public.users (id) on delete cascade,
  source_document_id uuid not null references public.source_documents (id) on delete restrict,
  target_role text not null,
  primary_goal text not null default 'english_interview',
  education jsonb not null default '[]'::jsonb,
  work_experience jsonb not null default '[]'::jsonb,
  projects jsonb not null default '[]'::jsonb,
  skills jsonb not null default '[]'::jsonb,
  industries jsonb not null default '[]'::jsonb,
  career_transition text,
  technical_keywords jsonb not null default '[]'::jsonb,
  confirmed_at timestamptz not null,
  updated_at timestamptz not null default now()
);

alter table public.source_documents enable row level security;
alter table public.profiles enable row level security;

create policy "users manage their own source documents"
on public.source_documents for all
using ((select auth.uid()) = user_id)
with check ((select auth.uid()) = user_id);

create policy "users manage their own confirmed profile"
on public.profiles for all
using ((select auth.uid()) = user_id)
with check ((select auth.uid()) = user_id);

grant select, insert, update, delete on public.source_documents to authenticated;
grant select, insert, update, delete on public.profiles to authenticated;
