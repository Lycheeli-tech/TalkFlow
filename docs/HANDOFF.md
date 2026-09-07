# Current Agent Handoff

## Updated

- 2026-09-07
- Branch: `feat/live-ai-providers`
- HEAD: `d16cbc3`

## Current Task

Complete Phase 2 Gate C — Real Voice Pipeline validation.

## Why This Task Exists

Gate A infrastructure and Gate B Bailian live providers are complete. The remaining proof is the
actual browser turn-based voice path from microphone capture through durable Attempt/audio/transcript/
analysis and recoverable retry.

## What Has Been Completed

- Gate B Bailian text, Qwen3-ASR, Qwen3-TTS, runtime wiring, and TTS→STT round trip passed.
- User listened to and accepted the generated English voice.
- Local backend and frontend were started; browser is at `http://localhost:3000/`.

## Current State

The browser is on the FluentLoop authentication/onboarding entry page. The user has not yet reached
Voice Calibration. Existing user modifications are present in `frontend/components/app-entry.tsx`,
`frontend/lib/api.ts`, and `frontend/next-env.d.ts`; preserve them until reviewed.

## Current Blocker

None in product code. Human browser login/Onboarding and microphone speech are required to continue.

## Next Action

Ask the user to log in or create a test account on the local page and complete Onboarding until the
“Begin voice calibration” screen appears. Then request microphone permission and three short English
answers, one interaction at a time.

## Relevant Files

- `frontend/components/voice-calibration.tsx`
- `frontend/lib/api.ts`
- `backend/app/api/v1/calibration.py`
- `backend/app/services/calibration.py`
- `backend/app/storage/audio.py`
- `backend/app/ai/bailian.py`
- `docs/PHASE2_MVP_ACTIVATION.md`

## Do Not Change

- No Build Spec edits, product redesign, provider replacement, or schema/migration changes.
- No realtime voice, M8, V1.5/V2, Gate D/E/F, or unrelated refactor.
- Do not print or commit `.env` secrets; preserve unrelated user files and current frontend changes.

## Verification Still Required

Real microphone format/upload, private audio persistence, STT/transcript/analysis/assessment,
failure recovery and same-Attempt retry, reconnection, bilingual route smoke, approximately 375 px
viewport, and browser console check.

## Last Verified Baseline

- `m7-hardening` / `cbfed8f` is the stable Phase 1 baseline.
- Gate B checkpoint: `d16cbc3`.
- Backend 81 tests, Ruff, frontend lint/typecheck/build, Gate A live infrastructure, and Gate B live
  Bailian checks passed. Gate C browser microphone path is not verified.

## Git / Recovery Notes

Before Gate C changes, inspect `git status`. Do not touch `frontend/next-env.d.ts` or other user work.
Create one focused checkpoint after Gate C validation; do not merge or push without explicit approval.
