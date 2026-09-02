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

### ADR-012 — Shared Calibration Session

Voice Calibration uses the common Session model with `session_type = CALIBRATION`; this does not authorize Daily Session orchestration.

### ADR-013 — Historical Learner Assessments

Speaking ability is stored in a separate, versionable LearnerAssessment associated with its calibration session, not in the confirmed background Profile.

### ADR-014 — Qualitative Calibration Levels

The MVP uses NEEDS_WORK, DEVELOPING, FUNCTIONAL, and STRONG with qualitative observations, avoiding false numerical precision from three answers.

### ADR-015 — Constrained Hybrid Questions

Question categories and order are deterministic: EXPERIENCE, MOTIVATION, PROJECT. A provider may personalize wording from confirmed profile data but may not alter categories or invent experience.

### ADR-016 — Recoverable Voice Ordering

Persist learner audio and link the attempt before STT; persist the transcript before analysis. Downstream failure must preserve prior artifacts and retry the same attempt idempotently.

### ADR-017 — Bounded Adaptive Daily Planning

The 30-Day Interview Bootcamp has a fixed BUILD → TRANSFER → PERFORM stage backbone, bounded MVP inventories, deterministic target selection, and LLM-generated personalized lesson content. Day 1 is Career Transition; Day 2–30 topics are selected by the planner, not hard-coded as a calendar.

### ADR-018 — Gated Durable Memory Writes

Production memory uses the PostgreSQL repository. Normal durable writes pass through the memory application service and Memory Gate; repositories remain low-level persistence boundaries. In-memory storage is limited to deterministic tests and fixtures.

### ADR-019 — Atomic Cross-Session Resolution

Resolving a persisted Daily Attempt uses a small cross-session unit of work. Verified evidence,
deterministic Expression mastery/review updates, and RetrievalOpportunity consumption commit in one
PostgreSQL transaction; fixtures emulate the same rollback and idempotency semantics in memory.

### ADR-020 — Versioned Deterministic Rewards

XP and streak updates are deterministic application rules behind a versioned `RewardRules` contract.
Reward events may be emitted by later practice flows, but LLM/provider output must not directly decide
XP, streak, or durable progress state.

### ADR-021 — Atomic Daily Completion Progress

A valid Daily Session completion records the session state and applies the versioned passive-learning
reward, streak update, and Journey advancement in one persistence transaction. Replaying a completed
session returns its progress state without awarding XP again.
