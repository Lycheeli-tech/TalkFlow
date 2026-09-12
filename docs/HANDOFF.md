# Current Agent Handoff

## Updated

- 2026-09-12
- Branch: `codex/course-core-stage-4`
- Checkpoint: Course Core Stage 4 About Me and AI Memory closeout, tagged `course-core-stage-4`

## Current State

Course Core Stage 4 is complete and waiting for product-owner review. Optional About Me and the new
source-validated AI Memory are enabled; Course 11 remains the only Answer-enabled Course. Do not
merge, push, or begin Stage 5 without explicit instruction.

Legacy remains frozen at `8cc986d` and unmounted from the default runtime. Historical regressions use
the explicit rollback test app only. `docs/CURRENT_MILESTONE_V1.md` contains full stage evidence.

## Stage 4 Result

- Dedicated About Me profile, target-role, Memory item/source, cleanup queue, repository, service, API,
  client, and UI boundaries exist outside Legacy. About Me is optional and supports multiple roles,
  multiple private Resume sources, supplemental facts, and all-Memory view/delete.
- `memory_decision_v1` constrains AI to CREATE/UPDATE/MERGE/IGNORE. Deterministic validation controls
  ownership, source IDs/types/field paths, exact excerpts, target Memories, and transactional writes;
  the database forbids source-less Memory.
- Source deletion removes only matching links and preserves multi-source Memory until its last source
  disappears. Answer deletion also removes Transcript/Feedback, related Memory sources, and private audio.
- Answer audio and Resume object deletion use durable idempotent cleanup jobs so storage failure never
  restores deleted product state and remains retryable.
- No Chinese Answer, AI Course help/Feedback generation, remaining-Course answering, completion,
  unlocking, auto-next, mastery, XP/streak, Daily, or Practice V2 behavior was added.

## Verification Evidence

- Backend: 130 passed, 6 opt-in real PostgreSQL tests passed separately; Ruff format/check passed.
- Frontend: TypeScript, ESLint, production build passed.
- Real database: four Memory actions, four source types, exact excerpt/ownership rejection, source-less
  rejection, multi-source deletion, two-user RLS, no authenticated direct writes, and equality for
  `current_day`, `current_phase`, XP, streak, `sessions`, `attempts`, `expressions`,
  `expression_attempts`, and `retrieval_opportunities`.
- Real service smoke: Bailian returned a validated CREATE for synthetic Course Answer content; two
  synthetic PDFs completed Supabase private upload/parse/list/delete with zero cleanup jobs.
- Browser: authenticated About Me empty state, multiple roles, Memory provenance, supplemental facts,
  bilingual desktop and 375px layout, direct Courses access, no overflow, and no console errors passed.
- Disposable accounts, P4 rows, Answers, Memories, documents, and private objects were deleted.

## Database State

- P4 migrations `202609120014` through `202609120019` are applied and recorded in the configured test
  database in addition to the P3 migrations.
- Integration tests require pre-applied migrations and use explicit transactions or fully cleaned
  synthetic rows. No Course/P4 test rows, test accounts, or private test objects remain.
- No Legacy migration or data changed.

## Known Limitations

- Memory currently displays source type/excerpt but no source-object detail link. Feedback generation
  belongs to Stage 5,
  Chinese Answer is Stage 6, other Courses are Stage 7, and Practice V2 is Stage 8.
- Auth session lifecycle remains sessionStorage-based. One existing Starlette/httpx warning remains.
- Preserve the unrelated user change in `frontend/next-env.d.ts`; it is not part of Stage 4.

## Next Action

Review Stage 4. Do not merge, push, or start Stage 5 without explicit product-owner instruction.
