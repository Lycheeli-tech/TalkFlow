alter table public.attempts
  drop constraint if exists attempts_question_type_check;

alter table public.attempts
  add constraint attempts_question_type_check
  check (
    question_type in (
      'EXPERIENCE',
      'MOTIVATION',
      'PROJECT',
      'QUICK_REVIEW',
      'RECALL',
      'IMITATE',
      'RETRIEVE',
      'TRANSFER',
      'INTERVIEW'
    )
  );
