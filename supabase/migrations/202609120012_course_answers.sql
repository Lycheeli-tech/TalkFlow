create sequence public.course_answer_saved_sequence;

create table public.course_answers (
  id uuid primary key,
  user_id uuid not null references public.users (id) on delete cascade,
  catalog_version text not null default 'course_catalog_v1'
    check (catalog_version = 'course_catalog_v1'),
  course_id text not null check (course_id ~ '^course-(0[1-9]|[12][0-9]|30)$'),
  question_id text not null,
  answer_language text not null check (answer_language in ('ENGLISH', 'CHINESE')),
  status text not null default 'PROCESSING'
    check (status in ('PROCESSING', 'SAVED', 'PROCESSING_FAILED', 'DISCARDED')),
  idempotency_key text not null,
  response_duration_ms integer check (response_duration_ms is null or response_duration_ms >= 0),
  audio_path text,
  audio_content_type text,
  audio_retention_status text not null default 'RETAINED'
    check (audio_retention_status in ('RETAINED', 'PENDING_CLEANUP', 'EXPIRED', 'CLEANUP_FAILED')),
  audio_cleanup_pending boolean not null default false,
  provider_error_code text,
  failure_expires_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  saved_at timestamptz,
  saved_sequence bigint unique,
  confirmed_at timestamptz,
  constraint uq_course_answer_idempotency unique (user_id, idempotency_key),
  constraint uq_course_answer_owner unique (id, user_id),
  constraint course_answers_catalog_question_check check (
    question_id = course_id || '.core'
    or (course_id <> 'course-30' and question_id = course_id || '.follow-up')
  ),
  constraint course_answers_saved_state_check check (
    (status = 'SAVED' and saved_at is not null and saved_sequence is not null)
    or (status <> 'SAVED' and saved_at is null and saved_sequence is null)
  ),
  constraint course_answers_audio_pair_check check (
    (audio_path is null) = (audio_content_type is null)
  ),
  constraint course_answers_failure_expiry_check check (
    (status = 'PROCESSING_FAILED' and failure_expires_at is not null)
    or (status <> 'PROCESSING_FAILED' and failure_expires_at is null)
  )
);

create index course_answers_history_idx
on public.course_answers (user_id, question_id, saved_at desc)
where status = 'SAVED';

create index course_answers_audio_retention_idx
on public.course_answers (user_id, question_id, answer_language, saved_at desc)
where status = 'SAVED' and audio_path is not null;

create index course_answers_failed_expiry_idx
on public.course_answers (failure_expires_at)
where status = 'PROCESSING_FAILED' and audio_path is not null;

create table public.course_transcripts (
  answer_id uuid primary key,
  user_id uuid not null references public.users (id) on delete cascade,
  source_language text not null check (source_language in ('ENGLISH', 'CHINESE')),
  transcript text not null check (length(trim(transcript)) > 0),
  organized_english text,
  stt_provider text not null,
  stt_model text,
  organizer_prompt_version text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint course_transcripts_answer_owner_fk
    foreign key (answer_id, user_id)
    references public.course_answers (id, user_id) on delete cascade
);

create table public.course_feedback (
  answer_id uuid primary key,
  user_id uuid not null references public.users (id) on delete cascade,
  status text not null check (status in ('NOT_REQUESTED', 'PENDING', 'READY', 'FAILED')),
  summary text,
  priority_changes jsonb,
  prompt_version text not null,
  provider_name text,
  model_name text,
  error_code text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint course_feedback_answer_owner_fk
    foreign key (answer_id, user_id)
    references public.course_answers (id, user_id) on delete cascade
);

alter table public.course_answers enable row level security;
alter table public.course_transcripts enable row level security;
alter table public.course_feedback enable row level security;

create policy "users read their own course answers"
on public.course_answers for select
using ((select auth.uid()) = user_id);

create policy "users read their own course transcripts"
on public.course_transcripts for select
using ((select auth.uid()) = user_id);

create policy "users read their own course feedback"
on public.course_feedback for select
using ((select auth.uid()) = user_id);

grant select on public.course_answers to authenticated;
grant select on public.course_transcripts to authenticated;
grant select on public.course_feedback to authenticated;
