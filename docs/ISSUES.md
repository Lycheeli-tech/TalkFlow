# FluentLoop Issues

## AUTH-03: Hour-long access token expired without renewal

Status: CLOSED — original account restored; persistent session/refresh regressions and data digests passed.

- During review, Course API returned 401 and the UI fell back to login. Old Course Core auth retained
  only access_token in sessionStorage, discarded refresh_token and had no renewal lifecycle.
- Original confirmed review account password login succeeded (200); provider access-token lifetime is
  3600 seconds and a refresh token is supplied. The account was not deleted or unconfirmed.
- ADR-033 implements persistent browser session and single-flight pre-request/active-page renewal;
  all authenticated Course/About Me/Practice clients use it. 401 retries once for the same owner;
  transient outages retain credentials, late responses/new-login and cross-tab sign-out are guarded.
- Fourteen frontend regressions passed, including simulated three-day absence, rotation, concurrency,
  outages and owner-switch/logout races. Actual provider refresh returned 200 for the original owner.
  Frontend ESLint/TypeScript/production build and backend 298 passed / 13 skipped passed.
- Original account restored via UI; independent new page opened authenticated with original two roles,
  two PDFs and supplemental fact. Profile/role/SourceDocument/Memory/Answer/Transcript/Feedback row
  digests match the pre-recovery snapshot. No new account, reset, cleanup or business/schema changes.
- Three days are covered by retained-account policy and simulated expiry/real refresh verification;
  no claim of waiting 72 hours in real time. Explicit sign-out still requires same-account sign-in.

## ABOUT-10: Supplemental facts save had no visible progress or confirmation

Status: CLOSED — TypeScript/ESLint/build passed; browser saving/saved states verified.

- User perceived the save button as ineffective. Logs showed two PATCH 200 / GET 200 pairs;
  owner-scoped read-only database verification found one saved 19-character fact. No request,
  validation or persistence failure was present, and the UI had neither progress nor success status.
- About Me now displays saving/saved feedback next to the facts button. Success requires the save
  and reload requests to finish; errors retain their alert without showing success. Editing clears
  the old saved message; textarea/buttons are disabled while an operation is pending.
- Backend, Memory decisions, schema and existing facts are unchanged. Frontend ESLint, TypeScript
  and production build passed; browser showed saving status with repeated-input protection.
  The same existing facts completed with saved status, no error and editable input restored.

## RESUME-09: Chinese display filename caused upload Failed to fetch

Status: CLOSED — real Chinese PDF upload/parse/list/delete passed; 298 backend tests passed.

- User review reached authenticated About Me; resumes POST returned 500 while other reads and
  role writes worked. Storage rejected the original Unicode object name with `InvalidKey 400`.
  The unhandled upload exception surfaced as a browser network/CORS error rather than a detail.
- A same-bucket synthetic probe reproduced Unicode 400 / ASCII 200 and removed its test object.
- Product-neutral DocumentStorage now uses `{owner}/{document}/resume.pdf`; SourceDocument still
  retains the exact original display filename. Existing saved paths and private ownership are unchanged.
  HTTP/storage failures become a safe typed exception; About Me returns readable 503 with CORS headers.
- Mock HTTP regressions cover Unicode/accented/path-like display names, provider/network failures,
  unchanged raw bytes and API 503/CORS. Real disposable-account Chinese PDF POST 201, parse/list/name
  preservation and DELETE passed; account/source/job/Storage fixtures removed (all residuals zero).
- Ruff check/format and full backend 298 passed / 13 opt-in skipped. No frontend, schema, Legacy
  business or user data changes. Backend restarted with the fix; original About Me page refreshed.

## GIT-07: P7 remote push blocked by GitHub HTTPS connectivity

Status: CLOSED — retry succeeded; P7 refs verified remotely at main `66de471`, branch/tag `ac360dd`.

- 2026-09-13 user authorized P7 merge/push, then P8. Local main fast-forwarded from `71f606b`
  to P7 checkpoint `ac360dd`; original `frontend/next-env.d.ts` changes were preserved.
- Two escalated `git fetch origin` attempts failed: connection reset, then GitHub port 443 timeout.
  Atomic push with HTTP/1.1 also failed to connect after 21s. This was a network failure, not an
  automatic approval rejection, authentication error or non-fast-forward conflict.
