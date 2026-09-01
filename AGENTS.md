# FluentLoop Repository Guide

`FLUENTLOOP_MVP_BUILD_SPEC_v1.1.md` is the authoritative product and architecture specification. This file is only an operating and navigation map for coding agents. Do not rely on conversation history as the source of truth.

## Milestone Reading Protocol

Before starting or resuming any milestone:

1. Read `AGENTS.md`.
2. Read `docs/CURRENT_MILESTONE.md`.
3. Read `docs/DECISIONS.md`.
4. Read the sections of `FLUENTLOOP_MVP_BUILD_SPEC_v1.1.md` relevant to the current milestone.
5. If the task may affect product behavior, architecture boundaries, data models, memory, mastery, or cross-session behavior, consult the full relevant specification before implementation.

- Do not implement V1.5 or V2 scope.
- Preserve the canonical learning loop defined in the Build Spec: Recall → Learn → Imitate → Retrieve → Transfer → Interview → Recap, including evidence-based mastery across sessions.
- Keep deterministic domain rules deterministic; do not replace them with LLM judgment.
- Do not bypass the Memory Gate. Extracted candidates are not confirmed learner facts until the user confirms them.
- Use versioned database migrations and versioned prompts.
- Create a Git checkpoint before risky changes, following Section 20 of the Build Spec.
- Inspect Git status first and never overwrite unrelated user work.
- Run the relevant tests and checks before declaring a milestone complete.

## Milestone Closeout

Before declaring a milestone complete:

1. Run all milestone-relevant tests and checks.
2. Compare the implementation against the milestone acceptance criteria in the Build Spec.
3. Record known limitations explicitly.
4. Update `docs/CURRENT_MILESTONE.md`.
5. Update `docs/DECISIONS.md` only if a stable architectural decision was actually made or changed.
6. Confirm that no later-milestone or V1.5/V2 scope was accidentally implemented.
7. Report Git branch, HEAD, working-tree status, commits, tests/checks, and remaining limitations.
8. Stop for review before merge, push, or starting the next milestone unless explicitly instructed otherwise.
