# FluentLoop Issues

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
