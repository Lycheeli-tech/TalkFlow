# FluentLoop Repository Guide

`FLUENTLOOP_MVP_BUILD_SPEC_v2.0.md` is the authoritative product and architecture specification. `FLUENTLOOP_MVP_BUILD_SPEC_v1.1.md` is retained only as the Legacy Loop historical specification. This file is an operating and navigation map for coding agents; do not rely on conversation history as the source of truth.

## Milestone Reading Protocol

Before starting or resuming any milestone:

1. Read `AGENTS.md`.
2. Read `docs/CURRENT_MILESTONE.md`.
3. Read `docs/DECISIONS.md`.
4. Read the sections of `FLUENTLOOP_MVP_BUILD_SPEC_v2.0.md` relevant to the current stage.
5. If the task may affect product behavior, architecture boundaries, data models, memory, mastery, or cross-session behavior, consult the full relevant specification before implementation.

- Implement only the explicitly authorized Course Core stage. Do not infer later-stage or post-MVP scope.
- Preserve `course_catalog_v1`: 30 Courses, 59 Questions, stable order, fixed wording, and fixed answer focus.
- Keep Question selection under user control. Do not add Course completion, unlocking, day progression, phases, mastery, XP, streak, or automatic next-question behavior.
- Treat Today, Daily Planner, Daily Session, Journey, BUILD/TRANSFER/PERFORM, `current_day`, the seven-step loop, Quick Review, XP/streak, Mastery/Aha, Onboarding, and Voice Calibration as frozen Legacy.
- Before changing routing, shared seams, or any Legacy-adjacent file, read `docs/LEGACY_FREEZE_MANIFEST.md` and `docs/LEGACY_CODE_FREEZE_RULES.md` completely.
- New Course Core, About Me, and Practice V2 code must not import or call Legacy UI, Services, Repositories, Session/Attempt, Progress, Reward, Mastery, Retrieval, or the old Memory Gate.
- Keep product contracts deterministic: ownership, RLS, state transitions, audio mutual exclusion, recording navigation guards, Chinese-draft confirmation, answer deletion, audio retention, Memory-source validation, and Legacy write isolation.
- AI product-mechanism decisions are limited to Memory candidate value and CREATE/UPDATE/MERGE/IGNORE. AI-generated hints, expression materials, reference answers, translation, and feedback are content generation, not authority to change product state.
- Do not allow AI to fabricate learner experience, responsibility, numbers, results, or company facts.
- New AI Memory saves automatically only after deterministic source, target, action, and ownership validation. Do not reuse or bypass the old confirmation-gated Memory Gate.
- New Course Answer data must use new models, tables, repositories, services, and APIs; never add Course semantics to Legacy Session or Attempt.
- Use versioned database migrations and versioned prompts.
- Create a Git checkpoint before risky changes, following Sections 18, 22, 23, and 26 of the Build Spec.
- Inspect Git status first and never overwrite unrelated user work.
- Run the relevant tests and checks before declaring a milestone complete.

## Milestone Closeout

Before declaring a milestone complete:

1. Run all milestone-relevant tests and checks.
2. Compare the implementation against the current stage and MVP acceptance criteria in the Build Spec.
3. Record known limitations explicitly.
4. Update `docs/CURRENT_MILESTONE.md` with the current Course Core stage.
5. Update `docs/DECISIONS.md` only if a stable architectural decision was actually made or changed.
6. Confirm that no later Course Core stage, Legacy behavior, or post-MVP scope was accidentally implemented.
7. Report Git branch, HEAD, working-tree status, commits, tests/checks, and remaining limitations.
8. Stop for review before merge, push, or starting the next milestone unless explicitly instructed otherwise.

## Agent Session Protocol

### Start / resume

For a normal new coding session, read in this order:

1. `AGENTS.md`
2. `docs/PROJECT_STATUS.md`
3. `docs/HANDOFF.md`
4. `docs/ISSUES.md` only for active blockers, debugging, or when HANDOFF references an issue
5. the current Course Core stage execution document
6. only the relevant Build Spec sections
7. `docs/DECISIONS.md` when architecture boundaries matter

Do not automatically reread the entire Build Spec or rely on conversation history. Expand context
only when behavior, architecture, schema, memory/mastery, cross-session rules, or ambiguity requires it.

### Working radius

Before implementation, identify the one current task, inspect Git status, identify relevant files,
and preserve unrelated work. Prefer the smallest coherent change; do not perform repository-wide
refactors or redesign stable architecture without explicit need.

### Session handoff

Keep coding sessions short: aim for one coherent checkpoint or roughly 15–25 turns. Before handing
off, reach a safe checkpoint, run relevant checks, update `HANDOFF.md`, update `PROJECT_STATUS.md` only
when project state changed, update `ISSUES.md` when debugging knowledge changed, update the current
Phase document when execution state changed, and update `DECISIONS.md` only for stable decisions.
Record recovery information and commit a coherent checkpoint when appropriate.

### Debugging continuity

For a meaningful bug, record evidence, attempted diagnostics, ruled-out causes, relevant files, and
the next diagnostic step in a stable `ISSUES.md` entry. Do not repeat documented diagnostics without
new evidence.

### Repository-memory ownership

- `FLUENTLOOP_MVP_BUILD_SPEC_v2.0.md`: authoritative product and architecture requirements.
- `FLUENTLOOP_MVP_BUILD_SPEC_v1.1.md`: Legacy Loop historical requirements only.
- `docs/LEGACY_FREEZE_MANIFEST.md`: frozen files, routes, symbols, tables, and transition seams.
- `docs/LEGACY_CODE_FREEZE_RULES.md`: allowed and prohibited Legacy changes.
- `DECISIONS.md`: stable architectural decisions and ADR history.
- `PROJECT_STATUS.md`: compact project dashboard.
- `HANDOFF.md`: small, short-lived operational context for the next agent.
- `ISSUES.md`: debugging continuity and known issue state.
- `CURRENT_MILESTONE.md` and the current Phase document: execution and acceptance state.

Avoid duplicating large content across these files. Keep the system tool-neutral so Codex, Zcode,
Claude Code, and other agents can use it.

### Context efficiency

Prefer compact summaries, paths, commit hashes, issue IDs, exact next actions, and targeted spec
sections. Do not turn project-memory files into changelogs, transcripts, bug diaries, or Build Spec
copies. Never store secrets or credentials.
