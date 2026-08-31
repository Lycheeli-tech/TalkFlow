# FluentLoop MVP Build Specification v1.1

## 0. How Codex Should Use This Document

This document is the single source of truth for the FluentLoop MVP. It consolidates product decisions, MVP scope, learning architecture, system architecture, agent/harness behavior, data model, technical guardrails, and maintainability requirements.

Codex should:
1. Read this document completely before coding.
2. Produce an implementation plan and proposed milestone sequence before modifying files.
3. Identify contradictions or missing implementation-critical details instead of silently inventing product behavior.
4. Preserve the architecture boundaries in this document.
5. Build only MVP scope. Do not implement V1.5/V2 features unless explicitly requested.
6. Prefer simple deterministic code over agentic/LLM behavior when rules can solve the problem.
7. Keep the application runnable after each milestone.
8. Add tests around core domain rules before or alongside implementation.
9. Use versioned database migrations. Never solve schema conflicts by destructively resetting persistent user data.
10. Treat this specification as product intent and architectural constraints; implementation details not specified here may be chosen pragmatically.
11. Use Git as the change-safety mechanism described in Section 20; preserve rollback points and do not make risky broad changes without a clean checkpoint.

---

# 1. Product Definition

## 1.1 Product Name
FluentLoop

## 1.2 Product Vision
FluentLoop is an adaptive English-speaking training application initially focused on English interviews for international companies and English-speaking roles.

It is not primarily a chatbot, generic speaking companion, vocabulary app, or static interview question bank.

Its core purpose is to turn language that a learner has seen or understood into language the learner can retrieve and use independently under interview conditions.

Core promise:

**Turn what you know into what you can say.**

## 1.3 Primary User Problem
Target users may:
- know what they want to say in Chinese but translate word-for-word into English;
- understand English passively but fail to retrieve natural spoken expressions;
- speak with grammar errors when under time pressure;
- hesitate, freeze, or stop because they are afraid of mistakes;
- understand only part of a long or fast interview question and become uncertain;
- lack reusable interview stories and structured ideas;
- over-prepare model answers but fail to transfer learned language to new questions;
- have pronunciation/accent concerns, although deep accent training is not an MVP goal.

## 1.4 MVP Target
The first product program is a **30-Day English Interview Bootcamp**.

MVP training priority:
- Interview performance: approximately 80-90%.
- Broader English idea expression: approximately 10-20%.

Long-term FluentLoop may expand into general spoken English, workplace English, IELTS speaking, debate/idea training, pronunciation, and other programs. The MVP architecture must not prevent those extensions.

## 1.5 Core Product Hypothesis
FluentLoop succeeds if it can:

1. Understand a learner's real professional background.
2. Generate relevant learning material.
3. teach a small number of useful expressions and answer structures;
4. force active retrieval rather than passive rereading;
5. test those expressions later in a different context without revealing the target;
6. remember success/failure across sessions;
7. adapt future review opportunities;
8. make progress visible.

The key MVP "aha" moment is:

**Yesterday I could not say this. Today I used it by myself in a different interview question.**

---

# 2. MVP Scope

## 2.1 MVP Must Have
- Account/basic user state
- Interface language: English and Simplified Chinese
- Support language: English or Simplified Chinese
- Target role and interview goal
- Resume PDF upload
- Paste-text background import fallback
- Structured profile extraction
- User review/edit/confirmation before persistent profile write
- Voice calibration with 3 personalized questions
- Initial learner profile
- Fixed 30-day curriculum backbone with adaptive personal review
- 10/20/30/60-minute session choices
- Daily learning session
- Turn-based voice recording
- Speech-to-text
- Basic text-to-speech for interviewer questions
- Coach role
- Interviewer role
- Structured Me Database
- Expression tracking
- Error-pattern tracking
- Interview story bank
- Cross-session review
- Mastery state machine
- Mock Interview
- Quick Review
- Streak
- XP
- Mastery moments
- 30-day journey map
- Basic logging, error recovery, tests, migrations

## 2.2 Explicitly NOT MVP

Do not implement these in the initial build:

- Realtime speech-to-speech
- Advanced accent scoring
- phoneme scoring
- detailed stress/rhythm/linking scoring
- Skill Tree
- complex achievement/badge system
- coins/shop/leaderboard
- Small Talk mode
- Idea Gym
- Debate
- Listening Lab as an independent module
- Pronunciation Agent
- separate Review Agent
- multiple country accents/interviewer nationalities
- JD/company-specific interview sprint
- semantic/vector memory unless later required
- fully AI-generated curriculum
- complex adaptive pressure model
- complex psychological/emotional learner model
- background-job infrastructure unless required for basic reliability
- microservices/Kubernetes
- LangChain/LangGraph unless complexity later justifies it

## 2.3 V1.5 Candidates
- Skill Tree
- Small Talk
- Listening Lab
- Idea Gym
- Pronunciation Lite
- richer achievements
- ability radar
- Mission Talk
- richer pressure levels
- more coaching personalities
- more dynamic curriculum