- DNS resolved github.com to 20.205.243.166. Independent IPv4 HTTPS HEAD timed out after 8s;
  no environment/Git HTTP proxy was detected. No credentials or network settings were changed.
- Recovery: restore external GitHub HTTPS connectivity; fetch/check remote main, then retry
  `git -c http.version=HTTP/1.1 push --atomic origin main codex/course-core-stage-7 refs/tags/course-core-stage-7`.
  All refs are now verified; P8 TBD-007 approved under ADR-032. No further network diagnosis needed.

## PRACTICE-08: Expiry policy used transaction-start time

Status: CLOSED — final real PostgreSQL regression passed (1 passed, 18.81s).

- Initial P8 rolled-back integration passed saves, idempotency, RLS ownership and cleanup retry,
  but an expired owned Run stayed readable inside the long outer test transaction.
- PostgreSQL `now()` is fixed at transaction start, so it cannot enforce expiry during a long
  transaction. P8 RLS now compares against `statement_timestamp()`; application GET and cleanup
  additionally check actual UTC expiry. Migration `202609130021` is applied/registered in the test DB.
- Re-run `test_practice_v2_database_integration.py` with the opt-in environment flag; no production
  schema or Legacy behavior changed. P8 retention is approved in ADR-032.

## PRACTICE-09: Silence accepted as a punctuation-only Answer

Status: CLOSED — actual device silence and same-recording retry remained FAILED; automated cases passed.

- P8 actual microphone smoke reached RECORDING with blocked question/navigation controls; stop
  uploaded audio and ASR returned only punctuation. `strip()` was not sufficient to detect no speech.
- P8 now requires at least one alphanumeric character in the final STT text; punctuation-only
  output becomes a FAILED attempt with retained audio and same-attempt retry. Course/Legacy unchanged.
- Initial synthetic helper timed out before localhost Run creation because HTTPX inherited the
  environment proxy. Local HTTP requests now use a separate client with `trust_env=False`;
  external Auth/TTS/provider calls keep normal proxy settings. No proxy configuration was changed.

## PRACTICE-10: Provider cited a Question instead of an Answer excerpt

Status: CLOSED — fixed-source Bailian fixture passed (9.72s), real synthetic voice complete passed (95).

- Synthetic voice passed actual TTS/upload/STT/audio replay; complete returned 503 and preserved
  the Run. A separate fixed-text Bailian fixture reproduced a citation quoting Question text.
- Practice feedback now supplies deterministic transcript-only quote IDs. The provider selects an
  ID and writes an observation; code resolves both the exact quote and its Question ID, rejects
  unknown IDs, then applies existing exact-source validation. No AI state decisions or new history.
- Re-run `test_practice_v2_live.py` and owner-scoped synthetic voice smoke; cleanup retry remains
  durable; final owner Run/job/Practice Storage object counts are all zero. Five-question browser
  completion also passed (92), with one voiced synthetic answer and four explicitly skipped questions.

## SHELL-08: Mobile navigation covered the language switch

Status: CLOSED — rebuilt Practice/Course language clicks and viewport navigation bounds passed.

- At 375x812, DOM bounds put the fixed navigation at y=24..71 inside the 72px sticky header,
  overlapping locale buttons at y=17..54. Clicking 中文 hit About Me instead. The header's backdrop
  filter established the fixed navigation's containing block; this pre-existing Course Core defect
  also appeared during P7 testing and was not caused by Practice state or locale persistence.
- Remove backdrop-filter only at the existing mobile breakpoint so navigation anchors to the
  viewport bottom. No Legacy component or route changed. Verify bounds and actual Chinese/English
  clicks on Practice and a Course; check recording still removes navigation links.

## PRACTICE-11: Upload completed after abandonment cleanup

Status: CLOSED — two service race cases and real PostgreSQL cleanup generation regression passed.

- A Run can be abandoned while a Storage upload is pending. Its deletion job may finish before
  the upload returns, leaving a late object without a Run or pending job.
- After late upload success or lost-response failure, missing Run ownership re-registers only the
  previously owned Practice path. Cleanup deletes/updates a job only if its schedule and attempt
  still match, preserving a newer registration. Real PostgreSQL regression passed (18.81s).

## AUTH-02: P6 device smoke used an unconfirmed disposable account

Status: CLOSED — replacement confirmed device account successfully used for recording and saved Answers.

- User reported failed login; the current Course 11 login page displayed `Email not confirmed`.
  User clarified that the account is disposable and has no real inbox; asking for email verification
  was the wrong recovery path. No existing user's confirmation state was changed.
