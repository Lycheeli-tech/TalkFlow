# Current Agent Handoff

## Updated

- 2026-09-12
- Branch: `codex/course-core-stage-3`
- Checkpoint: Course Core Stage 3 English Answer closeout, tagged `course-core-stage-3`

## Current State

Course Core Stage 3 is complete and waiting for product-owner review. Course 11 alone is enabled for
the English Answer minimum loop; all other Courses remain read-only. Do not merge, push, or begin
Stage 4 without explicit instruction.

Legacy remains frozen at `8cc986d` and unmounted from the default runtime. Historical regressions use
the explicit rollback test app only. `docs/CURRENT_MILESTONE_V1.md` contains full stage evidence.

## Stage 3 Result

- Dedicated Course Answer, Transcript, and Feedback models/tables/RLS/repository/service/API/client
  exist outside Legacy. Course authentication and AI provider dependencies no longer import the
  Legacy dependency graph.
- Authenticated database clients can RLS-read only their own Course data and cannot bypass API state
  transitions with direct inserts, updates, or deletes.
- Course 11 supports free core/follow-up selection, exact Catalog TTS, turn-based English recording,
  original-audio-first persistence, final STT, immutable transcript display, History, replay,
  idempotent submission, and same-Answer recovery.
- Recording blocks question/global navigation and browser leave; History remains openable but audio
  playback is disabled while recording. Playback sources are mutually exclusive.
- Saved audio retention is newest two per user/question/language. Failed audio expires three days
  after the most recent processing failure (ADR-028), with retryable cleanup state.
- No About Me, Memory, Chinese Answer, AI help/Feedback generation, remaining-Course answering,
  completion, unlocking, auto-next, mastery, XP/streak, Daily, or Practice V2 behavior was added.

## Verification Evidence

- Backend: 121 passed, 2 opt-in real PostgreSQL tests passed separately; Ruff check passed.
- Frontend: TypeScript, ESLint, production build passed.
- Real database: two-user RLS isolation, no authenticated direct writes, and before/after equality for
  `current_day`, `current_phase`, XP, streak, `sessions`, `attempts`, `expressions`,
  `expression_attempts`, and `retrieval_opportunities`.
- Real service smoke: Catalog TTS, Supabase private storage, Bailian STT, Answer save, History, replay,
  and three-save `[RETAINED, RETAINED, EXPIRED]` behavior passed; expired audio retained transcript.
- Browser: authenticated desktop and 375px layouts, free question switching, History/replay, left/right
  drawers, and no horizontal overflow passed. Automated device microphone approval was intentionally
  not granted; the physical microphone button path remains a manual smoke item.
- Disposable account, three Answers/transcripts, and two remaining private audio objects were deleted.

## Database State

- `202609120012_course_answers.sql` and `202609120013_course_answer_write_boundary.sql` are applied and
  recorded in the configured test database.
- The first migration was applied during an attempted rollback-only DDL test because raw asyncpg DDL
  bypassed the SQLAlchemy transaction. It succeeded fully; migration metadata was repaired immediately.
- The integration test now requires pre-applied migrations and uses an explicit driver transaction for
  RLS checks. It no longer executes DDL.
- No Course test rows or private test audio remain. No Legacy migration or data changed.

## Known Limitations

- Physical microphone capture still needs a user-approved manual browser smoke; unit/static contracts
  and the real audio-upload pipeline cover the remaining recording flow.
- Feedback is schema-only in Stage 3; generation belongs to Stage 5. About Me/Memory is Stage 4,
  Chinese Answer is Stage 6, other Courses are Stage 7, and Practice V2 is Stage 8.
- Auth session lifecycle remains sessionStorage-based. One existing Starlette/httpx warning remains.
- Preserve the unrelated user change in `frontend/next-env.d.ts`; it is not part of Stage 3.

## Next Action

Review Stage 3. Do not merge, push, or start Stage 4 without explicit product-owner instruction.
