# Current Agent Handoff

## Updated

- 2026-09-13
- Branch: `codex/course-core-stage-6`
- Checkpoint: `course-core-stage-6`; baseline `course-core-stage-5` / `9f08381`

## Current State

Course Core Stage 5 is COMPLETE and merged/pushed. Stage 6 is COMPLETE locally, awaiting review.
TBD-010 is explicitly approved: uploaded unconfirmed Chinese Drafts support refresh recovery (ADR-031).
Course 11 remains the only Answer-enabled Course. Do not merge/push or begin P7 without authorization.

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
- P6 migration `202609130020` is persistently applied/registered in the authorized test database;
  migration Legacy progress/field snapshots were unchanged.

## Stage 6 Checkpoint

- Dedicated Chinese organizer + fidelity Prompt, exact citation/numerical validation, immutable dual texts,
  owner-scoped Draft recovery, confirmation/discard APIs, and frontend Chinese recorder/guide/confirmation UI.
- Pending Drafts never enter History, Feedback, or Memory. Saved audio retention serializes the whole
  owner/question/language group; failed organizer retries do not re-transcribe an existing Chinese source.
- Backend 151 passed, Ruff check/format passed. Real PostgreSQL + Bailian first run: 2 passed.
- Frontend TypeScript/lint/build passed including microphone-unmount safety. Final dual-text migration
  constraint rerun: 1 passed. The last fidelity Prompt tracking column still needs real-database recheck.
- Real synthetic Chinese TTS→ASR→organizer/fidelity→Draft→confirmation passed with immutable dual texts.
- Desktop 1280px refresh/resume/confirm and 375px dual texts/History/discard/reanswer passed.
- Shared STT defaults remain English; Chinese runtime now explicitly uses zh. Supabase exact-prefix
  deletion and late cleanup failure protection were corrected; oldest audio EXPIRED, latest two RETAINED.
- Final backend 153 passed; combined real integrations 9 passed; frontend lint/typecheck/build passed.
- Device microphone gate is now passed: user-operated IAB recorded and saved two English Answers and
  one confirmed Chinese Answer (31,226 ms, WebM/Opus), with real Bailian STT/organizer and READY Chinese
  Feedback. Reload preserved three History entries, Chinese dual texts, duration and Question selection.
- Disposable Auth user/Answers/private audio/local credentials were removed; persisted Answer and
  Storage object counts are zero. New late-cleanup guard real PostgreSQL rerun: 1 passed.

## Known Limitations

- Chinese Answer implementation is P6-only; P7/P8 were not added. P6 awaits review before merge/push.
- Auth session lifecycle remains sessionStorage-based. One existing Starlette/httpx warning remains.
- Preserve the unrelated user change in `frontend/next-env.d.ts`; exclude it from P6 commits and restore
  its `.next/dev/types` imports after production builds regenerate it.

## Next Action

2026-09-13 resume: backend 153 passed / 10 opt-in skipped, Ruff check/format, frontend
TypeScript/lint/production build, 20-migration validation, and read-only live P6 registry verification
passed. No implementation changes, migrations, or disposable data were added. Chrome exists natively
but its connector is unavailable; native sky activation/read was rejected by automatic approval because
the required interface is cua_repl (whose native control is disabled). See COURSE-06; do not bypass it.

Local acceptance servers remain running: production frontend `127.0.0.1:3100`, backend
`127.0.0.1:8000`; Course 11 and health return 200. Backend CORS permits localhost/127.0.0.1:3100.
Processes started for this resume: backend PID 9480; frontend is the `next start --port 3100` process.
Stop only these acceptance services after device evidence is collected; do not stop unrelated processes.

Login recovery: user clarified their failed login was for a disposable account with no real inbox.
`prepare-device` now creates an already-confirmed temporary user without synthetic audio. Password
login and authenticated Draft API returned success. Keep the replacement until device smoke finishes.
Recovery state is in OS temp: `fluentloop-p6-607ae176946542cc96fed5b0c6d1cf67.json`.
Do not commit its contents; pass its absolute path to the existing `cleanup --state` action afterward.

User-operated Chrome smoke at `http://localhost:3100/courses/course-11`:
1. Sign in, open Chinese guide, start recording and approve microphone if requested.
2. Speak a short Chinese answer using only actual facts; while recording verify Question/navigation
   locks, no Transcript, playback disabled, and opening/closing History does not stop the timer.
3. Finish recording; verify Chinese Transcript plus organized English appear and History stays unchanged.
4. Refresh, resume the Draft, verify both texts, then confirm; verify exactly one saved History entry,
   unchanged Question selection, and no forced English recording. Repeat confirmation must not duplicate.
5. Verify recording/stop at 375px with both drawers and no horizontal overflow; a second Draft can be
   discarded through the explicit confirmation and must not enter History.

Final state supersedes the pending-device instructions above: user device recording passed and P6 is
locally COMPLETE. `CURRENT_MILESTONE_V1.md` records evidence and its limits. Prior tests cover
recording/navigation guards and 375px Draft flows; not every user action was directly observed.
Three saved device Answers and three private audio objects remain only for review in the disposable
account; cleanup its OS-temp state after review. Do not stop services or delete review data prematurely.
Next: product-owner review only; do not merge/push or start P7 without explicit authorization.
