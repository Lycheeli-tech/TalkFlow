# FluentLoop Project Status

## Last Updated

- 2026-09-07
- Branch: `feat/live-ai-providers`
- HEAD: `d16cbc3` (`docs: complete phase 2 gate b`)

## Product

FluentLoop (repository: TalkFlow) turns a learner's real experience into spoken English interview
practice. The MVP proves a Recall → Learn → Imitate → Retrieve → Transfer → Interview → Recap loop
with durable, evidence-based progress.

## Current Lifecycle

M0–M7 implementation is complete. The project is now in Phase 2 MVP Activation / Live Integration;
deployment and real-device validation follow the activation gates. No Milestone 8 exists.

## Current Work

- Phase: Phase 2 — MVP Activation
- Gate: C — Real Voice Pipeline
- Status: IN PROGRESS
- Objective: validate browser microphone recording, private audio upload, Attempt persistence, Bailian
  ASR/TTS/analysis, recovery/retry, and real browser/mobile behavior.

## Stable Baseline

Phase 1 stable baseline is tag `m7-hardening` at merge commit `cbfed8f`. Phase 2 Gate A and B local
checkpoints are `e2615ca` and `d16cbc3`. Phase 2 commits have not been assumed pushed; verify remote
state before any merge or push.

## Implemented

- Onboarding/Profile, confirmed-profile Memory Gate, structured memory/mastery/review/error rules.
- Turn-based Voice Calibration with raw audio, transcript, analysis, assessment, and retry semantics.
- Daily Session shell and deterministic planner; Practice, Quick Review, Journey, My English, XP/Streak.
- Cross-session RetrievalOpportunity and trusted verification path.
- Supabase PostgreSQL/Auth/Storage runtime validation and RLS/user isolation.
- Bailian text, Qwen3-ASR, and Qwen3-TTS runtime adapters behind provider interfaces.

## Not Yet Activated / Not Yet Complete

- Gate C real browser voice pipeline is unfinished.
- Gate D real Daily Learning Loop, Gate E cross-session live aha, and Gate F local MVP acceptance are not started.
- Deployment-host setup and real-device coverage remain future activation work.

## Current Blockers

No confirmed product defect. Gate C is waiting for a real browser login/Onboarding path and human
microphone interaction before its live acceptance checks can complete.

## Next Steps

1. Preserve current user changes and confirm local backend/frontend services.
2. Reach Voice Calibration in the browser with a test account.
3. Validate three real recordings, TTS/STT, private Storage, persistence, retry, and reconnection.
4. Run focused bilingual, 375 px, navigation, and console checks; update Gate C documents.
5. Create a checkpoint and stop for review; do not start Gate D automatically.

## Verification Snapshot

- Backend: 81 passed after Gate B provider work; prior M7 full suite was 80 passed.
- Ruff format/check: passed.
- Frontend ESLint, TypeScript, and production build: passed during M7/Gate B validation.
- Ten live Supabase migrations and provisioning/RLS/storage/reconnection probes: passed in Gate A.
- Bailian live text, TTS→STT, and human voice acceptance: passed in Gate B.
- Gate C real browser microphone/upload/retry validation: not yet verified.

## Source of Truth

- Build Spec: authoritative product/architecture specification.
- `DECISIONS.md`: stable architecture decisions.
- `PHASE2_MVP_ACTIVATION.md`: execution gates and acceptance state.
- `PROJECT_STATUS.md`: compact project dashboard.
- `HANDOFF.md`: immediate operational context.
- `ISSUES.md`: debugging and known-issue continuity.
- `CURRENT_MILESTONE.md`: milestone history and current lifecycle notes.
