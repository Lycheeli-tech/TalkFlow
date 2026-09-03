# Phase 2 — MVP Activation

This document tracks activation of the implemented FluentLoop MVP after Phase 1
(M0–M7). The Build Spec remains authoritative; this is an execution/status
document, not a replacement specification. There is no Milestone 8.

## Activation gates

| Gate | Scope | Status |
| --- | --- | --- |
| A | Live Infrastructure | IN PROGRESS — implementation ready; live project configuration/validation required |
| B | Live AI Providers | NOT STARTED |
| C | Real Voice Pipeline | NOT STARTED |
| D | Real Daily Learning Loop | NOT STARTED |
| E | Real Day 1 → Day 2 Cross-Session Aha | NOT STARTED |
| F | Local MVP Acceptance | NOT STARTED |

## Gate A readiness inventory

The repository was inspected on the M7-merged `main` state. Classifications
describe implementation readiness, not successful validation against a real
Supabase project.

| Capability | Classification | Evidence / next action |
| --- | --- | --- |
| Supabase configuration | IMPLEMENTED BUT REQUIRES LIVE VALIDATION | `.env.example`, settings, SQL migrations, and provider adapters exist; fill a real project configuration and verify connectivity. |
| PostgreSQL repositories | IMPLEMENTED BUT REQUIRES LIVE VALIDATION | SQL repositories use SQLAlchemy/asyncpg and are wired by FastAPI dependencies; run against the selected project. |
| Migrations | IMPLEMENTED BUT REQUIRES LIVE VALIDATION | Nine versioned migrations and user provisioning pass local PGlite validation; apply and validate in Supabase. |
| Auth | IMPLEMENTED BUT REQUIRES LIVE VALIDATION | Supabase JWT/JWKS verification and frontend auth client exist; validate with a real user/session. |
| User provisioning | IMPLEMENTED BUT REQUIRES LIVE VALIDATION | Authenticated user state is provisioned through the user repository and migration trigger contract; verify in live Auth/Postgres. |
| RLS | IMPLEMENTED BUT REQUIRES LIVE VALIDATION | User-scoped policies cover users, profiles, sessions, attempts, memory, retrieval opportunities, progress, and private storage paths; exercise with two live users. |
| Profile persistence | IMPLEMENTED BUT REQUIRES LIVE VALIDATION | Confirmed profiles and source documents have SQL models/repositories and ownership constraints; validate create/read isolation. |
| Resume/source-document storage | IMPLEMENTED BUT REQUIRES LIVE VALIDATION | Private Supabase Storage adapter and `resumes` bucket policies exist; validate upload, access, and isolation. |
| Audio storage | IMPLEMENTED BUT REQUIRES LIVE VALIDATION | Private `learner-audio` Supabase Storage adapter and policies exist; validate upload/read and isolation. |
| Session persistence | IMPLEMENTED BUT REQUIRES LIVE VALIDATION | Calibration and Daily Session SQL repositories/migrations exist; validate restart/resume behavior. |
| Attempt persistence | IMPLEMENTED BUT REQUIRES LIVE VALIDATION | Calibration/Daily attempts persist transcripts, processing state, and provenance; validate failure recovery on live Postgres/Storage. |
| Memory persistence | IMPLEMENTED BUT REQUIRES LIVE VALIDATION | PostgreSQL `MemoryRepository` and gated application service are wired for runtime; validate durable writes and ownership. |
| RetrievalOpportunity persistence | IMPLEMENTED BUT REQUIRES LIVE VALIDATION | SQL repository and atomic cross-session unit of work are implemented; validate consume/replay behavior. |
| Progress persistence | IMPLEMENTED BUT REQUIRES LIVE VALIDATION | User progress, streak, rewards, and Daily completion migrations/repositories exist; validate idempotent completion. |

## Gate A minimum activation work

No product-code or architecture change is currently required. Gate A needs:

1. A selected Supabase project with database, Auth, and Storage enabled.
2. Local server-only environment values populated from that project, including
   `DATABASE_URL`, `SUPABASE_URL`, `SUPABASE_JWKS_URL`, JWT configuration,
   `SUPABASE_SERVICE_ROLE_KEY`, and the frontend anon key. Secrets must remain
   outside Git and must not be sent through chat.
3. The nine migrations applied in filename order.
4. A live smoke check covering migration/provisioning, authenticated user
   isolation, private resume/audio Storage, and durable repository writes.

Gate A cannot be marked complete until those live checks are performed. Gate B
must not start before Gate A is complete.

## Current status

- Phase 1 (M0–M7): COMPLETE and merged/tagged on `main`.
- Phase 2 Gate A: implementation inventory complete; waiting for live Supabase
  project configuration and credentials.
- No M8 exists. Later gates require the human review boundaries defined in the
  activation instructions, including real provider, microphone, Daily Session,
  cross-session, and local golden-path use.
