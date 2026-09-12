# FluentLoop Project Status

## Last Updated

- 2026-09-12
- Branch: `codex/course-core-stage-0`
- HEAD: Course Core Stage 0 checkpoint (tag `course-core-stage-0`)

## Product

FluentLoop (repository: TalkFlow) is an AI Course and interview-practice product. Users freely choose
from 30 fixed Courses and 59 fixed Questions; AI uses real profile data, prior Course Answers, and
source-validated Memory to help users express truthful experience in clearer, more natural English.

## Current Lifecycle

The v1.1 Legacy Loop implementation and Phase 2 local acceptance are complete at `8cc986d`. Product
architecture has moved to Build Spec v2.0. Course Core Stage 0 is complete; no Course Core runtime
implementation has started.

## Current Work

- Phase: Course Core
- Stage: 0 — Specification and Safety Boundaries
- Status: COMPLETE
- Objective achieved: the approved v2.0 Build Spec, superseding ADR, Legacy Freeze Manifest, and
  Legacy Code Freeze Rules are established before runtime changes.

## Stable Baseline

The final Legacy code baseline is tag `legacy-loop-final-baseline` at `8cc986d`. Earlier milestone
tags and branches remain intact. Course Core Stage 0 is isolated on `codex/course-core-stage-0`.

## Legacy Implementation Preserved

- Onboarding/Profile, confirmed-profile Memory Gate, structured memory/mastery/review/error rules.
- Turn-based Voice Calibration with raw audio, transcript, analysis, assessment, and retry semantics.
- Daily Session shell and deterministic planner; Practice, Quick Review, Journey, My English, XP/Streak.
- Cross-session RetrievalOpportunity and trusted verification path.
- Supabase PostgreSQL/Auth/Storage runtime validation and RLS/user isolation.
- Bailian text, Qwen3-ASR, and Qwen3-TTS runtime adapters behind provider interfaces.

## Course Core Not Yet Implemented

- Stage 1 Legacy runtime shutdown is not started.
- New App Shell, Course Catalog, Course Answer data, About Me/Memory, AI support, Chinese flow,
  remaining Courses, and Practice V2 are not implemented.
- The existing runtime still behaves as the Legacy product until Stage 1 and Stage 2 are implemented
  and approved.

## Current Blockers

No Stage 0 blocker. Build Spec Section 25 contains product decisions that must be resolved by their
specified implementation deadlines.

## Next Steps

1. Review the Course Core Stage 0 checkpoint.
2. Do not merge, push, or begin Stage 1 without explicit instruction.

## Stage 0 Verification Snapshot

- Build Spec v2.0 is active and v1.1 is explicitly historical.
- ADR-025 records the supersession boundary.
- Legacy Manifest covers files, endpoints, tables, fields, prompts, tests, and migration seams.
- Freeze Rules define prohibited changes, allowed exceptions, and Stage 1 automated enforcement.
- No runtime code or migration changed.

## Legacy Verification Snapshot

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

- `FLUENTLOOP_MVP_BUILD_SPEC_v2.0.md`: authoritative product/architecture specification.
- `FLUENTLOOP_MVP_BUILD_SPEC_v1.1.md`: Legacy Loop historical specification.
- `docs/LEGACY_FREEZE_MANIFEST.md` and `docs/LEGACY_CODE_FREEZE_RULES.md`: frozen boundary.
- `DECISIONS.md`: stable architecture decisions.
- `PHASE2_MVP_ACTIVATION.md`: execution gates and acceptance state.
- `PROJECT_STATUS.md`: compact project dashboard.
- `HANDOFF.md`: immediate operational context.
- `ISSUES.md`: debugging and known-issue continuity.
- `CURRENT_MILESTONE.md`: milestone history and current lifecycle notes.
