# Current Agent Handoff

## Updated

- 2026-09-13
- Branch: `codex/course-core-stage-5`
- Checkpoint: `course-core-stage-5`; implementation verified and product UI approved

## Current State

Course Core Stage 5 is COMPLETE. The product owner approved TBD-003/TBD-004 and explicitly authorized
merge/push on 2026-09-13. Course 11 remains the only Answer-enabled Course.
Do not begin Stage 6 without explicit instruction.

Legacy remains frozen at `8cc986d` and unmounted from the default runtime. Historical regressions use
the explicit rollback test app only. `docs/CURRENT_MILESTONE_V1.md` contains full stage evidence.

## Stage 5 Result

- Bounded Course Context Builder, three on-demand support APIs, four versioned prompts, structured
  provider contracts, Answer-scoped Feedback and idempotent retry are implemented outside Legacy.
- Approved UI places hints, materials, reference answer, Feedback, and History in one mutually exclusive
  right assistant panel. Recorder state remains independent; desktop uses three columns and mobile a drawer.
- Feedback validates exact Transcript quotes and rejects source-external numbers. Real-provider testing
  led to a deterministic no-context reference template and exact-source validation for grounded segments.
- No Chinese Answer, remaining-Course answering, completion, unlocking, auto-next, mastery, XP/streak,
  Daily, Practice V2, or general AI Coach Orchestrator was added.

## Verification Evidence

- Backend: 141 passed; Ruff format/check passed. Seven combined real PostgreSQL tests passed; final P5
  integration rerun passed after context hardening.
- Frontend: TypeScript, ESLint, and production build passed.
- Real Bailian: structured hints, safe no-context reference template, source-grounded reference path,
  exact-quote Feedback, initial failure isolation, and successful retry were exercised.
- Browser: authenticated real hint/reference/Feedback panels passed. Headless Chrome measured 1280px
  three-column geometry and 375px fixed drawer with no horizontal overflow or console errors.
- Disposable Auth user, Answer, Feedback, local services, and temporary Chrome profile were removed.

## Database State

- No Stage 5 migration is required; `course_feedback` was intentionally created in Stage 3.
- Integration tests confirmed single-row Feedback retry and no Legacy field/table mutation.
- No Stage 5 test rows or test accounts remain; no Legacy migration or data changed.

## Known Limitations

- Chinese Answer is Stage 6, other Courses are Stage 7, and Practice V2 is Stage 8; none was added.
- Auth session lifecycle remains sessionStorage-based. One existing Starlette/httpx warning remains.
- Preserve the unrelated user change in `frontend/next-env.d.ts`; it is not part of Stage 5.

## Next Action

Complete the authorized merge/push of Stage 5 and its checkpoint tag, then stop. ADR-030 records the
approved panel structure. Stage 6 requires a new explicit instruction.
