"use client";

import { useRef, useState } from "react";

import { Button } from "@/components/ui/button";
import { calibrationTts, getCalibration, LearnerAssessment, retryCalibrationAttempt, startCalibration, submitCalibrationAttempt, VoiceAttempt } from "@/lib/api";

type Copy = Record<string, string>;

export function VoiceCalibration({ token, copy, onComplete }: { token: string; copy: Copy; onComplete?: () => void }) {
  const [sessionId, setSessionId] = useState("");
  const [questions, setQuestions] = useState<{ category: string; text: string }[]>([]);
  const [index, setIndex] = useState(0);
  const [recording, setRecording] = useState(false);
  const [attempt, setAttempt] = useState<VoiceAttempt | null>(null);
  const [assessment, setAssessment] = useState<LearnerAssessment | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const recorder = useRef<MediaRecorder | null>(null);
  const chunks = useRef<Blob[]>([]);
  const startedAt = useRef(0);

  async function begin() {
    setBusy(true); setError("");
    try { const session = await startCalibration(token); setSessionId(session.id); setQuestions(session.questions); }
    catch (caught) { setError(caught instanceof Error ? caught.message : copy.error); }
    finally { setBusy(false); }
  }

  async function playQuestion() {
    if (!questions[index]) return;
    try { const blob = await calibrationTts(token, sessionId, questions[index].category); new Audio(URL.createObjectURL(blob)).play(); }
    catch (caught) { setError(caught instanceof Error ? caught.message : copy.ttsFallback); }
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
    if (!active) return;
    active.onstop = async () => {
      active.stream.getTracks().forEach((track) => track.stop());
      setRecording(false); setBusy(true);
      try {
        const saved = await submitCalibrationAttempt(token, sessionId, questions[index].category, new Blob(chunks.current, { type: active.mimeType || "audio/webm" }), Date.now() - startedAt.current);
        setAttempt(saved);
      } catch (caught) { setError(caught instanceof Error ? caught.message : copy.error); }
      finally { setBusy(false); }
    };
    active.stop();
  }

  async function next() {
    setAttempt(null);
    if (index < 2) { setIndex(index + 1); return; }
    setBusy(true);
    try { const result = await getCalibration(token, sessionId); setAssessment(result.assessment); }
    catch (caught) { setError(caught instanceof Error ? caught.message : copy.error); }
    finally { setBusy(false); }
  }

  async function retry() {
    if (!attempt) return;
    setBusy(true); setError("");
    try { setAttempt(await retryCalibrationAttempt(token, attempt.id)); }
    catch (caught) { setError(caught instanceof Error ? caught.message : copy.error); }
    finally { setBusy(false); }
  }

  if (!sessionId) return <div className="completion"><span className="completion-mark">✓</span><h2>{copy.readyTitle}</h2><p>{copy.readyCopy}</p><Button disabled={busy} onClick={begin}>{busy ? copy.working : copy.begin}</Button>{error && <p className="error">{error}</p>}</div>;
  if (assessment) return <div className="assessment"><p className="eyebrow">{copy.provisional}</p><h2>{copy.assessmentTitle}</h2><div className="dimension-grid">{["fluency", "naturalness", "grammar", "retrieval", "structure"].map((key) => <div key={key}><span>{copy[key]}</span><strong>{assessment[key as keyof LearnerAssessment] as string}</strong></div>)}</div><h3>{copy.primaryFocus}</h3><p>{assessment.primary_focus}</p><p className="card-copy">{copy.evolves}</p>{onComplete && <Button onClick={onComplete}>{copy.continue ?? "Continue"}</Button>}</div>;
  const question = questions[index];
  return <div className="calibration"><p className="eyebrow">{copy.question} {index + 1} / 3 · {question.category}</p><h2>{question.text}</h2><p className="card-copy">{copy.noCorrection}</p><div className="form-actions"><Button className="button-secondary" onClick={playQuestion}>{copy.listen}</Button>{!recording ? <Button disabled={busy || !!attempt} onClick={startRecording}>{copy.record}</Button> : <Button onClick={stopRecording}>{copy.stop}</Button>}</div>{busy && <p className="notice">{copy.processing}</p>}{attempt && <div className="transcript"><strong>{copy.transcript}</strong><p>{attempt.transcript ?? attempt.provider_error}</p><small>{copy.readOnly}</small>{attempt.status === "ANALYZED" ? <Button onClick={next}>{index < 2 ? copy.next : copy.results}</Button> : <Button disabled={busy} onClick={retry}>{copy.retry}</Button>}</div>}{error && <p className="error">{error}</p>}</div>;
}