- Added `course_stage6_acceptance.py prepare-device`: creates a dedicated confirmed disposable Auth
  user and verifies password login without generating TTS audio. The account must remain available
  until user-operated device smoke completes, then use the existing owner-scoped cleanup command.
- Credentials are stored only in OS temporary state, never in repository docs. No email was sent.

## COURSE-06: P6 real-audio closeout and device-browser limitation

Status: CLOSED — code defects fixed and user-operated actual device microphone smoke passed.

- Real Chinese audio exposed shared ASR's hard-coded en: Course Chinese now injects zh, preserving
  the default English/Legacy contract. Real Chinese Transcript and dual Draft passed.
- Supabase single-object DELETE returned 400; exact `prefixes` bulk-delete succeeded. A concurrent
  completed cleanup followed by late failure produced CLEANUP_FAILED with a null path; repository
  failure marking now cannot downgrade completed cleanup. Unit and real PostgreSQL regressions cover it.
- P6 native Draft confirmation blocked IAB automation; replaced only P6 discard/reanswer with explicit
  page-level second confirmation. Authenticated 375px discard/reanswer now passed.
- User authorized localhost:3100 microphone and Chrome fallback. IAB getUserMedia remains pending
  without a visible permission result; `createBrowserTab('chrome', ...)` reports browser unavailable.
  No fake microphone injection or alternate unapproved UI automation was used.
- 2026-09-13 resume: Chrome exists as a native window, but its browser connector still reports
  unavailable. Automatic approval rejected native `sky` activation/read because the active interface
  requires `cua_repl`; native control is disabled there. Do not retry through shell/CDP or change privacy
  settings. User-operated Chrome is the remaining device-smoke path.
- Resume checks passed: backend 153 passed / 10 opt-in skipped, Ruff check/format, frontend
  TypeScript/ESLint/production build, 20-migration validation, and read-only live migration registry
  verification of `202609130020`. No migration was reapplied and no test account/data was created.
- Final evidence: user-operated IAB produced two saved English device Answers and one confirmed Chinese
  device Answer (31,226 ms, WebM/Opus). Chinese STT and organizer used Bailian, dual texts and both Prompt
  versions persisted, Feedback READY, confirmation returned 200, and History remained three after reload.
  No simulated microphone or generated audio was used for this device gate. Prior guard/responsive
  checks remain the evidence for those contracts; do not claim direct observation of every user action.
- Next: review P6 and clean its disposable owner-scoped account/data afterward; no migration replay or P7.

## AUTH-01: Expired-token dead end blocked the login entry path (FIXED)

Status: fix implemented and partially regression-tested; full authenticated-path re-validation
waits for a real Supabase account login.

### Symptom

During Phase 2 Gate C voice validation, Voice Calibration first failed with `Failed to fetch`.
After the previous session restored frontend→backend reachability, the error became
`The access token is invalid or expired`. Finally the login page appeared to offer no usable
entry path into the application.

### Confirmed root causes

1. Stale-token dead end. The app stores only a Supabase `access_token` in `sessionStorage`
   (no refresh-token lifecycle). `AppEntry` read the token once into state, so when the backend
   returned 401 and the previous fix removed the token from `sessionStorage`, `AppEntry` kept the
   stale token and the error string, rendering the error page with no way back to login. The
   401-cleanup added by the previous session was correct but incomplete: nothing made the app
   react to the removal.
2. Login-success dead end (pre-existing). A fresh-browser login happens inside `OnboardingFlow`,
   which wrote the new token to `sessionStorage` without notifying `AppEntry`. `AppEntry` therefore
   never fetched the application entry, `onReady` stayed undefined in the no-token branch, and a
   returning user with a confirmed profile was forced through Onboarding again instead of being
   routed by entry stage to CALIBRATION/TODAY.
3. Stale error state. A failed entry fetch left `error` set; after a later successful login the
   error page still rendered instead of the authenticated app.

### Fixes (in existing architecture, no new auth layer)

- `frontend/components/app-entry.tsx`: token is now read through `useSyncExternalStore`
  (same idiom as `interface-locale-provider.tsx`) with a storage/custom-event subscription, so
  token removal (401) falls back to the login UI and token creation routes by entry stage.
  A successful entry fetch clears stale `error`.
