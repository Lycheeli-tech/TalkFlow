"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { useInterfaceLocale } from "@/components/interface-locale-provider";
import { CourseCoreAppShell } from "@/components/course-core/app-shell";
import { StageOneEntry } from "@/components/course-core/stage-one-entry";
import { getMessages } from "@/lib/i18n";
import { abandonPractice, completePractice, createPractice, getCurrentPractice, getPractice,
  movePractice, practiceAudio, retryPracticeAnswer, submitPractice,
  type PracticeRun, type PracticeFeedback } from "@/lib/practice-api";
import styles from "./practice-page.module.css";

type Pending = { question: string; blob: Blob; duration: number; key: string };

function Workspace() {
  const { locale } = useInterfaceLocale();
  const copy = getMessages(locale).practiceV2;
  const [run, setRun] = useState<PracticeRun | null>(null);
  const [feedback, setFeedback] = useState<PracticeFeedback | null>(null);
  const [loading, setLoading] = useState(true);
  const [working, setWorking] = useState(false);
  const [recording, setRecording] = useState(false);
  const [requesting, setRequesting] = useState(false);
  const [discard, setDiscard] = useState(false);
  const [elapsed, setElapsed] = useState(0);
  const [error, setError] = useState("");
  const [pendingUpload, setPendingUpload] = useState(false);
  const recorder = useRef<MediaRecorder | null>(null);
  const stream = useRef<MediaStream | null>(null);
  const chunks = useRef<Blob[]>([]);
  const started = useRef(0);
  const pending = useRef<Pending | null>(null);
  const createKey = useRef<{ count: 3 | 5; key: string } | null>(null);
  const audio = useRef<HTMLAudioElement | null>(null);
  const audioUrl = useRef<string | null>(null);
  const generation = useRef(0);
  const active = useRef(false);
  const mounted = useRef(true);
  const busy = working || recording || requesting || loading;
  const recordingGuard = recording || requesting;
  const question = run?.questions[run.current_position];
  const answer = run?.answers.find(item => item.question_id === question?.id);
  const answered = run?.questions.filter(q => run.answers.some(a => a.question_id === q.id && a.status === "SAVED") || run.skipped.includes(q.id)).length ?? 0;

  const stopAudio = useCallback(() => {
    generation.current++; audio.current?.pause(); audio.current = null;
    if (audioUrl.current) URL.revokeObjectURL(audioUrl.current);
    audioUrl.current = null;
  }, []);

  useEffect(() => {
    let cancelled = false;
    getCurrentPractice().then(result => { if (!cancelled) setRun(result); })
      .catch(error => { if (!cancelled) setError(error.message); })
      .finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, []);

  useEffect(() => {
    mounted.current = true;
    return () => { mounted.current = false; active.current = false; stopAudio();
      if (recorder.current?.state === "recording") recorder.current.stop();
      stream.current?.getTracks().forEach(track => track.stop()); };
  }, [stopAudio]);

  useEffect(() => {
    if (!recordingGuard) return;
    const before = (event: BeforeUnloadEvent) => { event.preventDefault(); event.returnValue = ""; };
    window.history.pushState({ ...window.history.state, practiceRecordingGuard: true }, "");
    const back = () => { window.history.pushState({ ...window.history.state, practiceRecordingGuard: true }, ""); setError(copy.leaveBlocked); };
    window.addEventListener("beforeunload", before); window.addEventListener("popstate", back);
    return () => { window.removeEventListener("beforeunload", before); window.removeEventListener("popstate", back);
      if (window.history.state?.practiceRecordingGuard) window.history.back(); };
  }, [recordingGuard, copy.leaveBlocked]);

  useEffect(() => {
    if (!recording) return;
    const timer = window.setInterval(() => setElapsed(Math.round((performance.now() - started.current) / 1000)), 250);
    return () => window.clearInterval(timer);
  }, [recording]);

  async function change(operation: () => Promise<PracticeRun>) {
    stopAudio(); setWorking(true); setError(""); pending.current = null; setPendingUpload(false);
    try { setRun(await operation()); } catch (error) { setError((error as Error).message); }
    finally { setWorking(false); }
  }
  async function start(count: 3 | 5) {
    if (!createKey.current || createKey.current.count !== count) createKey.current = { count, key: crypto.randomUUID() };
    const key = createKey.current.key;
    await change(async () => { const result = await createPractice(count, key); createKey.current = null; setFeedback(null); return result; });
  }
  async function play(answerId?: string) {
    if (!run || active.current) return;
    stopAudio(); const current = generation.current;
    try { const blob = await practiceAudio(run.id, answerId);
      if (current !== generation.current || active.current || !mounted.current) return;
      const url = URL.createObjectURL(blob); audioUrl.current = url;
      const player = new Audio(url); audio.current = player;
      player.addEventListener("ended", stopAudio, { once: true }); await player.play();
    } catch { setError(copy.audioError); }
  }
  async function begin() {
    if (busy || active.current || !run || run.status === "PAUSED") return;
    stopAudio(); active.current = true; setRequesting(true); setError(""); pending.current = null; setPendingUpload(false);
    try {
      const nextStream = await navigator.mediaDevices.getUserMedia({ audio: true });
      if (!mounted.current) { nextStream.getTracks().forEach(track => track.stop()); return; }
      stream.current = nextStream; chunks.current = [];
      const nextRecorder = new MediaRecorder(nextStream); recorder.current = nextRecorder;
      nextRecorder.addEventListener("dataavailable", event => { if (event.data.size) chunks.current.push(event.data); });
      nextRecorder.addEventListener("stop", () => { nextStream.getTracks().forEach(track => track.stop()); stream.current = null; });
      started.current = performance.now(); setElapsed(0); nextRecorder.start(); setRecording(true);
    } catch { active.current = false; stream.current?.getTracks().forEach(track => track.stop()); setError(copy.micError); }
    finally { setRequesting(false); }
  }
  async function upload(item: Pending) {
    if (!run) return;
    setWorking(true); setError("");
    try { const nextRun = await submitPractice(run.id, item.question, item.blob, item.duration, item.key); setRun(nextRun);
      if (nextRun.answers.some(a => a.question_id === item.question && a.status === "SAVED")) { pending.current = null; setPendingUpload(false); }
    } catch (error) { setError((error as Error).message); }
    finally { setWorking(false); }
  }
  function finishRecording() {
    const current = recorder.current; if (!current || !question) return;
    const duration = Math.round(performance.now() - started.current);
    current.addEventListener("stop", () => { active.current = false;
      if (!mounted.current) return;
      const item = { question: question.id, duration, key: crypto.randomUUID(), blob: new Blob(chunks.current, { type: current.mimeType || "audio/webm" }) };
      pending.current = item; setPendingUpload(true); void upload(item); }, { once: true });
    current.stop(); recorder.current = null; setRecording(false); setWorking(true);
  }
  function discardRecording() {
    recorder.current?.stop(); recorder.current = null; active.current = false;
    chunks.current = []; pending.current = null; setRecording(false); setDiscard(false);
  }
  async function end() {
    if (!run) return; stopAudio(); setWorking(true); setError("");
    try { const result = await completePractice(run.id); setFeedback(result); setRun(null); pending.current = null; }
    catch (error) { setError((error as Error).message); try { setRun(await getPractice(run.id)); } catch { setRun(null); } }
    finally { setWorking(false); }
  }
  async function abandon() {
    if (!run) return; setWorking(true); stopAudio();
    try { await abandonPractice(run.id); setRun(null); pending.current = null; setDiscard(false); setError(""); }
    catch (error) { setError((error as Error).message); } finally { setWorking(false); }
  }

  return <CourseCoreAppShell navigationBlocked={busy}><div className={styles.page}>
    <p className={styles.eyebrow}>{copy.eyebrow}</p><h1>{copy.title}</h1>
    <p className={styles.notice}>{copy.description}</p>
    {error && <p role="alert" className={styles.error}>{error}</p>}
    {loading && <p role="status">{copy.loading}</p>}
    {!run && !loading && <>{feedback && <section className={styles.card} aria-label={copy.feedback}>
      <h2>{copy.feedback}</h2><p>{feedback.summary}</p><p className={styles.score}>{feedback.score}/100</p>
      <p className={styles.notice}>{copy.scoreNotice}</p>
      <h3>{copy.strengths}</h3>{feedback.strengths.map((item, i) => <div key={i}><blockquote className={styles.quote}>{item.quote}</blockquote><p>{item.observation}</p></div>)}
      <h3>{copy.improvements}</h3>{feedback.improvements.map((item, i) => <div key={i}><blockquote className={styles.quote}>{item.quote}</blockquote><p>{item.observation}</p></div>)}
      <p className={styles.notice}>{copy.noHistory}</p></section>}
      <section className={styles.card}><h2>{copy.choose}</h2><div className={styles.choices}>
        <button disabled={busy} onClick={() => void start(3)}>{copy.three}</button><button disabled={busy} onClick={() => void start(5)}>{copy.five}</button>
      </div><p className={styles.notice}>{copy.retention}</p></section></>}
    {run && question && <>
      <nav className={styles.questions} aria-label={copy.questions}>{run.questions.map((q, i) => <button key={q.id} disabled={busy || run.status === "PAUSED"}
        aria-pressed={i === run.current_position} onClick={() => void change(() => movePractice(run.id, i))}>
        {i + 1}{run.answers.some(a => a.question_id === q.id && a.status === "SAVED") ? " ✓" : run.skipped.includes(q.id) ? " −" : ""}
      </button>)}</nav>
      <section className={styles.card}><p className={styles.eyebrow}>{copy.question} {run.current_position + 1} / {run.question_count}</p>
        <h2>{question.text}</h2>
        {run.status === "PAUSED" ? <><p>{copy.paused}</p><button disabled={busy} onClick={() => void change(() => movePractice(run.id, run.current_position))}>{copy.resume}</button></> : <>
          {recording ? <><p className={styles.recording} role="status">{copy.recording} · {elapsed}s</p><div className={styles.actions}>
            <button className={styles.primary} onClick={finishRecording}>{copy.stop}</button><button className={styles.danger} onClick={() => setDiscard(true)}>{copy.discard}</button>
          </div></> : <><div className={styles.actions}><button disabled={busy} onClick={() => void play()}>{copy.playQuestion}</button>
            <button className={styles.primary} disabled={busy || answer?.status === "PROCESSING"} onClick={() => void begin()}>{answer ? copy.reanswer : copy.record}</button>
            {answer?.audio_available && <button disabled={busy} onClick={() => void play(answer.id)}>{copy.playAnswer}</button>}</div>
            {answer?.status === "SAVED" && <><h3>{copy.transcript}</h3><p>{answer.transcript}</p><p className={styles.notice}>{copy.saved}</p></>}
            {answer?.status === "FAILED" && <p role="alert" className={styles.error}>{copy.answerFailed}</p>}
            {(answer?.status === "FAILED" || answer?.status === "PROCESSING" || pendingUpload) && <button disabled={busy} onClick={() => pending.current ? void upload(pending.current) : answer && void change(() => retryPracticeAnswer(run.id, answer.id))}>{copy.retry}</button>}
          </>}
          <div className={styles.actions}><button disabled={busy} onClick={() => void change(() => movePractice(run.id, Math.max(0, run.current_position - 1)))}>{copy.previous}</button>
            <button disabled={busy} onClick={() => void change(() => movePractice(run.id, Math.min(run.question_count - 1, run.current_position + 1), false, true))}>{copy.skip}</button>
            <button disabled={busy || run.current_position === run.question_count - 1} onClick={() => void change(() => movePractice(run.id, run.current_position + 1))}>{copy.next}</button>
            <button disabled={busy} onClick={() => void change(() => movePractice(run.id, run.current_position, true))}>{copy.pause}</button></div>
        </>}
      </section>
      <div className={styles.actions}><button className={styles.primary} disabled={busy || answered !== run.question_count || !run.answers.some(a => a.status === "SAVED")}
        onClick={() => void end()}>{copy.end}</button><button className={styles.danger} disabled={busy} onClick={() => setDiscard(true)}>{copy.abandon}</button></div>
      <p className={styles.notice}>{copy.expires} {new Date(run.expires_at).toLocaleString(locale)}</p>
    </>}
    {(working || requesting) && <p role="status">{requesting ? copy.requesting : copy.processing}</p>}
    {discard && <section className={styles.card} role="alert"><p>{recording ? copy.discardConfirm : copy.abandonConfirm}</p>
      <div className={styles.actions}><button onClick={() => recording ? discardRecording() : void abandon()}>{copy.confirm}</button><button onClick={() => setDiscard(false)}>{copy.cancel}</button></div></section>}
  </div></CourseCoreAppShell>;
}

export function PracticeV2Page() { return <StageOneEntry><Workspace /></StageOneEntry>; }