## 2.4 V2 Candidates
- realtime voice
- accent analysis
- interviewer accent/nationality variants
- JD/resume targeting
- company interview sprint
- debate/news/English-thinking programs
- advanced learner model
- semantic memory
- full evaluation/observability harness

---

# 3. Product Information Architecture

Primary navigation:

1. **Today**
2. **Practice**
3. **My English**
4. **Journey**

## 3.1 Today
Primary daily experience. User should need minimal decision-making.

Shows:
- streak
- current day and phase
- today's focus
- Continue Training
- session length selection: 10/20/30/60 minutes
- simple preview of session structure

## 3.2 Practice
MVP contains only:
- Mock Interview
- Quick Review

## 3.3 My English
MVP contains:
- Expressions
- Patterns
- Stories

This is the user-visible projection of the Me Database. It is not the raw database.

## 3.4 Journey
MVP contains:
- 30-day map
- phase display: BUILD / TRANSFER / PERFORM

Skill Tree and complex analytics are deferred.

---

# 4. Onboarding Golden Path

## 4.1 Welcome
Communicate the product promise.

## 4.2 Goal Setup
Collect:
- target role
- primary goal: English Interview
- default session duration
- interface language
- support language

Default coaching style may be Supportive and changed later in Settings.

## 4.3 Build My Profile
User can:
- upload resume PDF; or
- paste background text.

## 4.4 Profile Extraction
Pipeline:

PDF -> parser -> raw text -> profile extractor -> candidate profile

The model must produce structured output, not free-form prose.

Candidate fields:
- work experience
- projects
- skills
- industries
- education
- career transition
- technical keywords
- potential story candidates

## 4.5 Profile Review
Display concise editable cards.

User can:
- confirm
- edit
- delete
- add

**Memory Gate:** candidate profile becomes persistent confirmed profile only after user confirmation.

## 4.6 Voice Calibration
Three personalized voice questions:
1. Familiar experience question
2. Motivation/career-transition question
3. Project/story question

No mid-answer correction.

Pipeline:
question -> TTS -> user recording -> audio saved -> STT -> transcript -> analysis

## 4.7 Initial Learner Profile
MVP public dimensions:
- Fluency
- Naturalness
- Grammar
- Retrieval
- Structure

Listening may be recorded as observations but should not present false precision from only three questions.

Output:
- strengths
- primary focus
- secondary focus
- observed patterns
- message that the profile will evolve with training

## 4.8 30-Day Journey
Explain:
- Days 1-10 BUILD
- Days 11-20 TRANSFER
- Days 21-30 PERFORM

Then start Day 1.

---

# 5. Learning Architecture

## 5.1 Core Learning Loop
The canonical full-session loop is:

**Recall -> Learn -> Imitate -> Retrieve -> Transfer -> Interview -> Recap**

This loop is the core of FluentLoop and must remain explicit in the product architecture.

### Recall
Retrieve previously learned material.

### Learn
Present personalized material based on user's background and current curriculum unit.

### Imitate
Listen/repeat useful spoken chunks or answer segments.

### Retrieve
Hide the full model answer and require independent production with phase-appropriate scaffolding.

### Transfer
Change the question/context and test whether learned language transfers.

### Interview
Interviewer role asks realistic follow-ups without revealing target expressions.

### Recap
Prioritized feedback, memory update, mastery/review changes, reward.

## 5.2 Session Duration
60-minute mode is the full experience.

10/20/30-minute sessions should reuse the same curriculum and learner state, not create separate progress.

Example 10-minute session:
Recall -> Retrieve -> Mini Interview -> Recap

Completing a valid quick daily session should preserve streak.

## 5.3 Three Phases

### BUILD (Days 1-10)
Goal: build language and story inventory.

High scaffolding:
- Chinese support allowed
- model answers allowed
- chunks
- keywords
- retries
- first-word hints where appropriate

### TRANSFER (Days 11-20)
Goal: use learned language in new contexts.

Medium scaffolding:
- keywords
- limited retries
- indirect hints

Avoid:
- full answer
- directly revealing target expression during retrieval/transfer tests

### PERFORM (Days 21-30)
Goal: perform under realistic interview conditions.

Low scaffolding:
- no answer hints
- no mid-answer correction
- natural clarification is allowed
- random/natural follow-ups
- fewer new inputs, more retrieval and performance

## 5.4 Curriculum Model
Use:

**Fixed Backbone + Adaptive Layer**

Do not let an LLM freely reinvent the curriculum every day.

Fixed curriculum defines:
- phase
- topic
- core skill
- question category
- story category
- language function

Adaptive layer inserts:
- due expressions
- active error patterns
- relevant personal stories
- role-specific questions

## 5.5 Curriculum / Inventory Separation
Inventory is the content warehouse:
- Questions
- Expressions
- Strategies

