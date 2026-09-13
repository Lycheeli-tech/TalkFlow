-- Additive Course Core P6 state boundary; no Legacy schema changes.
alter table public.course_transcripts add column organizer_provider text;
alter table public.course_transcripts add column organizer_model text;
alter table public.course_transcripts add column fidelity_prompt_version text;
alter table public.course_answers drop constraint course_answers_status_check;
alter table public.course_answers add constraint course_answers_status_check
  check (status in ('PROCESSING', 'AWAITING_CONFIRMATION', 'SAVED', 'PROCESSING_FAILED', 'DISCARDED'));

alter table public.course_answers add constraint course_answers_chinese_confirmation_check
  check (
    (status <> 'AWAITING_CONFIRMATION' or answer_language = 'CHINESE')
    and (answer_language <> 'CHINESE' or status <> 'SAVED' or confirmed_at is not null)
  );

-- The API is the only product write boundary. Authenticated clients retain owner-filtered reads.
create index course_answers_draft_recovery_idx
  on public.course_answers (user_id, question_id, created_at desc)
  where answer_language = 'CHINESE' and status in
    ('PROCESSING', 'PROCESSING_FAILED', 'AWAITING_CONFIRMATION');

-- Even an application bug cannot commit a ready/saved Chinese Answer without both immutable texts.
create function public.validate_chinese_answer_texts()
returns trigger language plpgsql security definer set search_path = '' as $$
declare answer_id_to_check uuid;
begin
  if tg_table_name = 'course_answers' then
    answer_id_to_check := new.id;
  else
    answer_id_to_check := coalesce(new.answer_id, old.answer_id);
  end if;
  if exists (select 1 from public.course_answers a
    where a.id = answer_id_to_check and a.answer_language = 'CHINESE'
    and a.status in ('AWAITING_CONFIRMATION', 'SAVED')
    and not exists (select 1 from public.course_transcripts t
      where t.answer_id = a.id and t.user_id = a.user_id and t.source_language = 'CHINESE'
      and length(trim(t.transcript)) > 0 and length(trim(t.organized_english)) > 0)) then
    raise exception 'Ready Chinese Answer requires both Chinese and organized English texts';
  end if;
  return null;
end;
$$;

create constraint trigger course_chinese_answer_texts_check
after insert or update on public.course_answers
deferrable initially deferred for each row execute function public.validate_chinese_answer_texts();
create constraint trigger course_chinese_transcript_texts_check
after insert or update or delete on public.course_transcripts
deferrable initially deferred for each row execute function public.validate_chinese_answer_texts();
revoke all on function public.validate_chinese_answer_texts() from public, authenticated;
