# Stable Architectural Decisions

`FLUENTLOOP_MVP_BUILD_SPEC_v2.1.md` is authoritative if this summary and the Build Spec ever differ. `FLUENTLOOP_MVP_BUILD_SPEC_v2.0.md` and `FLUENTLOOP_MVP_BUILD_SPEC_v1.1.md` are retained as history only.

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

### ADR-022 — Learner-Local Reward Date

Streak and completion rewards use the server timestamp converted through the learner's persisted IANA
timezone. Client-provided local dates are never authoritative.

### ADR-023 — Server-Gated Daily Progress

Daily step progression is persisted on the Session. Only the final configured Recap step can transition
an in-progress Daily Session into a reward-eligible completion; the MVP does not fabricate voice evidence.

### ADR-024 — Mainland-China Live AI Provider

Phase 2 live activation uses Alibaba Cloud Model Studio (Bailian), China (Beijing), for text LLM,
speech-to-text, and text-to-speech services. Provider abstractions remain intact and deterministic
domain rules remain outside model control. Runtime OpenAI adapters and credentials are removed;
fake providers remain available for deterministic tests and local fallback.

### ADR-025 — Course Core Supersedes the Legacy Daily Loop

**Status:** Accepted

**Date:** 2026-09-12

**Authority:** `FLUENTLOOP_MVP_BUILD_SPEC_v2.0.md`

#### Context

The completed v1.1 product centers on Today, a 30-day Daily Session, BUILD/TRANSFER/PERFORM phases,
the seven-step learning loop, Voice Calibration, confirmation-gated memory, cross-session mastery,
XP, streak, Quick Review, and Journey. Product review replaced that model with a user-directed
Course product.

#### Decision

- The active product has three equal entries: Courses, Practice, and About Me.
- A versioned static catalog of 30 Courses and 59 Questions is the learning-content backbone.
- Users choose any Course and Question; Course has no unlocking, completion, mastery, or automatic
  progression.
- New Course Answer, Transcript, Feedback, History, About Me, Memory, and Practice V2 modules use
  new domain models, repositories, services, APIs, and frontend state.
- Existing Auth, database connectivity, private file/audio storage, Resume/text parsing, and
  provider-abstracted LLM/STT/TTS remain reusable infrastructure.
- The Legacy Loop remains in the repository for rollback and historical inspection but is not
  mounted as the new product runtime and cannot be imported by new Course Core modules.
- New AI Memory saves automatically after deterministic source, ownership, action, and target
  validation. AI decides only whether information is worth retaining and whether the action is
  CREATE, UPDATE, MERGE, or IGNORE.
- Hints, expression materials, reference answers, Chinese-to-English organization, and feedback are
  AI-generated content, not authority to change product state.
- Course 11 is the first vertical slice but must use the same generic engine as every Course.

#### Supersession

For the active Course Core, this ADR supersedes:

- ADR-004 only where it requires user confirmation before durable Memory; structured provenance
  remains required;
- ADR-005 for Coach/Interviewer as primary product-control roles;
- ADR-006 for active-product Mastery; the deterministic engine remains frozen Legacy behavior;
- ADR-009 fixed curriculum plus adaptive review;
- ADR-012 through ADR-015 Voice Calibration and calibration-question rules;
- ADR-017 bounded Daily planning;
- ADR-018 confirmation-gated Legacy Memory writes;
- ADR-019 atomic cross-session retrieval resolution;
- ADR-020 through ADR-023 rewards, streak, Daily completion, and Day progression.

The superseded ADRs remain historically valid descriptions of the frozen Legacy implementation.

ADR-001, ADR-002, ADR-003, ADR-007, ADR-008, ADR-010, ADR-011, ADR-016, and ADR-024 remain active
where they do not conflict with Build Spec v2.0.

#### Consequences

- The repository must maintain a concrete Legacy Freeze Manifest and Legacy Code Freeze Rules.
- New code must not add Course semantics to Legacy Session or Attempt.
- New routes must not read or write Legacy progress, Reward, Mastery, or Retrieval state.
- Legacy route shutdown and new App Shell activation require architecture and no-old-write tests.
- Any exception to the freeze requires an explicit reason, scoped review, and product approval when
  it changes the Build Spec.

### ADR-026 — Thirty Critical Course Core Acceptance Criteria

**Status:** Accepted

**Date:** 2026-09-12

**Authority:** `FLUENTLOOP_MVP_BUILD_SPEC_v2.1.md`

#### Context

Build Spec v2.0 expressed the overall MVP acceptance gate as 50 detailed checks. The product owner
approved a smaller, explicit set of 30 critical product acceptance criteria so review remains focused
on the product behaviors that cannot be violated. Detailed requirements elsewhere in the Build Spec
remain normative and testable; they do not become additional critical-product criteria by default.

The approved list contained an empty item 14. The existing rule that saving an Answer must not
automatically advance to the follow-up Question or the next Course fills that position. This preserves
an already approved user-control boundary and does not introduce new behavior.

#### Decision

- Build Spec v2.1 Section 20.3 is the authoritative 30-item critical MVP acceptance list.
- Acceptance evidence and release reporting must map directly to those 30 numbered criteria.
- Course questions and answer focus remain static Catalog authority; AI cannot modify either.
- Course Answers remain repeatable and Question-scoped, with no completion or Mastery state and no
  automatic progression.
- Chinese drafts require confirmation; unconfirmed drafts are not retained.
- Memory saves automatically only with verifiable provenance and remains visible and deletable.
- Practice uses only the 59 static Course Questions, produces whole-session Feedback only, and keeps
  no Practice history.
- New paths cannot create Daily Sessions, update Legacy progress, or import old learning records.
- User data isolation, saved-Answer durability, and the generic Course engine remain release gates.

#### Consequences

- Test plans must identify each criterion by its v2.1 Section 20.3 number.
- The earlier 50-item list remains visible only in historical Build Spec v2.0.
- Requirements removed from the critical list are not silently deleted from their detailed product,
  architecture, security, or failure-handling sections.
- Any future change to the 30-item list requires the Build Spec change-control process.