Curriculum decides when/why categories are trained.

Session builder selects appropriate inventory items for the user.

## 5.6 Content Inventory Concept
Long-term learning content spans:
- Question Inventory
- Story Inventory
- Language Inventory
- Listening Inventory
- Strategy Inventory
- Delivery Inventory

MVP implementation prioritizes:
- Questions
- Expressions/language chunks
- Story categories
- Strategies

Listening/Delivery inventories can be expanded later.

---

# 6. Correction and Coaching Policy

## 6.1 Correction Budget
Do not overwhelm the user.

A single response may generate many internal observations, but visible feedback should normally be limited to approximately:
- 1 Fix Now
- up to 2 Improve items
- 1 Win

Priority:
1. communication breakdown
2. unnatural/Chinese-literal expression
3. repeated grammar problem
4. minor grammar

Other observations may be stored without immediately surfacing them.

## 6.2 Do Not Rescue Too Early
Retrieval effort is a product objective.

The system must allow hesitation and silence appropriate to the phase before offering help.

Do not immediately reveal a target expression when the user hesitates.

## 6.3 Coaching Style vs Scaffolding
These are independent dimensions.

Coaching styles:
- Supportive
- Professional
- Strict

Scaffolding determines **how much help** is allowed.
Personality determines **how the allowed help is expressed**.

Do not create separate duplicated agents for every combination.

---

# 7. Agent / Harness Architecture

## 7.1 User-Visible Roles
MVP has only two primary conversational roles.

### Coach
Responsibilities:
- teach
- explain
- provide examples
- provide phase-allowed hints
- correct
- recap
- encourage
- help construct answers

### Interviewer
Responsibilities:
- ask interview questions
- follow up
- test recall
- test transfer
- run mock interviews

Interviewer policy:
- do not reveal target expression
- do not provide answer hints during a test
- do not correct mid-answer
- allow reasonable silence
- ask natural follow-ups
- use known user background without inventing experience

## 7.2 Non-Personified Harness Components
- Session Orchestrator
- Context Builder
- Analyzer
- Memory Extractor / Memory proposal logic
- Verifier
- Mastery Engine
- Memory Gate
- Reward Engine

These are components, not chat personalities.

## 7.3 Runtime Flow

User Voice
-> save raw audio
-> Speech-to-Text
-> save transcript/attempt
-> Answer Analyzer
-> Structured Observation
-> Verifier
-> Mastery Engine
-> Memory Gate
-> Database Update
-> Reward Engine
-> Next Step

Important principle:

**Agent proposes/observes; deterministic harness decides durable state.**

## 7.4 LLM vs Deterministic Code

Use deterministic code for:
- streak
- XP
- current day
- session duration
- spaced review date
- mastery state transitions
- hint-used flags
- cross-session checks
- role switching
- scaffolding level
- phase
- database retrieval rules

Use LLM for:
- resume/profile extraction
- personalized learning material
- answer relevance
- naturalness analysis
- Chinglish/literal-translation detection
- explanation of errors
- natural follow-up generation
- story candidate extraction
- creating natural retrieval opportunities

## 7.5 Prompt Layering
Prompts should be separated into:
1. Global Product Policy
2. Role Policy
3. Session Context
4. Turn Context

Do not create one unmaintainable mega-prompt.

Prompt files must be versioned.

## 7.6 Context Builder
Agents must not independently query arbitrary user history.

Context Builder should assemble a bounded context from:
- target role
- current phase
- current topic
- coaching style
- relevant story: usually 1
- due expressions: usually 3-5
- active patterns: usually 1-2
- recent relevant attempts: usually 1-3

Do not inject full history.

Context Store and Context Window are separate concepts.

## 7.7 Memory Write Policy
Coach/Interviewer/Analyzer must not directly mutate durable mastery/memory truth.

Flow:
Memory Proposal -> Memory Gate -> Validation -> Memory Writer

Example:
First occurrence of a grammar issue -> CANDIDATE, not automatically ACTIVE.

---

# 8. Me Database / Data Model

The MVP should use approximately 8 user-data objects plus product-content objects.

## 8.1 User
Purpose: identity, preferences, current product state.

Fields conceptually include:
- id
- created_at
- interface_language
- support_language
- default_session_length
- coaching_style
- current_day
- current_phase
- xp/current_streak as cached display values if useful

Do not turn User into a catch-all table.

## 8.2 Profile
Confirmed user background:
- target_role
- primary_goal
- education
- work_experience (structured JSON acceptable in MVP)
- skills
- industries
- career_transition
- technical_keywords
- confirmed_at
- updated_at

## 8.3 SourceDocument
Preserve provenance:
- id
- user_id
- type
- filename
- raw_text
- parse_status
- created_at

Resume and later source material should remain traceable.

## 8.4 Session
Represents one learning/practice session:
- id
- user_id
- day
- phase
- session_type
- duration_plan
- duration_actual
- topic
- role
- scaffolding_level
- pressure_level
- status
- started_at
- completed_at

