alter table public.expressions enable row level security;
alter table public.expression_attempts enable row level security;
alter table public.error_patterns enable row level security;
alter table public.stories enable row level security;
alter table public.retrieval_opportunities enable row level security;

create policy "users manage their own expressions"
on public.expressions for all
using ((select auth.uid()) = user_id)
with check ((select auth.uid()) = user_id);

create policy "users manage their own expression attempts"
on public.expression_attempts for all
using ((select auth.uid()) = user_id)
with check ((select auth.uid()) = user_id);

create policy "users manage their own error patterns"
on public.error_patterns for all
using ((select auth.uid()) = user_id)
with check ((select auth.uid()) = user_id);

create policy "users manage their own stories"
on public.stories for all
using ((select auth.uid()) = user_id)
with check ((select auth.uid()) = user_id);

create policy "users manage their own retrieval opportunities"
on public.retrieval_opportunities for all
using ((select auth.uid()) = user_id)
with check ((select auth.uid()) = user_id);
