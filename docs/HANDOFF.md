# Current Agent Handoff

## Updated

- 2026-09-08
- Branch: `feat/real-daily-learning-loop`
- HEAD: `d004ef1` (`feat: complete phase 2 gate c voice pipeline`)

## Current Task

Phase 2 Gate D — Real Daily Learning Loop activation.

## Why This Task Exists

Gate A–C are complete and merged to `main`. Gate D now validates the existing Daily Session runtime
against the Build Spec's complete Recall → Learn → Imitate → Retrieve → Transfer → Interview → Recap
loop without beginning Gate E/F.

## What Has Been Completed

- Root-caused and fixed the auth chain (stale-token dead end, login-success dead end, stale error
  state) in `frontend/components/app-entry.tsx`, `frontend/lib/api.ts`,
  `frontend/components/onboarding-flow.tsx`. No architecture change; token remains a Supabase
  access token in `sessionStorage` without refresh-token lifecycle.
- Verified in-browser: fresh unauthenticated login form renders; injected stale token → backend
  401 → token removed → UI returns to usable login form (no loop, no dead end).
- Frontend `tsc --noEmit` and `eslint .` pass. Backend confirmed healthy: `/api/v1/entry` returns
  401 with a clear message and correct CORS headers; frontend `.env.local` Supabase URL present.
- Supabase rejects synthetic signup domains (`email_address_invalid`), so account creation needs a
  real user mailbox.

## Current State

Backend (127.0.0.1:8000) and frontend (localhost:3000) are running. Working tree contains the
uncommitted AUTH-01 fix plus pre-existing `frontend/next-env.d.ts` (Next dev-generated; leave it)
and untracked `docs/PROJECT_HANDOFF.md` (cross-agent navigation doc; keep untracked).

## New Gate C Progress

On 2026-09-07, the user manually completed three real English Voice Calibration recordings and
reached Today. Today showed five progress markers and the final Recap awarded `+1 XP`. This is
human-observed browser evidence that the existing calibration and Today completion shell are
reachable. It does not yet prove private audio storage, durable Attempt/transcript/analysis/
assessment records, failure recovery, same-Attempt retry, or reconnection persistence.

After a fresh login/reload, the app resumed at Today. A 375px viewport smoke check had no
horizontal overflow, and no browser console errors or warnings were observed.

A read-only live Supabase aggregate query found two completed Calibration Sessions with three
Attempts each; all six were ANALYZED with audio paths, transcripts, and analysis present, and two
LearnerAssessment rows existed. Private Storage object existence and current-user attribution
still require focused verification.

A recursive read-only listing then found 6 private nested learner-audio objects totaling 1,696,172
bytes. Paths and content were not exposed; exact current-user attribution remains pending.

An anonymous aggregate comparison found database Attempts per user as `[3, 3]` and private Storage
files per user directory as `[3, 3]`, matching the expected three-attempt shape without exposing
IDs or paths.

On 2026-09-08, two independent live database connections each found seven analyzed Attempts with
audio references, transcript, analysis, and a non-empty private-audio load; two LearnerAssessment
rows remain present. No sensitive values were printed. The 4-test focused calibration service suite
also passed: its controlled analyzer outage retains audio/transcript and retries the same Attempt
ID/path without a duplicate. This is service-level evidence, not a live browser fault.

The subsequent real-browser silent-recording check captured `audio/webm;codecs=opus`, persisted a
non-empty private object, and reached live `STT_FAILED`. The initial Retry exposed a transient
Supabase Session Pooler disconnect as `Failed to fetch`. `SQLCalibrationRepository` now retries an
explicitly invalidated connection once before the Attempt is read; the same browser Retry returned
normally to `STT_FAILED` and did not create a duplicate Attempt.

## Next Action

1. Add the minimum Daily turn-based voice/Attempt path needed for evidence-bearing Daily steps.
2. Validate real Daily content, ordered step persistence, provider processing, raw-audio recovery,
   Recap progress, i18n/responsive/console, and reconnection.
3. Create a Gate D checkpoint and stop before Gate E.

## Relevant Files

- `frontend/components/app-entry.tsx`
- `frontend/components/onboarding-flow.tsx`
- `frontend/lib/api.ts`
- `frontend/lib/auth.ts`
- `frontend/components/voice-calibration.tsx`
- `backend/app/api/v1/entry.py`
- `docs/ISSUES.md` (AUTH-01)

## Do Not Change

- No Build Spec edits, no new auth architecture (e.g. refresh-token flow), no provider replacement,
  no realtime voice, M8, V1.5/V2, Gate E/F, unrelated refactor.
- Do not print or commit `.env`/`.env.local` secrets; do not touch `frontend/next-env.d.ts`.

## Verification Still Required

The live Daily Session creation path is confirmed: Day 1, BUILD, 20-minute plan, Bailian-generated
question and language content. The current Today UI only advances passive steps and contains no
Daily voice/Attempt capture; this is the Gate D implementation gap.

## Last Verified Baseline

- `m7-hardening` / `cbfed8f` is the stable Phase 1 baseline; Gate B checkpoint `d16cbc3`.
- Backend 81 tests, Ruff, Gate A live infrastructure, Gate B live Bailian checks passed earlier.
- Auth regression evidence so far: see `docs/ISSUES.md` AUTH-01.

## Git / Recovery Notes

Phase 2 commits are local-only; do not assume pushed. Commit the AUTH-01 fix as one coherent
checkpoint only after the user validates login. Never stage `.env*`.