Session types may include DAILY and MOCK_INTERVIEW.

## 8.5 Attempt
One spoken answer/interaction:
- id
- session_id
- user_id
- question
- question_type
- audio reference
- transcript
- response_duration
- hint_level
- preparation_time
- feedback/analysis reference
- created_at

Attempt history is important for longitudinal comparison.

## 8.6 Expression
Represents the user's learning state for a useful spoken expression/chunk:
- id
- user_id
- text
- meaning
- source_type/source_id
- status
- successful_recall
- failed_recall
- transfer_success
- next_review_at
- timestamps

## 8.7 ExpressionAttempt
Evidence linking an expression to a real attempt:
- id
- expression_id
- attempt_id
- context
- hint_used
- usage_correct
- retrieval_type
- result
- created_at

Retrieval types conceptually:
- LEARNING
- RECALL
- TRANSFER
- PRESSURE (future/optional in MVP)

## 8.8 ErrorPattern
Tracks recurring patterns rather than permanently labeling isolated mistakes:
- id
- user_id
- pattern_type
- original_example
- preferred_expression/correction
- occurrence_count
- successful_correction_count
- status
- first_seen
- last_seen

States:
CANDIDATE -> ACTIVE -> IMPROVING -> RESOLVED

## 8.9 Story
Interview story bank:
- id
- user_id
- title
- background
- goal
- role
- action
- challenge
- result
- reflection
- tags
- readiness
- source_document_id
- timestamps

A story may answer multiple question categories.

## 8.10 Product Content
Separate from user data.

### CurriculumUnit
Conceptual fields:
- program
- day/unit
- phase
- topic
- skill
- question categories
- language functions

### InventoryItem
Conceptual types:
- QUESTION
- EXPRESSION
- STRATEGY

Fields may include:
- content
- category
- difficulty
- tags

MVP may seed these from JSON/SQL rather than building a CMS.

---

# 9. Mastery and Review

## 9.1 Expression State Machine

NEW -> LEARNING -> RECALLED -> TRANSFERRED -> MASTERED

Definitions:

### NEW
Identified/selected but not meaningfully learned.

### LEARNING
Presented and practiced with support.

### RECALLED
Produced without the full answer visible and without disqualifying direct hint.

### TRANSFERRED
Correctly used in a different question/context.

### MASTERED
Demonstrated reliably across multiple sessions.

A single successful use must never produce MASTERED.

MVP may use a deterministic rule such as:
- successful recall >= 3
- transfer success >= 2
- successes across >= 3 sessions

Exact thresholds may be tuned, but mastery must remain evidence-based and deterministic.

## 9.2 Review Scheduler
MVP can use simple spaced intervals:
- next day
- 3 days
- 7 days
- 14 days

Failure shortens interval.
Success lengthens interval.

The most important behavior is not displaying a traditional flashcard queue; it is inserting due expressions naturally into later speaking opportunities.

## 9.3 Evidence
Durable states should be traceable to evidence.

Examples:
- Expression mastery -> ExpressionAttempts
- Error pattern -> Attempts
- Story -> resume/source document + user confirmation

This supports verification, debugging, and future explainability.

---

# 10. Daily Session Functional Requirements

## 10.1 Session Creation Inputs
- current day
- phase
- session duration
- curriculum unit
- due expressions
- active patterns
- relevant story
- target role

## 10.2 Session Plan
Full session:
Recall -> Learn -> Imitate -> Retrieve -> Transfer -> Interview -> Recap

Quick sessions should select a useful subset without breaking shared progress.

## 10.3 Day 1 Example
Topic: Career Transition.

Teach personalized answer ideas and a small set of chunks such as:
- where the industry is heading
- I'm naturally curious about...
- highly transferable
- a natural next step

Then:
- imitate
- retrieve without full answer
- transfer to a different question
- interviewer creates an unannounced opportunity to use a target expression

Do not immediately mark the expression mastered.

## 10.4 Day 2 Cross-Session Aha
A due expression from Day 1 should be inserted into a new natural interview question without revealing it.

If the user independently uses it correctly:
- create evidence
- update state (e.g. RECALLED -> TRANSFERRED)
- surface a meaningful mastery/progress moment at recap rather than interrupting the interview

This cross-session behavior is a critical MVP acceptance test.

---

# 11. Voice Requirements

## 11.1 MVP Voice
Turn-based voice only.

Flow:
Interviewer/Coach text -> TTS -> user listens -> browser recording -> audio stored -> STT -> transcript -> analysis

## 11.2 Raw Data Preservation
Save raw audio before analysis where practical.

If STT/analyzer fails, the attempt should be recoverable/retryable without losing the user's recording.

## 11.3 MVP Non-goals
No advanced pronunciation/accent scoring.
No realtime interruption/barge-in.
No streaming conversational infrastructure unless later explicitly added.

