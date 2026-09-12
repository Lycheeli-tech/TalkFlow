# FluentLoop Project Status

## Last Updated

- 2026-09-12
- Branch: `codex/course-core-stage-3`
- HEAD: Course Core Stage 3 closeout checkpoint (tag `course-core-stage-3`)

## Product

FluentLoop (repository: TalkFlow) is an AI Course and interview-practice product. Users freely choose
from 30 fixed Courses and 59 fixed Questions; AI uses real profile data, prior Course Answers, and
source-validated Memory to help users express truthful experience in clearer, more natural English.

## Current Lifecycle

The v1.1 Legacy Loop implementation and Phase 2 local acceptance are complete at `8cc986d`. Product
architecture has moved to Build Spec v2.1. Course Core Stages 1–3 are complete: Legacy remains
preserved for rollback but is not mounted by default, and Course 11 now has the isolated English
Answer minimum loop on top of the immutable Course Catalog.

## Current Work

- Phase: Course Core
- Stage: 3 — Course 11 English Answer minimum loop
- Status: COMPLETE
- Objective achieved: Course 11 supports user-selected core/follow-up questions, exact Catalog TTS,
  English recording, original-audio-first storage, final STT, saved transcripts, History, retry, and
  newest-two audio retention through dedicated Course Core data and API boundaries.
- Practice V2, About Me, Chinese Answer, AI support, and Feedback generation remain disabled.
- Real PostgreSQL assertions prove ownership/RLS and zero Legacy progress/table mutation.

## Stable Baseline

The final Legacy code baseline is tag `legacy-loop-final-baseline` at `8cc986d`. Stage 0 is closed at
tag `course-core-stage-0-v2.1`; Stage 1 is merged to `main` and closed at tag
`course-core-stage-1`; Stage 2 is merged to `main` and closed at tag `course-core-stage-2`; Stage 3
is isolated on `codex/course-core-stage-3` and closed at tag `course-core-stage-3`.

## Legacy Implementation Preserved

- Onboarding/Profile, confirmed-profile Memory Gate, structured memory/mastery/review/error rules.
- Turn-based Voice Calibration with raw audio, transcript, analysis, assessment, and retry semantics.
- Daily Session shell and deterministic planner; Practice, Quick Review, Journey, My English, XP/Streak.
- Cross-session RetrievalOpportunity and trusted verification path.
- Supabase PostgreSQL/Auth/Storage runtime validation and RLS/user isolation.
- Bailian text, Qwen3-ASR, and Qwen3-TTS runtime adapters behind provider interfaces.

## Course Core Not Yet Implemented

- About Me/Memory, AI support and Feedback generation, Chinese flow, Answer deletion,
  remaining-Course answering, and Practice V2 are not implemented.

## Current Blockers

No Stage 3 blocker. Failed Answer/Draft audio TTL is three days and is recorded in ADR-028. Remaining
Build Spec Section 25 decisions retain their specified implementation deadlines.

## Next Steps

1. Review the Stage 3 checkpoint and English Answer evidence.
2. Do not begin Stage 4, merge, or push Stage 3 without explicit instruction.

## Stage 3 Verification Snapshot

- Dedicated Course tables, RLS, repository/service/API/client and Course 11 UI are implemented without
  Legacy business imports; authenticated clients cannot write tables directly.
- Backend: 121 passed with 2 opt-in real PostgreSQL tests also passed; Ruff check passed.
- Frontend: TypeScript, ESLint, and production build passed.
- Real TTS → private audio → final STT → saved Answer → History/replay passed. Three-save retention
  kept the latest two audio objects and retained the oldest transcript.
- Desktop and 375px authenticated browser checks passed; device microphone permission was not
  auto-approved, so the physical microphone button path remains a documented manual smoke item.
- Both Stage 3 migrations are applied and registered in the configured test database; Legacy fields,
  tables, schema, and data were unchanged. Disposable browser test data was removed.

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

- `FLUENTLOOP_MVP_BUILD_SPEC_v2.1.md`: authoritative product/architecture specification.
- `FLUENTLOOP_MVP_BUILD_SPEC_v2.0.md`: previous Course Core specification retained as history.
- `FLUENTLOOP_MVP_BUILD_SPEC_v1.1.md`: Legacy Loop historical specification.
- `docs/LEGACY_FREEZE_MANIFEST.md` and `docs/LEGACY_CODE_FREEZE_RULES.md`: frozen boundary.
- `DECISIONS.md`: stable architecture decisions.
- `PHASE2_MVP_ACTIVATION.md`: execution gates and acceptance state.
- `PROJECT_STATUS.md`: compact project dashboard.
- `HANDOFF.md`: immediate operational context.
- `ISSUES.md`: debugging and known-issue continuity.
- `CURRENT_MILESTONE_V1.md`: current Course Core V1 stage, execution, and acceptance state.
- `CURRENT_MILESTONE.md`: historical milestone and lifecycle notes only.
