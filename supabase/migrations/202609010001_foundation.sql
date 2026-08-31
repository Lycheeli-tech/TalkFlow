create table public.users (
  id uuid primary key references auth.users (id) on delete cascade,
  interface_language text not null default 'en'
    check (interface_language in ('en', 'zh-CN')),
  support_language text not null default 'en'
    check (support_language in ('en', 'zh-CN')),
  default_session_length smallint not null default 20
    check (default_session_length in (10, 20, 30, 60)),
  coaching_style text not null default 'supportive'
    check (coaching_style in ('supportive', 'professional', 'strict')),
  timezone text not null default 'UTC',
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

alter table public.users enable row level security;

create policy "users can read their own state"
on public.users for select
using ((select auth.uid()) = id);

create policy "users can update their own state"
on public.users for update
using ((select auth.uid()) = id)
with check ((select auth.uid()) = id);

create policy "users can delete their own state"
on public.users for delete
using ((select auth.uid()) = id);

grant select, update, delete on public.users to authenticated;

create function public.handle_new_user()
returns trigger
language plpgsql
security definer
set search_path = ''
as $$
begin
  insert into public.users (id) values (new.id)
  on conflict (id) do nothing;
  return new;
end;
$$;

create trigger on_auth_user_created
after insert on auth.users
for each row execute procedure public.handle_new_user();