---

# 12. Rewards and Progress

MVP rewards:
- Streak
- XP
- Mastery Moment
- 30-Day Map

XP should reward retrieval effort more than passive exposure.

Illustrative weighting:
- Passive Learn +1
- Imitation +2
- Successful Recall +5
- Transfer +10
- Mastery +20

Exact values may be tuned.

Avoid excessive reward popups.

Use:
- light micro-feedback during training
- stronger mastery moment only for meaningful progress
- session-end recap/reward

---

# 13. Internationalization

MVP interface languages:
- English
- Simplified Chinese

Learning language:
- English only in MVP

Support language:
- English or Simplified Chinese

These are separate concepts:
- Interface Language controls navigation/system UI.
- Learning Language is the language being learned.
- Support Language controls explanations/translations/scaffolding.

UI strings must use i18n keys and must not be hard-coded throughout components.

Changing interface language must not alter learner memory or curriculum progress.

---

# 14. Technical Architecture

## 14.1 Architecture Style
Use a modular monolith for MVP.

Do not use microservices.

Suggested stack:
- Frontend: Next.js + React + TypeScript
- Backend: Python + FastAPI
- Database: PostgreSQL
- Managed backend option: Supabase for Postgres/Auth/Storage
- Storage: resume PDFs and audio
- AI: provider-abstracted LLM/STT/TTS services

Semantic/vector retrieval is not required for MVP.

## 14.2 Why Structured Memory First
Most MVP retrieval can use SQL:
- due expressions
- relevant stories/tags
- active patterns
- recent attempts

Future semantic memory may be added behind a retrieval abstraction, potentially using pgvector, without replacing the structured Me Database.

## 14.3 Backend Layers

API
-> Application/Services
-> Domain
-> Repositories
-> Database

AI is an external capability used through service interfaces.

Suggested logical modules:

### API
HTTP endpoints only; no core business logic.

### Services
Workflow orchestration:
- ProfileService
- SessionService
- AttemptService
- MemoryService
- CurriculumService
- AnalysisService

### Domain
Deterministic product rules:
- MasteryEngine
- ReviewScheduler
- RewardEngine
- ScaffoldingPolicy
- SessionOrchestrator

### AI
- LLMService
- SpeechToTextService
- TextToSpeechService
- ProfileExtractor
- AnswerAnalyzer
- Coach
- Interviewer
- ContextBuilder

### Memory
- MemoryGate
- MemoryWriter

### Repositories
Database access only.

## 14.4 AI Provider Abstraction
Business logic must not directly depend on a specific provider SDK.

Conceptually:

Business -> LLMService -> Provider Adapter -> Model

Similarly:
SpeechToTextService -> STT Provider
TextToSpeechService -> TTS Provider

MVP may use one provider/model initially, but architecture must permit replacement.

## 14.5 Program Abstraction
Do not hard-code product logic to "Day 17" throughout code.

Conceptually:

Program -> Phase -> CurriculumUnit -> SessionPlan

MVP program:
30-Day Interview Bootcamp

Future programs should be addable without replacing the core Session/Attempt/Memory runtime.

---

# 15. Maintainability and Extensibility Requirements

## 15.1 Stable Core
Treat this as the stable learning runtime:

User -> Curriculum -> Session -> Attempt -> Analysis -> Memory -> Mastery -> Next Session

Future features should extend around this core rather than repeatedly rewriting it.

## 15.2 Domain Boundaries
Conceptual domains:
1. Identity
2. Learning
3. Interaction
4. Intelligence
5. Memory
6. Progression

Avoid circular dependencies and cross-domain database manipulation.

## 15.3 Domain Must Not Depend on LLM
Core deterministic rules must not ask an LLM to decide state.

For example, MasteryEngine receives verified observations and counts; it does not ask a model whether something "feels mastered."

## 15.4 Composition Over Agent Duplication
Agent behavior should conceptually compose:
Role + Policy + Context + Tools + Personality

Future accent/difficulty/pressure should be independent configuration dimensions where possible.

Do not create separate duplicated agent implementations for every combination.

## 15.5 Practice Mode Extension Point
MVP modes:
- MockInterviewMode
- QuickReviewMode

Future modes such as SmallTalkMode or PronunciationMode should be addable primarily by addition rather than rewriting Daily Learning Loop.

A heavy plugin framework is not required now; preserve clean boundaries.

## 15.6 Curriculum and Session Separation
Curriculum = what should be learned.
Session = how today's available time and personal memory turn curriculum into actual exercises.

Changing session duration must not mutate curriculum definition.

## 15.7 Memory Retrieval Abstraction
Context Builder should call a memory retrieval interface rather than know whether retrieval uses SQL, semantic vectors, or both.

Future:
Memory Retrieval -> Structured Retriever + Semantic Retriever

## 15.8 Centralized Memory Writes
New roles/modes may propose memory updates but should not bypass Memory Gate.

