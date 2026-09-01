create table if not exists public.expressions (
  id uuid primary key,
  user_id uuid not null references public.users(id) on delete cascade,
  text text not null,
  meaning text not null,
  source_type text not null check (source_type in ('CURRICULUM', 'ATTEMPT', 'USER')),
  source_id uuid,
  status text not null default 'NEW' check (status in ('NEW', 'LEARNING', 'RECALLED', 'TRANSFERRED', 'MASTERED')),
  successful_recall integer not null default 0,
  failed_recall integer not null default 0,
  transfer_success integer not null default 0,
  next_review_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists public.expression_attempts (
  id uuid primary key,
  expression_id uuid not null references public.expressions(id) on delete cascade,
  attempt_id uuid not null references public.attempts(id) on delete cascade,
  session_id uuid not null references public.sessions(id) on delete cascade,
  user_id uuid not null references public.users(id) on delete cascade,
  context text not null,
  retrieval_type text not null check (retrieval_type in ('LEARNING', 'RECALL', 'TRANSFER')),
  hint_used boolean not null default false,
  independent_evidence boolean not null default false,
  usage_correct boolean not null default false,
  result text not null check (result in ('SUCCESS', 'FAILURE')),
  created_at timestamptz not null default now()
);

create table if not exists public.error_patterns (
  id uuid primary key,
  user_id uuid not null references public.users(id) on delete cascade,
  pattern_type text not null,
  original_example text not null,
  preferred_expression text,
  occurrence_count integer not null default 1,
  successful_correction_count integer not null default 0,
  status text not null default 'CANDIDATE' check (status in ('CANDIDATE', 'ACTIVE', 'IMPROVING', 'RESOLVED')),
  first_seen timestamptz not null default now(),
  last_seen timestamptz not null default now()
);

create table if not exists public.stories (
  id uuid primary key,
  user_id uuid not null references public.users(id) on delete cascade,
  title text not null,
  content text not null,
  source_document_id uuid references public.source_documents(id) on delete restrict,
  confirmed_by_user boolean not null default false check (confirmed_by_user = true),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index if not exists expression_attempts_user_expression_idx
  on public.expression_attempts (user_id, expression_id, created_at);
