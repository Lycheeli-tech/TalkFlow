# Phase 2 — MVP Activation

This document tracks activation of the implemented FluentLoop MVP after Phase 1
(M0–M7). The Build Spec remains authoritative; this is an execution/status
document, not a replacement specification. There is no Milestone 8.

## Activation gates

| Gate | Scope | Status |
| --- | --- | --- |
| A | Live Infrastructure | COMPLETE — live Supabase project configured and validated |
| B | Live AI Providers | NOT STARTED |
| C | Real Voice Pipeline | NOT STARTED |
| D | Real Daily Learning Loop | NOT STARTED |
| E | Real Day 1 → Day 2 Cross-Session Aha | NOT STARTED |
| F | Local MVP Acceptance | NOT STARTED |

## Gate A completion inventory

The repository and live `TalkFlow` Supabase project were validated from the
M7-merged `main` state. Secrets remain in ignored local environment files.

| Capability | Classification | Evidence / next action |
| --- | --- | --- |
| Supabase configuration | VALIDATED LIVE | Browser publishable key, protected server Secret Key, and asymmetric JWKS validation are configured. |
| PostgreSQL repositories | VALIDATED LIVE | SQLAlchemy/asyncpg connected through the regional Supabase Session Pooler using the application `DATABASE_URL`. |
| Migrations | VALIDATED LIVE | Ten versioned migrations are applied; local PGlite migration/provisioning validation also passed. |
| Auth and provisioning | VALIDATED LIVE | Temporary confirmed users signed in and the Auth trigger created matching public user rows. |
| RLS | VALIDATED LIVE | All eleven user-data tables have RLS/policies; two-user probes confirmed cross-user read/write isolation. |
| Profile persistence | VALIDATED LIVE | Preferences, source document, and confirmed profile survived a new database engine/session. |
| Resume storage | VALIDATED LIVE | Private `resumes` owner access passed and cross-user path access was rejected. |
| Audio storage | VALIDATED LIVE | Private `learner-audio` owner access passed and cross-user path access was rejected. |
| Session and Attempt persistence | VALIDATED LIVE | Daily Session and transcript-bearing analyzed Attempt survived reconnection. |
| Memory persistence | VALIDATED LIVE | An Expression written through `MemoryApplicationService` and `SQLMemoryRepository` survived reconnection. |
| RetrievalOpportunity persistence | VALIDATED LIVE | A user/session/expression-owned opportunity written through its SQL repository survived reconnection. |
| Progress persistence | VALIDATED LIVE | Preferences, XP, streak, and completion date written through `SQLUserRepository` survived reconnection. |

## Gate A configuration contract

- Root `.env` holds server/database configuration and remains ignored.
- `frontend/.env.local` holds the browser-safe URL and publishable key and remains ignored.
- The publishable key maps to the existing `NEXT_PUBLIC_SUPABASE_ANON_KEY` client contract.
- The server Secret Key maps to `SUPABASE_SERVICE_ROLE_KEY` and is used only by protected backend code.
- `SUPABASE_JWT_SECRET` remains empty because Auth uses the project JWKS endpoint and
  `authenticated` audience.
- The database uses the regional Session Pooler because the direct database hostname was not
  resolvable from the validation machine.

## Current status

- Phase 1 (M0–M7): COMPLETE and merged/tagged on `main`.
- Phase 2 Gate A: COMPLETE under the DEFAULT PASS protocol.
- Live validation passed for database connectivity, ten migrations, Auth/user provisioning,
  all-table RLS, private Resume/Audio Storage, durable repositories, reconnection recovery, and
  tracked-file secret leakage.
- A missing-RLS gap on five durable learning-memory tables was fixed by
  `202609050010_harden_memory_rls.sql`; all eleven user-data tables now have RLS and policies.
- Remaining Gate A limitations: deployment-host environment configuration has not been performed;
  live checks used temporary synthetic users and fixtures; provider and real voice behavior belong
  to Gates B and C.
- No M8 exists. Later gates require the human review boundaries defined in the
  activation instructions, including real provider, microphone, Daily Session,
  cross-session, and local golden-path use.