## 15.9 Feature Flags
Provide a lightweight feature configuration mechanism.

Potential future flags:
- skill_tree
- small_talk
- semantic_memory
- realtime_voice

No enterprise feature-flag platform is required.

## 15.10 Database Migrations
All schema changes must use versioned migrations.

Do not destructively reset persistent data to resolve ordinary schema evolution.

## 15.11 API Versioning
Use a versioned API namespace such as `/api/v1/...`.

## 15.12 Prompt Versioning
Prompts live outside business logic and carry versions:
- global_policy
- coach_v1
- interviewer_v1
- profile_extractor_v1
- answer_analyzer_v1

Logs/traces should record relevant prompt/model versions.

## 15.13 Failure Isolation
Auxiliary failure must not destroy core learning data.

Examples:
- TTS failure -> show text fallback
- analyzer failure -> preserve attempt and allow re-analysis
- reward failure -> do not lose attempt
- future pronunciation failure -> session continues

## 15.14 Background Work
Future expensive operations may move to background jobs.

Do not introduce Redis/Celery/queue infrastructure until actually needed, but keep service boundaries compatible with later asynchronous execution.

## 15.15 Architecture Fitness Tests
Future changes should prefer extension by addition.

Expected examples:

### Add British Interviewer
Prefer adding voice/accent configuration; do not modify Mastery/Memory/Curriculum core.

### Add Small Talk
Prefer new mode/policy/UI entry while reusing Session, Attempt, Memory, Analyzer.

### Add Semantic Memory
Prefer new retriever/embedding layer; Coach/Interviewer should not need redesign.

### Change LLM Provider
Prefer provider adapter change; business/domain code should remain unchanged.

### Add IELTS Program
Expected additions: Program, Curriculum, Inventory, Evaluation policy.
Expected reuse: User, Session, Attempt, Voice, Memory, Progression.

Guiding principle:

**Extend by addition, not rewrite.**

---

# 16. Suggested Repository Structure

```text
fluentloop/
|
|-- frontend/
|   |-- app/
|   |   |-- (onboarding)/
|   |   |-- today/
|   |   |-- practice/
|   |   |-- my-english/
|   |   |-- journey/
|   |   `-- settings/
|   |-- components/
|   |   |-- ui/
|   |   |-- session/
|   |   |-- voice/
|   |   `-- progress/
|   |-- lib/
|   |-- locales/
|   |   |-- en.json
|   |   `-- zh-CN.json
|   |-- types/
|   `-- public/
|
|-- backend/
|   |-- app/
|   |   |-- main.py
|   |   |-- api/
|   |   |-- services/
|   |   |-- domain/
|   |   |-- ai/
|   |   |   |-- analyzers/
|   |   |   |-- agents/
|   |   |   `-- context/
|   |   |-- memory/
|   |   |-- repositories/
|   |   |-- models/
|   |   |-- prompts/
|   |   |-- curriculum/
|   |   `-- core/
|   `-- tests/
|       |-- domain/
|       |-- services/
|       |-- ai/
|       `-- regression/
|
|-- supabase/
|   |-- migrations/
|   `-- seed.sql
|
|-- docs/
|   |-- PRD.md
|   |-- architecture.md
|   |-- data-model.md
|   `-- api-contract.md
|
|-- .env.example
`-- README.md
```

This is guidance, not a requirement to create empty files/folders that have no current purpose. Keep the implementation lean.

---

# 17. Testing and Evaluation Requirements

## 17.1 Unit-Test Priority
Protect core deterministic product behavior:
- Mastery Engine
- Review Scheduler
- Reward Engine
- Scaffolding Policy
- Memory Gate
- Session Orchestrator

Minimum invariants:
- one recall cannot produce MASTERED
- BUILD allows defined hints
- PERFORM forbids answer hints
- first isolated error becomes CANDIDATE, not ACTIVE
- direct hint disqualifies an attempt from qualifying as independent transfer
- quick session completion can preserve streak
- confirmed profile is required before durable profile memory is treated as user truth

## 17.2 AI Regression Cases
Maintain a small set of fixed behavioral cases.

Examples:

### Case: Correction Budget
User produces multiple errors.
Expected:
- feedback prioritizes major issues
- visible correction budget is respected
- no ridicule
- include a useful win when justified

### Case: Hidden Target Retrieval
Interviewer is asked to create an opportunity for `highly transferable`.
Expected:
- target phrase is never revealed
- no direct hint
- follow-up remains natural

### Case: No Fabricated Background
If resume/profile lacks an experience:
- Coach/Interviewer must not state that the user did it as fact.

MVP may run these manually or semi-automatically; preserve them as regression fixtures.

---

# 18. Logging / Observability

MVP does not require a complex observability stack.

Record enough to debug:
- request_id
- user_id
- session_id
- step
- model/provider
- prompt_version
- latency
- token usage where available
- status
- error

Do not log secrets.

---

# 19. Security / Data Handling Basics

- Secrets must live in environment variables, never source control.
- Validate file type/size for uploads.
- Scope all user-data queries by authenticated user.
- Do not expose another user's audio, resume, profile, attempts, or memory.
- Store only data needed for product behavior.
- Preserve the ability to delete user data later, even if a polished deletion UI is not MVP.
- Avoid placing full sensitive profile/history in logs.

---


# 20. Version Control & Change Safety

## 20.1 Canonical Repository
The canonical GitHub repository for this project is:

`https://github.com/Lycheeli-tech/TalkFlow.git`

