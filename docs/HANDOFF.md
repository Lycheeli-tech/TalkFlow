# Current Agent Handoff

## Updated

- 2026-09-13
- Branch: `codex/course-core-stage-6`
- Checkpoint: Stage 6 implementation checkpoint; baseline `course-core-stage-5` / `9f08381`

## Current State

Course Core Stage 5 is COMPLETE and merged/pushed. Stage 6 is authorized and IN PROGRESS.
TBD-010 is explicitly approved: uploaded unconfirmed Chinese Drafts support refresh recovery (ADR-031).
Course 11 remains the only Answer-enabled Course. Do not close P6, merge/push, or begin P7 prematurely.

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
- P6 migration `202609130020` passed local full-sequence validation and real transactional tests;
  all P6 DDL/data were rolled back. It has NOT been persistently applied/registered.

## Stage 6 Checkpoint

- Dedicated Chinese organizer + fidelity Prompt, exact citation/numerical validation, immutable dual texts,
  owner-scoped Draft recovery, confirmation/discard APIs, and frontend Chinese recorder/guide/confirmation UI.
- Pending Drafts never enter History, Feedback, or Memory. Saved audio retention serializes the whole
  owner/question/language group; failed organizer retries do not re-transcribe an existing Chinese source.
- Backend 151 passed, Ruff check/format passed. Real PostgreSQL + Bailian first run: 2 passed.
- Frontend TypeScript/lint/build passed including microphone-unmount safety. Final dual-text migration
  constraint rerun: 1 passed. The last fidelity Prompt tracking column still needs real-database recheck.
- Real Chinese audio/browser release gates and persistent test-environment migration rollout remain.

## Known Limitations

- Chinese Answer implementation is P6-only; P7/P8 were not added. P6 is not yet release-accepted.
- Auth session lifecycle remains sessionStorage-based. One existing Starlette/httpx warning remains.
- Preserve the unrelated user change in `frontend/next-env.d.ts`; exclude it from P6 commits and restore
  its `.next/dev/types` imports after production builds regenerate it.

## Next Action

Resume P6 from its implementation checkpoint: verify final patches, exercise real Chinese audio upload,
organization, confirmation/discard and refresh recovery, then authenticated desktop/375px recording smoke.
Apply/register the new migration only in the configured test environment with a reviewed rollout gate.
Record final acceptance evidence before creating a P6 completion tag; do not start P7.
