"use client";

import { useState } from "react";

import { advanceDailySession, completeDailySession, createDailySession, DailySessionCompletion, DailySessionResponse } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { useInterfaceLocale } from "@/components/interface-locale-provider";
import { getMessages } from "@/lib/i18n";

export function TodaySession({ token }: { token: string }) {
  const [session, setSession] = useState<DailySessionResponse | null>(null);
  const [step, setStep] = useState(0);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [completion, setCompletion] = useState<DailySessionCompletion | null>(null);
  const { locale } = useInterfaceLocale();
  const copy = getMessages(locale).m6.today;

  async function begin() {
    setBusy(true);
    setError("");
    try {
      const created = await createDailySession(token);
      setSession(created);
      setStep(created.current_step);
      setCompletion(null);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : copy.error);
    } finally {
      setBusy(false);
    }
  }

  async function complete() {
    if (!session) return;
    setBusy(true);
    setError("");
    try {
      setCompletion(await completeDailySession(token, session.session_id));
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : copy.error);
    } finally {
      setBusy(false);
    }
  }

  async function continueStep() {
    if (!session) return;
    setBusy(true);
    setError("");
    try {
      const advanced = await advanceDailySession(token, session.session_id);
      setSession(advanced);
      setStep(advanced.current_step);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : copy.error);
    } finally {
      setBusy(false);
    }
  }

  if (!session) {
    return <Card className="today-card"><p className="eyebrow">{copy.eyebrow} · Day 1</p><h2>{copy.title}</h2><p className="card-copy">{copy.copy}</p><Button disabled={busy} onClick={() => void begin()}>{busy ? copy.preparing : copy.start}</Button>{error && <p className="error" role="alert">{error}</p>}</Card>;
  }

  const currentStep = session.plan.steps[step];
  const finished = step === session.plan.steps.length - 1;
  return <Card className="today-card"><div className="today-heading"><div><p className="eyebrow">Day {session.plan.day} · {session.plan.phase}</p><h2>{session.content.question_prompt}</h2></div><span className="today-duration">{session.plan.duration_minutes} min</span></div><div className="today-progress" aria-label={copy.eyebrow}>{session.plan.steps.map((item, index) => <span key={item} data-active={index === step} data-complete={index < step || completion !== null} title={item} />)}</div><p className="today-step"><strong>{currentStep}</strong> · {completion ? `${copy.saved}: +${completion.awarded_xp} XP · ${completion.progress.current_streak}${copy.streak}` : finished ? copy.recap : copy.continue}</p><p className="card-copy">{completion ? completion.progress.program_completed_at ? copy.programComplete : `${copy.tomorrow} ${completion.progress.current_day}.` : session.content.language_explanations[0] ?? copy.copy}</p><Button disabled={busy || completion !== null} onClick={() => finished ? void complete() : void continueStep()}>{busy ? copy.saving : completion ? copy.completed : finished ? copy.complete : copy.continue}</Button>{error && <p className="error" role="alert">{error}</p>}</Card>;
}
