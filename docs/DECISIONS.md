# Stable Architectural Decisions

The Build Spec remains authoritative if this summary and `FLUENTLOOP_MVP_BUILD_SPEC_v1.1.md` ever differ.

Future decisions should normally be appended rather than silently rewriting historical decisions. If a later decision supersedes an earlier ADR, it must explicitly reference the superseded ADR.

### ADR-001 — Modular Monolith

Use a modular monolith for the MVP.

### ADR-002 — Application Stack

Use a Next.js frontend and FastAPI backend.

### ADR-003 — Data Platform

Use PostgreSQL through Supabase for database, authentication, and storage.

### ADR-004 — Structured Memory First

Prefer structured memory. Extracted candidates remain unconfirmed until they pass through the Memory Gate.

### ADR-005 — Agent Roles

Coach and Interviewer share learner data but apply different policies and interaction behavior.

### ADR-006 — Deterministic Mastery

Mastery transitions are deterministic and evidence-based. An LLM must not decide durable mastery state.

### ADR-007 — Turn-Based Voice

Use turn-based voice for the MVP, not realtime voice.

### ADR-008 — No Agent Framework

Do not introduce LangChain or LangGraph for the MVP.

### ADR-009 — Curriculum Strategy

Use a fixed curriculum backbone with an adaptive review layer.

### ADR-010 — Provider Abstraction

Keep LLM, STT, and TTS behind provider abstractions. Concrete providers and models may be selected at the relevant milestone.

### ADR-011 — Versioned Evolution

Use versioned database migrations and explicit versions for behavior-changing prompts.
