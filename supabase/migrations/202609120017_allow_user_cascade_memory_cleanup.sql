create or replace function public.assert_memory_item_has_source()
returns trigger
language plpgsql
set search_path = ''
as $$
declare
  candidate_id uuid;
  candidate_user_id uuid;
begin
  if tg_table_name = 'memory_items' then
    candidate_id := new.id;
    candidate_user_id := new.user_id;
  else
    candidate_id := old.memory_id;
    candidate_user_id := old.user_id;
  end if;

  -- Parent-account deletion owns the complete cascade and must not be blocked by
  -- a child invariant whose rows are being removed in the same statement.
  if not exists (select 1 from public.users where id = candidate_user_id) then
    return null;
  end if;

  if exists (select 1 from public.memory_items where id = candidate_id)
     and not exists (select 1 from public.memory_sources where memory_id = candidate_id) then
    raise exception 'memory item % must have at least one source', candidate_id;
  end if;

  if tg_table_name = 'memory_sources' then
    if tg_op = 'UPDATE' and new.memory_id <> old.memory_id then
      if exists (select 1 from public.memory_items where id = new.memory_id)
         and not exists (select 1 from public.memory_sources where memory_id = new.memory_id) then
        raise exception 'memory item % must have at least one source', new.memory_id;
      end if;
    end if;
  end if;
  return null;
end;
$$;
