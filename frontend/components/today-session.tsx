"use client";

import { useState } from "react";

import { completeDailySession, createDailySession, DailySessionCompletion, DailySessionResponse } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";

export function TodaySession({ token }: { token: string }) {
  const [session, setSession] = useState<DailySessionResponse | null>(null);
  const [step, setStep] = useState(0);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [completion, setCompletion] = useState<DailySessionCompletion | null>(null);

  async function begin() {
    setBusy(true);
    setError("");
    try {
      setSession(await createDailySession(token));
      setStep(0);
      setCompletion(null);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Today is unavailable.");
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
      setError(caught instanceof Error ? caught.message : "Your progress could not be saved.");
    } finally {
      setBusy(false);
    }
  }

  if (!session) {
    return <Card className="today-card"><p className="eyebrow">Today · Day 1</p><h2>Turn what you know into what you can say.</h2><p className="card-copy">A short, guided practice built around your confirmed profile.</p><Button disabled={busy} onClick={() => void begin()}>{busy ? "Preparing…" : "Start today"}</Button>{error && <p className="error" role="alert">{error}</p>}</Card>;
  }

  const currentStep = session.plan.steps[step];
  const finished = step === session.plan.steps.length - 1;
  return <Card className="today-card"><div className="today-heading"><div><p className="eyebrow">Day {session.plan.day} · {session.plan.phase}</p><h2>{session.content.question_prompt}</h2></div><span className="today-duration">{session.plan.duration_minutes} min</span></div><div className="today-progress" aria-label="Training progress">{session.plan.steps.map((item, index) => <span key={item} data-active={index === step} data-complete={index < step || completion !== null} title={item} />)}</div><p className="today-step"><strong>{currentStep}</strong> · {completion ? `Saved: +${completion.awarded_xp} XP · ${completion.progress.current_streak}-day streak.` : finished ? "You have reached the recap." : "Follow the prompt, then continue when ready."}</p><p className="card-copy">{completion ? `Tomorrow is Day ${completion.progress.current_day}.` : session.content.language_explanations[0] ?? "Use your own experience and keep the answer specific."}</p><Button disabled={busy || completion !== null} onClick={() => finished ? void complete() : setStep((value) => Math.min(value + 1, session.plan.steps.length - 1))}>{busy ? "Saving…" : completion ? "Today complete" : finished ? "Complete today" : "Continue"}</Button>{error && <p className="error" role="alert">{error}</p>}</Card>;
}
