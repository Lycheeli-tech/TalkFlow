# FluentLoop MVP UI Wireframe Contract

## Purpose and Authority

This is a low-fidelity interaction and information-hierarchy contract for FluentLoop MVP UI. It defines screen families, navigation, learning-state presentation, and reusable interaction patterns. It is not a pixel-perfect visual specification or a full design system.

Source-of-truth hierarchy:

`FLUENTLOOP_MVP_BUILD_SPEC_v1.1.md`
→ authoritative product behavior and architecture

`docs/UI_WIREFRAMES.md`
→ UI hierarchy and interaction contract

Existing design tokens and reusable components
→ visual implementation language

If this document conflicts with the Build Spec, the Build Spec wins. Existing M1/M2 UI is not to be cosmetically refactored to match this document. Change it only for a required behavior, navigation, accessibility/responsiveness, or concrete later-integration conflict.

## 1. Global Authenticated Shell

The authenticated app is mobile-first. Primary navigation is always:

- Today
- Practice
- My English
- Journey

Mobile uses bottom navigation. Desktop may adapt it into another placement while preserving exactly this information architecture. The shell may surface current day, phase, streak, XP/level, and profile/settings access when useful; it must not turn every screen into a metrics dashboard.

```text
FluentLoop                              🔥 streak

                    PAGE CONTENT

Today              Practice          My English       Journey
```

## 2. Today / Home

Today answers one question immediately: **What should I train today?** It has one clear primary CTA, not a course catalog.

```text
DAY 06 · BUILD                              🔥 7

Good morning

Today's Focus
[planner-selected topic]

[ Continue Training                         ]
[ Recall and reuse what you learned.     → ]

Today's Session
● Recall  ○ Learn  ○ Imitate  ○ Retrieve
○ Transfer  ○ Interview  ○ Recap
```

Topic and plan come from the Daily Planner/curriculum runtime. The UI must not encode a rigid Day 2–30 topic calendar.

## 3. Canonical Daily Training Shell

All daily steps use one reusable Training Shell, not seven unrelated layouts.

```text
DAY 06 · BUILD                         progress

RETRIEVE

[ primary task or learning content ]
[ turn-based voice interaction     ]
[ contextual help when allowed     ]

[ Continue ]
```

The learner must always know where they are, what type of response is expected, whether the task is imitation/recall/transfer/free speech, and what happens next. Keep pre-speaking instruction brief.

Canonical order is always:

`Recall → Learn → Imitate → Retrieve → Transfer → Interview → Recap`

### Recall

Retrieve prior learning without immediately revealing the target expression. Speaking is primary. Show hints only when current scaffolding policy permits them.

```text
RECALL
Yesterday you learned an expression for [skill].
[question]
[ 🎙 Speak ]
Need a hint?
```

### Learn

Teach a deliberately small amount of high-value reusable material, preferably connected to the learner's own attempt.

```text
LEARN
You said: [attempt]
More natural: [small improvement]
Why it works: [short explanation]
Useful expression: [chunk]
[ ▶ Hear it ]                         [ Continue ]
```

Do not create textbook-sized explanations.

### Imitate

Use replay and simple re-recording to build phrase familiarity. Do not claim precise phoneme/accent scoring.

```text
IMITATE
[ ▶ Listen to phrase ]
Now say it naturally.
[ 🎙 Speak ]       Try again           [ Continue ]
```

### Retrieve

Require independent production without copying a reference answer. Post-attempt feedback is short: a win, the most useful correction(s), and evidence where applicable.

```text
RETRIEVE
No answer this time.
[question]
[ 🎙 Speak ]
Need a hint?
```

### Transfer

Change the question/context and test the same skill. Never tell the learner exactly which target expression to use.

```text
TRANSFER
New question. Same skill.
[new context question]
[ 🎙 Speak ]
```

### Interview

Use Interviewer framing, reduced coach intervention, no mid-answer correction, and no answer hints during the response. BUILD may be supportive; TRANSFER reduces scaffolding; PERFORM is increasingly interview-like. No realtime voice UX.

```text
INTERVIEW
Interviewer
[question]
[ 🎙 Answer ]
No hints during this answer.
```

### Recap

Close with a small motivating summary: useful expressions strengthened, one important pattern, session reward/progress, and the next retrieval expectation. Do not present every internal metric or claim future mastery prematurely.

```text
SESSION COMPLETE
+ XP / streak continuation
Today you strengthened: [small list]
One thing to remember: [one priority]
[ Finish ]
```

## 4. Voice Interaction Pattern

Calibration, Daily Training, and later Mock Interview share one turn-based recording pattern:

```text
[ 🎙 Speak ] → Recording… → [ ■ Stop ]
→ Uploading… → Processing… → Transcript / feedback
```

Required visible states: idle, permission request, recording, uploading, processing, success, and recoverable failure. Controls are large and reachable on mobile. Preserve the existing raw-audio-before-analysis behavior. Do not introduce streaming, barge-in, or realtime conversational UI.

## 5. My English

My English represents learner assets and recurring weaknesses. Its future primary tabs are:

- Expressions
- Patterns
- Stories

```text
MY ENGLISH
Expressions | Patterns | Stories
Due Today: [count]
[expression]  [state]
```

Patterns can show a concise observed-example → preferred-expression relationship. Stories are reusable interview stories, not a M3 content-management product. Until Memory/Mastery exists, the UI may reserve this navigation location but must not pretend these records or due counts already exist.

## 6. Journey

Journey visualizes stage progression, not a hard-coded daily content calendar.

```text
BUILD       Days 1–10
TRANSFER    Days 11–20
PERFORM     Days 21–30

01 ●  02 ●  ...  06 ◉ You are here  ... 30 🏆
```

It may surface streak, level, and current location sparingly. Daily content remains planner-selected within the fixed backbone plus adaptive layer.

## 7. Practice

Practice remains intentionally small:

```text
PRACTICE
[ Mock Interview  — Practice under pressure       → ]
[ Quick Review    — Review due expressions         → ]
```

The contract reserves locations for MVP Practice modes. It does not authorize premature Mock Interview, Quick Review, or marketplace implementation.

## 8. Coach, Rewards, and Feedback

Coach personality is behavioral composition, not separate application layouts. It can affect feedback tone, encouragement, pressure, hint behavior, and challenge framing; it must never alter deterministic learning/mastery rules.

Visible feedback follows correction budget: normally one Fix Now, up to two Improve items, and one Win. Avoid persistent coach popups.

Rewards reinforce meaningful retrieval, transfer, session completion, streak, and milestones. They may include XP, streak, level, achievements, and Journey progress, but should not reward meaningless taps or create a complex economy.

## 9. Bilingual and Responsive Requirements

- Interface language is English or Simplified Chinese; learning language remains English.
- Support language controls explanations/scaffolding independently of interface language.
- UI strings use i18n keys; changing interface language must not mutate learner state.
- Do not translate target English expressions/answers in a way that undermines retrieval unless that step explicitly teaches/explains them.
- Design first for approximately 375px width: no horizontal overflow, readable questions, limited density, reachable actions, obvious recording state, and bottom navigation.
- Desktop adapts gracefully without becoming a different information architecture.

## 10. Visual Freedom and Scope

Reuse existing token-driven M1/M2 visual language and reusable components. This contract does not dictate color, typography, exact spacing, border radii, animation, or pixel dimensions.

It does not authorize V1.5/V2 work, realtime voice, advanced pronunciation scoring, a complex reward economy, semantic memory, or implementation of later milestones before their approved scope.
