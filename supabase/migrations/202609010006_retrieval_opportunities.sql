create table public.retrieval_opportunities (
  id uuid primary key,
  user_id uuid not null references public.users(id) on delete cascade,
  expression_id uuid not null,
  session_id uuid not null,
  question_family text not null,
  question_text text not null,
  retrieval_type text not null default 'TRANSFER' check (retrieval_type in ('RECALL', 'TRANSFER')),
  status text not null default 'CREATED' check (status in ('CREATED', 'CONSUMED', 'EXPIRED')),
  created_at timestamptz not null default now(),
  consumed_at timestamptz,
  foreign key (expression_id, user_id) references public.expressions(id, user_id) on delete cascade,
  foreign key (session_id, user_id) references public.sessions(id, user_id) on delete cascade
);

create unique index retrieval_opportunity_open_target_idx
  on public.retrieval_opportunities (user_id, expression_id, session_id)
  where status = 'CREATED';

alter table public.expression_attempts
  add column retrieval_opportunity_id uuid unique
    references public.retrieval_opportunities(id) on delete restrict;
