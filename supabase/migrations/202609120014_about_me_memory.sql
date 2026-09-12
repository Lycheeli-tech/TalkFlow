create table public.about_me_profiles (
  user_id uuid primary key references public.users (id) on delete cascade,
  supplemental_facts jsonb not null default '[]'::jsonb
    check (jsonb_typeof(supplemental_facts) = 'array'),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table public.target_roles (
  id uuid primary key,
  user_id uuid not null references public.users (id) on delete cascade,
  role_name text not null check (length(trim(role_name)) between 1 and 160),
  created_at timestamptz not null default now(),
  constraint uq_target_role_owner unique (id, user_id),
  constraint uq_target_role_name unique (user_id, role_name)
);

create table public.memory_items (
  id uuid primary key,
  user_id uuid not null references public.users (id) on delete cascade,
  content text not null check (length(trim(content)) between 1 and 4000),
  normalized_content text not null check (length(trim(normalized_content)) > 0),
  extractor_prompt_version text not null,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint uq_memory_item_owner unique (id, user_id)
);

create index memory_items_owner_updated_idx
on public.memory_items (user_id, updated_at desc);

create table public.memory_sources (
  id uuid primary key,
  memory_id uuid not null,
  user_id uuid not null references public.users (id) on delete cascade,
  source_type text not null
    check (source_type in ('PROFILE', 'SOURCE_DOCUMENT', 'USER_INPUT', 'COURSE_ANSWER')),
  source_id uuid not null,
  source_excerpt text not null check (length(trim(source_excerpt)) between 1 and 2000),
  source_field_path text,
  created_at timestamptz not null default now(),
  constraint memory_sources_item_owner_fk
    foreign key (memory_id, user_id)
    references public.memory_items (id, user_id) on delete cascade,
  constraint uq_memory_source unique (
    memory_id, source_type, source_id, source_excerpt, source_field_path
  )
);

create index memory_sources_source_idx
on public.memory_sources (user_id, source_type, source_id);

create table public.course_audio_cleanup_jobs (
  answer_id uuid primary key,
  user_id uuid not null references public.users (id) on delete cascade,
  audio_path text not null,
  attempts integer not null default 0 check (attempts >= 0),
  last_error_at timestamptz,
  created_at timestamptz not null default now()
);

alter table public.about_me_profiles enable row level security;
alter table public.target_roles enable row level security;
alter table public.memory_items enable row level security;
alter table public.memory_sources enable row level security;
alter table public.course_audio_cleanup_jobs enable row level security;

create policy "users read their own about me profile"
on public.about_me_profiles for select using ((select auth.uid()) = user_id);
create policy "users read their own target roles"
on public.target_roles for select using ((select auth.uid()) = user_id);
create policy "users read their own memory items"
on public.memory_items for select using ((select auth.uid()) = user_id);
create policy "users read their own memory sources"
on public.memory_sources for select using ((select auth.uid()) = user_id);

revoke insert, update, delete on public.about_me_profiles from authenticated;
revoke insert, update, delete on public.target_roles from authenticated;
revoke insert, update, delete on public.memory_items from authenticated;
revoke insert, update, delete on public.memory_sources from authenticated;
revoke all on public.course_audio_cleanup_jobs from authenticated;

grant select on public.about_me_profiles to authenticated;
grant select on public.target_roles to authenticated;
grant select on public.memory_items to authenticated;
grant select on public.memory_sources to authenticated;
