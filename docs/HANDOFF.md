# Current Agent Handoff

## Updated

- 2026-09-09
- Branch: `chore/phase2-gate-f-local-mvp-acceptance`
- Gate F closeout checkpoint: this document's commit (`docs: complete phase 2 gate f acceptance`)

## Current State

Phase 2 Gate F — Local MVP Acceptance is complete. Gates A–E are merged on `main`. All 24 Build
Spec MVP acceptance criteria and the critical cross-session path have evidence. Do not create M8
or begin deployment, V1.5, V2, or any later scope implicitly.

The local frontend is available at `http://localhost:3000`. The backend is running from the
existing virtual environment at port 8000 with live Supabase/Bailian network access. Secrets remain
only in ignored environment files and were not printed or staged.

## Gate F Acceptance

- The 24 criteria in Build Spec Section 21 were traced to Gates A–E evidence and rechecked as one
  local configured MVP: onboarding/profile/calibration, duration plans and full learning loop,
  durable Attempts/memory/retrieval, deterministic mastery/error rules, projections, interview,
  rewards, failure retention, bilingual state, and restart persistence.
- The critical Day 1 → later-session hidden retrieval path remains verified with real voice evidence
  and a deterministic atomic memory/mastery/review update.
- No product-code, schema, prompt, or architectural change was required for Gate F.

## Verification Evidence

- Backend: 88 tests passed; Ruff format/check passed.
- Frontend: TypeScript, ESLint, and production build passed.
- Migrations: all 11 validate in order locally; Gate D migration applied live.
- Authenticated Day 3 Today created/resumed a persisted Build plan; Practice exposed Quick Review
  state and a working Mock Interview prompt; My English projected Expressions/Patterns/Stories;
  Journey showed the persisted Day 3 position and the complete 30-day phase map.
- English → 简体中文 switching and a full reload preserved route, locale, and Day 3 state.
- User-scoped read-only checks passed for confirmed profile, calibration assessment, two or more
  completed Daily Sessions, analyzed voice Attempts, Expressions, retrieval evidence/opportunities,
  Memory Gate, ownership consistency, two-connection persistence, and non-empty private audio.

## Known Limitations

- The pre-Gate-E live Day 1 Expression required a one-time due backfill from its completed Session.
- Exact phrase verification intentionally treats ASR lexical substitutions as failure.
- The frontend stores a Supabase access token in `sessionStorage` without refresh-token lifecycle;
  expiration returns cleanly to login but requires the user to sign in again.
- One known Starlette/httpx deprecation warning remains in backend tests.
- The live account's 20-minute plan omits IMITATE by deterministic duration design; the shared
  voice path is test-covered. Deployment-host and physical-device coverage remain later work.

## Next Action

Stop after the Gate F checkpoint and report for review. Do not merge, push, or begin later scope
without an explicit user request.

## Do Not Change

- Do not edit the Build Spec, create M8, implement realtime voice, or begin deployment, V1.5, V2,
  or any later scope.
- Do not print or commit `.env`/`.env.local`, database URLs, Supabase keys, Bailian keys, tokens,
  user identifiers, private object paths, or audio content.
- Preserve unrelated user work, especially `frontend/next-env.d.ts`.
