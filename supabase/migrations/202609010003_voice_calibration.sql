create table public.sessions (
  id uuid primary key,
  user_id uuid not null references public.users (id) on delete cascade,
  session_type text not null check (session_type in ('CALIBRATION', 'DAILY', 'MOCK_INTERVIEW')),
  status text not null default 'IN_PROGRESS' check (status in ('IN_PROGRESS', 'COMPLETED')),
  questions jsonb not null default '[]'::jsonb,
  started_at timestamptz not null default now(),
  completed_at timestamptz
);

create table public.attempts (
  id uuid primary key,
  session_id uuid not null references public.sessions (id) on delete cascade,
  user_id uuid not null references public.users (id) on delete cascade,
  question text not null,
  question_type text not null check (question_type in ('EXPERIENCE', 'MOTIVATION', 'PROJECT')),
  audio_path text not null,
  audio_content_type text not null,
  response_duration_ms integer check (response_duration_ms is null or response_duration_ms >= 0),
  transcript text,
  analysis jsonb,
  status text not null default 'AUDIO_SAVED'
    check (status in ('AUDIO_SAVED', 'STT_FAILED', 'TRANSCRIBED', 'ANALYSIS_FAILED', 'ANALYZED')),
  provider_error text,
  stt_provider text,
  analyzer_version text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (session_id, question_type)
);

create table public.learner_assessments (
  id uuid primary key,
  session_id uuid not null unique references public.sessions (id) on delete restrict,
  user_id uuid not null references public.users (id) on delete cascade,
  fluency text not null check (fluency in ('NEEDS_WORK', 'DEVELOPING', 'FUNCTIONAL', 'STRONG')),
  naturalness text not null check (naturalness in ('NEEDS_WORK', 'DEVELOPING', 'FUNCTIONAL', 'STRONG')),
  grammar text not null check (grammar in ('NEEDS_WORK', 'DEVELOPING', 'FUNCTIONAL', 'STRONG')),
  retrieval text not null check (retrieval in ('NEEDS_WORK', 'DEVELOPING', 'FUNCTIONAL', 'STRONG')),
  structure text not null check (structure in ('NEEDS_WORK', 'DEVELOPING', 'FUNCTIONAL', 'STRONG')),
  strengths jsonb not null default '[]'::jsonb,
  primary_focus text not null,
  secondary_focus text,
  observed_patterns jsonb not null default '[]'::jsonb,
  assessment_version text not null,
  created_at timestamptz not null default now()
);

alter table public.sessions enable row level security;
alter table public.attempts enable row level security;
alter table public.learner_assessments enable row level security;

create policy "users manage their own sessions" on public.sessions for all
using ((select auth.uid()) = user_id) with check ((select auth.uid()) = user_id);
create policy "users manage their own attempts" on public.attempts for all
using ((select auth.uid()) = user_id) with check ((select auth.uid()) = user_id);
create policy "users manage their own learner assessments" on public.learner_assessments for all
using ((select auth.uid()) = user_id) with check ((select auth.uid()) = user_id);

grant select, insert, update, delete on public.sessions to authenticated;
grant select, insert, update, delete on public.attempts to authenticated;
grant select, insert, update, delete on public.learner_assessments to authenticated;

insert into storage.buckets (id, name, public)
values ('learner-audio', 'learner-audio', false)
on conflict (id) do nothing;

create policy "users read their own learner audio" on storage.objects for select
using (bucket_id = 'learner-audio' and split_part(name, '/', 1)::uuid = (select auth.uid()));
create policy "users insert their own learner audio" on storage.objects for insert
with check (bucket_id = 'learner-audio' and split_part(name, '/', 1)::uuid = (select auth.uid()));
create policy "users delete their own learner audio" on storage.objects for delete
using (bucket_id = 'learner-audio' and split_part(name, '/', 1)::uuid = (select auth.uid()));
