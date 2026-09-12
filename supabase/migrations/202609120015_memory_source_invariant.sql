create function public.assert_memory_item_has_source()
returns trigger
language plpgsql
set search_path = ''
as $$
declare
  candidate_id uuid;
begin
  candidate_id := case when tg_table_name = 'memory_items' then new.id else old.memory_id end;
  if exists (select 1 from public.memory_items where id = candidate_id)
     and not exists (select 1 from public.memory_sources where memory_id = candidate_id) then
    raise exception 'memory item % must have at least one source', candidate_id;
  end if;
  if tg_table_name = 'memory_sources' and tg_op = 'UPDATE' and new.memory_id <> old.memory_id then
    if exists (select 1 from public.memory_items where id = new.memory_id)
       and not exists (select 1 from public.memory_sources where memory_id = new.memory_id) then
      raise exception 'memory item % must have at least one source', new.memory_id;
    end if;
  end if;
  return null;
end;
$$;

create constraint trigger memory_items_require_source
after insert or update on public.memory_items
deferrable initially deferred
for each row execute function public.assert_memory_item_has_source();

create constraint trigger memory_source_removal_keeps_item_sourced
after delete or update of memory_id on public.memory_sources
deferrable initially deferred
for each row execute function public.assert_memory_item_has_source();