Codex should treat the repository history as an important safety mechanism, not merely as a final publishing destination.

## 20.2 Git Is Required for All Development
All meaningful implementation work must be performed under Git version control.

Codex must:
- inspect repository status before making changes;
- avoid overwriting unrelated user changes;
- keep commits small enough to understand and revert;
- commit only coherent, working changes;
- never commit secrets, `.env` values, API keys, access tokens, generated credentials, or private user data;
- preserve migration history and prompt versions in Git;
- keep the repository in a runnable/testable state at milestone boundaries.

## 20.3 Branch Strategy
Use a lightweight branch strategy suitable for a solo Vibe Coding project.

Recommended:
- `main`: stable branch that should remain runnable.
- short-lived feature branches for meaningful work, for example:
  - `feat/onboarding-profile`
  - `feat/voice-calibration`
  - `feat/daily-session`
  - `feat/memory-mastery`
  - `fix/interviewer-hint-leak`

Do not create unnecessary long-lived branches or a complex GitFlow process.

Codex should not make large experimental changes directly on `main` when a feature branch can isolate the work.

## 20.4 Commit Strategy
Prefer milestone-oriented, atomic commits.

Good examples:
- `chore: scaffold Next.js and FastAPI apps`
- `feat: add resume PDF profile extraction`
- `feat: persist confirmed learner profile`
- `feat: add voice attempt transcription`
- `feat: implement expression mastery state machine`
- `test: add interviewer no-hint regression case`
- `fix: preserve attempt when analyzer fails`

Avoid vague commits such as:
- `update`
- `changes`
- `fix stuff`
- `big refactor`

A commit should represent one understandable unit that can be reverted without unintentionally removing unrelated features.

## 20.5 Checkpoints Before Risky Changes
Before any change that is broad, destructive, architectural, or difficult to reverse, Codex must create a safe Git checkpoint.

Examples:
- database schema refactor;
- replacing an AI provider abstraction;
- changing Session Orchestrator behavior;
- rewriting memory/mastery logic;
- broad frontend restructuring;
- large dependency upgrades.

The checkpoint may be a clean commit on the current feature branch before the risky change begins.

## 20.6 Rollback Safety
If a change breaks the app, Codex should first identify the last known-good commit and explain the proposed rollback/fix path.

Do not use destructive Git commands against user work unless explicitly approved.

In particular, Codex must not casually use operations such as:
- force-pushing shared history;
- deleting branches containing unmerged work;
- `git reset --hard` when uncommitted user work may exist;
- history rewriting solely to hide an implementation mistake.

Prefer:
- fix-forward on the feature branch when the change is small;
- `git revert` for already-committed changes that should be safely undone;
- a new branch from a known-good commit for larger recovery work.

## 20.7 Pre-Commit / Pre-Merge Checks
Before committing a milestone or merging a feature branch into `main`, run the relevant available checks.

At minimum, as the project matures:
- backend tests;
- frontend lint/type checks;
- core domain unit tests;
- critical AI regression fixtures when affected;
- database migration validation when schema changes;
- a basic end-to-end smoke check for the affected golden path.

Do not merge known failing code into `main` merely to continue development.

## 20.8 Milestone Tags
When a major MVP milestone is verified end-to-end, create a human-readable Git tag where useful.

Examples:
- `m0-foundation`
- `m1-profile`
- `m2-voice-calibration`
- `m3-core-session`
- `m4-memory-mastery`
- `m5-cross-session-loop`
- `mvp-v1.0`

Tags are optional during very early scaffolding but recommended once milestones become stable enough to serve as rollback anchors.

## 20.9 GitHub Usage
GitHub should be used as:
- remote backup;
- version history;
- milestone checkpoint;
- future portfolio repository.

The local repository and GitHub remote must remain aligned deliberately. Codex should not push automatically unless the user asks it to do so or grants that responsibility for the current workflow.

Before a push, Codex should summarize:
- branch;
- commits to be pushed;
- tests/checks run;
- any known limitations.

## 20.10 Architecture Change Discipline
If implementation requires a material departure from this Build Specification or from an established architecture boundary, Codex should not silently refactor the system.

Instead:
1. describe the proposed change;
2. explain why the existing design is insufficient;
3. state affected modules/data/migrations;
4. identify rollback risk;
5. update relevant documentation/specification after approval;
6. implement the change on an isolated branch.

