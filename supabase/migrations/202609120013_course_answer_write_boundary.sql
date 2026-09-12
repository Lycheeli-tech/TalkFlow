drop policy if exists "users manage their own course answers" on public.course_answers;

drop policy if exists "users read their own course answers" on public.course_answers;

create policy "users read their own course answers"
on public.course_answers for select
using ((select auth.uid()) = user_id);

revoke insert, update, delete on public.course_answers from authenticated;
grant select on public.course_answers to authenticated;
