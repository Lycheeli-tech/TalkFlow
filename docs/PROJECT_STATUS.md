# FluentLoop Project Status

## Last Updated

- 2026-09-09
- Branch: `chore/phase2-gate-f-local-mvp-acceptance`
- HEAD: Gate F closeout checkpoint (`docs: complete phase 2 gate f acceptance`)

## Product

FluentLoop (repository: TalkFlow) turns a learner's real experience into spoken English interview
practice. The MVP proves a Recall → Learn → Imitate → Retrieve → Transfer → Interview → Recap loop
with durable, evidence-based progress.

## Current Lifecycle

M0–M7 implementation is complete. The project is now in Phase 2 MVP Activation / Live Integration;
deployment and real-device validation follow the activation gates. No Milestone 8 exists.

## Current Work

- Phase: Phase 2 — MVP Activation
- Gate: F — Local MVP Acceptance
- Status: COMPLETE
- Objective achieved: all 24 Build Spec MVP acceptance criteria and the critical cross-session path
  are covered by automated, live-provider, real-browser, and durable-state evidence.

## Stable Baseline

Phase 1 stable baseline is tag `m7-hardening` at merge commit `cbfed8f`. Gates A–E are merged and
pushed on `main`; Gate F is complete on `chore/phase2-gate-f-local-mvp-acceptance` pending review.

## Implemented

- Onboarding/Profile, confirmed-profile Memory Gate, structured memory/mastery/review/error rules.
- Turn-based Voice Calibration with raw audio, transcript, analysis, assessment, and retry semantics.
- Daily Session shell and deterministic planner; Practice, Quick Review, Journey, My English, XP/Streak.
- Cross-session RetrievalOpportunity and trusted verification path.
- Supabase PostgreSQL/Auth/Storage runtime validation and RLS/user isolation.
- Bailian text, Qwen3-ASR, and Qwen3-TTS runtime adapters behind provider interfaces.

## Not Yet Activated / Not Yet Complete

- Gates A–F are COMPLETE locally.
- Deployment-host setup and real-device coverage remain future activation work.

## Current Blockers

No confirmed Gate F blocker. Known limitations are recorded in `PHASE2_MVP_ACTIVATION.md`.

## Next Steps

1. Review the Gate F checkpoint.
2. Do not merge or push without explicit instruction; do not begin later scope implicitly.

## Verification Snapshot

- Backend: 88 passed after Gate E validation.
- Ruff format/check: passed.
- Frontend ESLint, TypeScript, and production build: passed during M7/Gate B validation.
- Eleven migrations validate locally; the Gate D constraint migration is applied live.
- Bailian live text, TTS→STT, and human voice acceptance: passed in Gate B.
- Gate C real browser microphone/upload/retry validation: complete.
- Gate D real Daily voice/Attempt/Recap/progress/reconnection and bilingual responsive checks:
  complete.
- Gate E live hidden retrieval, real voice evidence, atomic resolution, failure recovery,
  reconnection, isolation, bilingual Recap, 375px routes, and console checks: complete.
- Gate F: all 24 MVP criteria mapped to prior/current evidence; authenticated Day 3 Today,
  Practice, My English, Journey, locale/reload persistence, durable data, ownership, and private
  audio checks passed. Full automated closeout passed again.

## Source of Truth

- Build Spec: authoritative product/architecture specification.
- `DECISIONS.md`: stable architecture decisions.
- `PHASE2_MVP_ACTIVATION.md`: execution gates and acceptance state.
- `PROJECT_STATUS.md`: compact project dashboard.
- `HANDOFF.md`: immediate operational context.
- `ISSUES.md`: debugging and known-issue continuity.
- `CURRENT_MILESTONE.md`: milestone history and current lifecycle notes.