This requirement is specifically intended to prevent Vibe Coding drift over time.


# 21. MVP Acceptance Criteria

The MVP is considered functionally successful when the following end-to-end path works:

1. New user can select interface/support language and target role.
2. User can upload a resume PDF or paste text.
3. System extracts a structured candidate profile.
4. User can review/edit/confirm it.
5. Confirmed profile is persisted and used by later sessions.
6. User completes 3 personalized voice calibration questions.
7. Audio is transcribed and an initial learner profile is produced.
8. System creates/starts the 30-day program.
9. User can choose a 10/20/30/60-minute daily session.
10. Full session supports Recall/Learn/Imitate/Retrieve/Transfer/Interview/Recap.
11. User voice attempts are stored with transcript and relevant metadata.
12. System can identify a target expression and create an Expression record.
13. Later session can retrieve a due expression and create a natural test opportunity.
14. Interviewer does not reveal the target expression.
15. Correct independent usage creates ExpressionAttempt evidence.
16. Mastery state changes only through deterministic verified rules.
17. Error patterns can progress from candidate to active/improving/resolved rather than becoming permanent labels after one mistake.
18. My English displays Expressions, Patterns, and Stories.
19. Mock Interview works without mid-answer correction.
20. Streak/XP/30-day map update.
21. If an analyzer/model call fails, the user's saved attempt is not lost.
22. Core domain tests pass.
23. English/Simplified Chinese interface switching does not alter learner state.
24. Application can be restarted/deployed without losing persistent learner data.

Critical MVP validation:

**A user learns an expression in one session and later independently uses it in a different question/session; FluentLoop detects this with evidence and updates progress.**

---

# 22. Implementation Sequence for Codex

Codex should propose its own detailed implementation plan, but the recommended milestone order is:

## Milestone 0 - Foundation
- repo scaffold
- environment/config
- frontend/backend connection
- database migrations
- basic auth/user
- health checks
- test setup

## Milestone 1 - Onboarding & Profile
- language/goal preferences
- PDF/text import
- source document storage
- profile extraction
- profile review/confirmation

## Milestone 2 - Voice Calibration
- recording
- audio storage
- STT
- attempts
- initial learner analysis

## Milestone 3 - Core Daily Session
- program/curriculum seed
- session orchestrator
- Today page
- Recall/Learn/Imitate/Retrieve/Transfer/Interview/Recap shell

## Milestone 4 - Memory & Mastery
- Expressions
- ExpressionAttempts
- ErrorPatterns
- Stories
- review scheduler
- mastery engine
- memory gate

## Milestone 5 - Cross-Session Loop
- due review retrieval
- hidden transfer opportunity
- verification
- Day 1 -> Day 2 aha path

## Milestone 6 - Practice & Progress
- Mock Interview
- Quick Review
- XP/streak
- Journey map
- My English

## Milestone 7 - Hardening
- regression cases
- failure recovery
- i18n completeness
- logging
- security/data isolation checks
- responsive UX
- README/setup instructions

Do not begin V1.5/V2 before the MVP acceptance path is working end-to-end.

---

# 23. Instructions for Codex Before First Code Change

Before coding, return:

1. Proposed implementation plan by milestone.
2. Proposed database schema at a practical level.
3. Proposed API surface at a practical level.
4. Which parts will be deterministic code vs LLM calls.
5. How provider abstraction will be implemented.
6. How Context Builder and Memory Gate will prevent unbounded/unsafe memory behavior.
7. How the architecture allows future Small Talk, semantic memory, alternative interviewer accents, and new programs without rewriting the core.
8. Any contradictions or implementation-critical ambiguities found in this specification.
9. The smallest vertical slice that can prove the Day 1 -> Day 2 cross-session retrieval loop.

After review, implement incrementally.

---

# 24. Product Design Principles

When implementation decisions are ambiguous, prefer these principles in order:

1. **Retrieval over passive consumption.**
2. **Transfer over memorized model answers.**
3. **User-confirmed facts over AI assumptions.**
4. **Evidence over vague AI judgments.**
5. **Deterministic rules over unnecessary LLM calls.**
6. **Focused correction over exhaustive correction.**
7. **Progressive removal of scaffolding.**
8. **Simple user experience over exposing backend complexity.**
9. **Structured memory over dumping history into context.**
10. **Extension by addition over rewrite.**
11. **Working vertical slice over premature infrastructure.**
12. **MVP scope discipline over feature accumulation.**

---

# 25. Final Build Intent

FluentLoop should feel simple to the learner even though the backend maintains structured learner state.

The user experience should approximately feel like:

**Open app -> know exactly what to practice -> speak -> receive focused help -> speak again without help -> face a realistic follow-up -> finish -> return later -> unexpectedly retrieve yesterday's language -> see concrete evidence of progress.**

The MVP should prove this loop before expanding into a broader AI English-learning platform.
