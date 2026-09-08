"use client";

import { useRef, useState } from "react";

import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { useInterfaceLocale } from "@/components/interface-locale-provider";
import { getMessages } from "@/lib/i18n";
import {
  advanceDailySession, completeDailySession, createDailySession, dailyStepTts,
  DailySessionCompletion, DailySessionResponse, DailyStep, getDailyAttempts,
  retryDailyAttempt, submitDailyAttempt, VoiceAttempt,
} from "@/lib/api";

const VOICE_STEPS = new Set<DailyStep>(["RECALL", "IMITATE", "RETRIEVE", "TRANSFER", "INTERVIEW"]);

function promptForStep(session: DailySessionResponse, step: DailyStep) {
  if (step === "IMITATE") return session.content.imitation_variants[0] ?? session.content.reference_answer;
  if (step === "TRANSFER") return session.content.transfer_prompts[0] ?? session.content.question_prompt;
  if (step === "INTERVIEW") return session.content.follow_up_questions[0] ?? session.content.question_prompt;
  if (step === "LEARN") return session.content.reference_answer;
  return session.content.question_prompt;
}

export function TodaySessionLive({ token }: { token: string }) {
  const [session, setSession] = useState<DailySessionResponse | null>(null);
  const [step, setStep] = useState(0);
  const [attempt, setAttempt] = useState<VoiceAttempt | null>(null);
  const [recording, setRecording] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [completion, setCompletion] = useState<DailySessionCompletion | null>(null);
  const recorder = useRef<MediaRecorder | null>(null);
  const chunks = useRef<Blob[]>([]);
  const startedAt = useRef(0);
  const { locale } = useInterfaceLocale();
  const copy = getMessages(locale).m6.today;

  async function loadAttempt(current: DailySessionResponse) {
    const attempts = await getDailyAttempts(token, current.session_id);
    setAttempt(attempts.find((item) => item.question_type === current.plan.steps[current.current_step]) ?? null);
  }

  async function begin() {
    setBusy(true); setError("");
    try {
      const created = await createDailySession(token);
      setSession(created); setStep(created.current_step); setCompletion(null);
      await loadAttempt(created);
    } catch (caught) { setError(caught instanceof Error ? caught.message : copy.error); }
    finally { setBusy(false); }
  }

  async function complete() {
    if (!session) return;
    setBusy(true); setError("");
    try { setCompletion(await completeDailySession(token, session.session_id)); }
    catch (caught) { setError(caught instanceof Error ? caught.message : copy.error); }
    finally { setBusy(false); }
  }

  async function continueStep() {
    if (!session) return;
    setBusy(true); setError("");
    try {
      const advanced = await advanceDailySession(token, session.session_id);
      setSession(advanced); setStep(advanced.current_step); await loadAttempt(advanced);
    } catch (caught) { setError(caught instanceof Error ? caught.message : copy.error); }
    finally { setBusy(false); }
  }

  async function playPrompt() {
    if (!session) return;
    try {
      const blob = await dailyStepTts(token, session.session_id, session.plan.steps[step]);
      void new Audio(URL.createObjectURL(blob)).play();
    } catch (caught) { setError(caught instanceof Error ? caught.message : copy.audioFallback); }
  }

  async function startRecording() {
    setError("");
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      chunks.current = [];
      recorder.current = new MediaRecorder(stream);
      recorder.current.ondataavailable = (event) => { if (event.data.size) chunks.current.push(event.data); };
      recorder.current.start(); startedAt.current = Date.now(); setRecording(true);
    } catch { setError(copy.micError); }
  }

  function stopRecording() {
    const active = recorder.current;
    if (!active || !session) return;
    const currentStep = session.plan.steps[step];
    active.onstop = async () => {
      active.stream.getTracks().forEach((track) => track.stop());
      setRecording(false); setBusy(true);
      try { setAttempt(await submitDailyAttempt(token, session.session_id, currentStep, new Blob(chunks.current, { type: active.mimeType || "audio/webm" }), Date.now() - startedAt.current)); }
      catch (caught) { setError(caught instanceof Error ? caught.message : copy.error); }
      finally { setBusy(false); }
    };
    active.stop();
  }

  async function retry() {
    if (!attempt) return;
    setBusy(true); setError("");
    try { setAttempt(await retryDailyAttempt(token, attempt.id)); }
    catch (caught) { setError(caught instanceof Error ? caught.message : copy.error); }
    finally { setBusy(false); }
  }

  if (!session) return <Card className="today-card"><p className="eyebrow">{copy.eyebrow}</p><h2>{copy.title}</h2><p className="card-copy">{copy.copy}</p><Button disabled={busy} onClick={() => void begin()}>{busy ? copy.preparing : copy.start}</Button>{error && <p className="error" role="alert">{error}</p>}</Card>;

  const currentStep = session.plan.steps[step];
  const finished = step === session.plan.steps.length - 1;
  const voiceStep = VOICE_STEPS.has(currentStep);
  const analyzed = attempt?.status === "ANALYZED";
  return <Card className="today-card"><div className="today-heading"><div><p className="eyebrow">{copy.day} {session.plan.day} · {copy.phaseCopy[session.plan.phase]}</p><h2>{promptForStep(session, currentStep)}</h2></div><span className="today-duration">{session.plan.duration_minutes} {copy.minutes}</span></div><div className="today-progress" aria-label={copy.eyebrow}>{session.plan.steps.map((item, index) => <span key={item} data-active={index === step} data-complete={index < step || completion !== null} title={copy.stepCopy[item]} />)}</div><p className="today-step"><strong>{copy.stepCopy[currentStep]}</strong> · {completion ? `${copy.saved}: +${completion.awarded_xp} XP · ${completion.progress.current_streak}${copy.streak}` : finished ? copy.recap : copy.continue}</p><p className="card-copy">{completion ? completion.progress.program_completed_at ? copy.programComplete : `${copy.tomorrow} ${completion.progress.current_day}.` : voiceStep ? copy.voiceInstruction : session.content.language_explanations[0] ?? copy.copy}</p>{voiceStep && !analyzed && <div className="form-actions"><Button className="button-secondary" disabled={busy} onClick={() => void playPrompt()}>{copy.listen}</Button>{!recording ? <Button disabled={busy || !!attempt} onClick={() => void startRecording()}>{copy.record}</Button> : <Button onClick={stopRecording}>{copy.stop}</Button>}</div>}{busy && <p className="notice">{copy.processing}</p>}{attempt && <div className="transcript"><strong>{copy.transcript}</strong><p>{attempt.transcript ?? attempt.provider_error}</p>{attempt.status !== "ANALYZED" && <Button disabled={busy} onClick={() => void retry()}>{copy.retry}</Button>}</div>}<Button disabled={busy || completion !== null || (voiceStep && !analyzed)} onClick={() => finished ? void complete() : void continueStep()}>{busy ? copy.saving : completion ? copy.completed : finished ? copy.complete : copy.continue}</Button>{error && <p className="error" role="alert">{error}</p>}</Card>;
}