- `frontend/lib/api.ts`: exported `ACCESS_TOKEN_STORAGE_KEY` / `ACCESS_TOKEN_STORAGE_EVENT`;
  the 401 branch now dispatches the change event after removing the token.
- `frontend/components/onboarding-flow.tsx`: dispatches the change event after a successful
  sign-in/sign-up token write, and uses the shared key constant.

### Already tried earlier (previous session)

- Process restart; stale backend process cleanup; hydration timing adjustment;
  localhost/127.0.0.1 reachability investigation; stale-token cleanup on 401.
  Those steps were real but did not address the reactivity gaps above.

### Regression evidence

- Frontend `tsc --noEmit` and `eslint .` pass with the changes.
- Browser check: fresh unauthenticated context renders a usable login form.
- Browser check: injecting a stale token and reloading produces backend 401 → token removed from
  `sessionStorage` → UI returns to the login form; no error-page dead end, no redirect loop.
- Successful login → authenticated entry fetch → persisted TODAY routing has now passed repeatedly
  with a real account. Secondary routes use the same hydration-safe token subscription.

### Previous Gate C blocker

Real Supabase account authentication and the initial microphone path have now been exercised by
the user. The remaining Gate C work is persistence/provider/retry/reconnection evidence and final
browser smoke validation.

## GATE-C-01: Initial real-browser voice path reached Today (CLOSED)

### Evidence

- User completed three English Voice Calibration recordings in the local browser.
- User reached Today, saw five progress markers, completed Recap, and received `+1 XP`.
- A fresh login/reload resumed at Today; 375px viewport smoke had no horizontal overflow and no
  browser console errors or warnings were observed.
- A live aggregate database check found two completed three-attempt Calibration Sessions; all six
  Attempts were ANALYZED with audio paths, transcripts, and analysis, and two assessments existed.
- A recursive private Storage listing found 6 nested learner-audio objects totaling 1,696,172
  bytes; exact current-user attribution is still pending.
- Anonymous aggregate comparison matched database Attempts per user `[3, 3]` with Storage files
  per user directory `[3, 3]`; no IDs or paths were exposed.
- Two independent live database connections each found seven analyzed Attempts with audio
  references, transcripts, and analysis plus two assessments, and each loaded the same non-empty
  private audio object without printing content, IDs, paths, or credentials.
- The focused 4-test calibration service suite passed. A controlled analyzer outage retained the
  original audio/transcript and retried the same Attempt ID/path without duplication.
- An automated browser silent recording captured `audio/webm;codecs=opus`, stored non-empty private
  audio, and received the live Bailian no-text STT failure. The aggregate moved from 7 to 8 Attempts;
  clicking Retry did not create a ninth. The original `Failed to fetch` was a Session Pooler
  connection-invalidated 500 during the first Attempt lookup; safe read retry fixed it, and the
  browser Retry now returns normally to `STT_FAILED`.

### Interpretation

This confirms the reachable UI path, private-audio persistence, durable Attempt/transcript/analysis/
LearnerAssessment shape, reconnection, and the service-level failure/retry contract. It does not
replace a live browser/provider fault injection for the final failure-recovery evidence.

### Closeout

The authenticated Simplified Chinese route smoke passed and Gate C is complete.

## GATE-D-01: Daily Attempt types rejected by live CHECK constraint (FIXED)

### Symptom and cause

The first real Daily recording uploaded successfully but Attempt insertion returned HTTP 500 and
the browser displayed `Failed to fetch`. The live `attempts_question_type_check` still allowed only
calibration and Quick Review categories, so PostgreSQL rejected `RETRIEVE`.

### Fix and evidence

- Added and applied versioned migration `202609080011_daily_voice_attempts.sql`, preserving all
  previous categories and adding the five Daily voice step types.
- Repeated real browser submissions returned 200 and persisted `ANALYZED` Attempts with Bailian
  STT/analysis and non-empty private audio objects.
- Local migration validation passes for all eleven migrations.

## GATE-D-02: Secondary-route hydration and Journey localization gaps (FIXED)

- Practice, My English, and Journey previously read `sessionStorage` during the first client render,
  producing server/client text mismatch on refresh. They now use the shared hydration-safe access
  token subscription.
- Journey's hard-coded English summary, phase, day, and accessibility labels now use locale files;
  Daily phase/step/minute labels are localized as well.
- Post-fix reload showed no Next.js Issue badge or new console warning/error.
