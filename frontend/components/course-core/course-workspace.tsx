"use client";

import Link from "next/link";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import { useInterfaceLocale } from "@/components/interface-locale-provider";
import { getStoredAccessToken } from "@/lib/auth-session";
import {
  CourseAnswer,
  CourseCatalogItem,
  CourseQuestion,
  getCourseAnswerAudio,
  getCourseHistory,
  getQuestionAudio,
  retryCourseAnswer,
  submitCourseAnswer,
} from "@/lib/course-api";
import { getMessages } from "@/lib/i18n";

import { CourseCoreAppShell } from "./app-shell";
import styles from "./course-core.module.css";

type WorkspaceState =
  | "PREPARING"
  | "RECORDING_ENGLISH"
  | "PROCESSING_ENGLISH"
  | "ANSWER_SAVED"
  | "RECOVERABLE_FAILURE";

type PendingSubmission = {
  blob: Blob;
  durationMs: number;
  idempotencyKey: string;
};

function formatDuration(durationMs: number | null): string {
  if (durationMs === null) return "—";
  const seconds = Math.max(0, Math.round(durationMs / 1000));
  return `${Math.floor(seconds / 60)}:${String(seconds % 60).padStart(2, "0")}`;
}

export function CourseWorkspace({ course }: { course: CourseCatalogItem }) {
  const { locale } = useInterfaceLocale();
  const copy = getMessages(locale).courseCore;
  const questions = useMemo(
    () => [course.core_question, course.follow_up_question].filter(Boolean) as CourseQuestion[],
    [course],
  );
  const [question, setQuestion] = useState(questions[0]);
  const [state, setState] = useState<WorkspaceState>("PREPARING");
  const [history, setHistory] = useState<Record<string, CourseAnswer[]>>({});
  const [historyOpen, setHistoryOpen] = useState(false);
  const [questionsOpen, setQuestionsOpen] = useState(false);
  const [answer, setAnswer] = useState<CourseAnswer | null>(null);
  const [error, setError] = useState("");
  const [elapsedMs, setElapsedMs] = useState(0);
  const recorderRef = useRef<MediaRecorder | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const recordingStartedRef = useRef(0);
  const pendingRef = useRef<PendingSubmission | null>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const audioUrlRef = useRef<string | null>(null);

  const recording = state === "RECORDING_ENGLISH";
  const processing = state === "PROCESSING_ENGLISH";
  const selectedHistory = history[question.id] ?? [];

  const stopAudio = useCallback(() => {
    audioRef.current?.pause();
    audioRef.current = null;
    if (audioUrlRef.current) URL.revokeObjectURL(audioUrlRef.current);
    audioUrlRef.current = null;
  }, []);

  const playBlob = useCallback(
    async (load: () => Promise<Blob>) => {
      stopAudio();
      try {
        const blob = await load();
        const url = URL.createObjectURL(blob);
        const nextAudio = new Audio(url);
        audioUrlRef.current = url;
        audioRef.current = nextAudio;
        nextAudio.addEventListener("ended", stopAudio, { once: true });
        await nextAudio.play();
      } catch {
        setError(copy.ttsError);
      }
    },
    [copy.ttsError, stopAudio],
  );

  const loadHistory = useCallback(
    async (questionId: string) => {
      try {
        const result = await getCourseHistory(getStoredAccessToken(), course.id, questionId);
        setHistory((current) => ({ ...current, [questionId]: result.answers }));
      } catch {
        setError(copy.historyError);
      }
    },
    [copy.historyError, course.id],
  );

  useEffect(() => {
    const token = getStoredAccessToken();
    void Promise.all(
      questions.map(async (item) => [item.id, (await getCourseHistory(token, course.id, item.id)).answers] as const),
    )
      .then((entries) => setHistory(Object.fromEntries(entries)))
      .catch(() => setError(copy.historyError));
  }, [copy.historyError, course.id, questions]);

  useEffect(() => {
    if (!recording) return;
    const preventUnload = (event: BeforeUnloadEvent) => {
      event.preventDefault();
    };
    const preventBack = () => {
      window.history.pushState({ courseRecordingGuard: true }, "", window.location.href);
      window.alert(copy.leaveBlocked);
    };
    window.history.pushState({ courseRecordingGuard: true }, "", window.location.href);
    window.addEventListener("beforeunload", preventUnload);
    window.addEventListener("popstate", preventBack);
    return () => {
      window.removeEventListener("beforeunload", preventUnload);
      window.removeEventListener("popstate", preventBack);
      if (window.history.state?.courseRecordingGuard) window.history.back();
    };
  }, [copy.leaveBlocked, recording]);

  useEffect(() => {
    if (!recording) return;
    const timer = window.setInterval(() => {
      setElapsedMs(Date.now() - recordingStartedRef.current);
    }, 250);
    return () => window.clearInterval(timer);
  }, [recording]);

  useEffect(
    () => () => {
      stopAudio();
      streamRef.current?.getTracks().forEach((track) => track.stop());
    },
    [stopAudio],
  );

  async function beginRecording() {
    setError("");
    stopAudio();
    let stream: MediaStream | null = null;
    try {
      const acquiredStream = await navigator.mediaDevices.getUserMedia({ audio: true });
      stream = acquiredStream;
      const recorder = new MediaRecorder(acquiredStream);
      recorderRef.current = recorder;
      streamRef.current = acquiredStream;
      chunksRef.current = [];
      pendingRef.current = null;
      setAnswer(null);
      recorder.addEventListener("dataavailable", (event) => {
        if (event.data.size > 0) chunksRef.current.push(event.data);
      });
      recorder.addEventListener("stop", () => {
        acquiredStream.getTracks().forEach((track) => track.stop());
        streamRef.current = null;
      });
      recordingStartedRef.current = Date.now();
      setElapsedMs(0);
      recorder.start();
      setState("RECORDING_ENGLISH");
    } catch {
      stream?.getTracks().forEach((track) => track.stop());
      setError(copy.micError);
    }
  }

  function discardRecording() {
    if (!window.confirm(copy.discardConfirm)) return;
    const recorder = recorderRef.current;
    recorderRef.current = null;
    if (recorder && recorder.state !== "inactive") recorder.stop();
    chunksRef.current = [];
    pendingRef.current = null;
    setElapsedMs(0);
    setState("PREPARING");
  }

  function finishRecording() {
    const recorder = recorderRef.current;
    if (!recorder || recorder.state === "inactive") return;
    const durationMs = Date.now() - recordingStartedRef.current;
    recorder.addEventListener(
      "stop",
      () => {
        const blob = new Blob(chunksRef.current, {
          type: recorder.mimeType || "audio/webm",
        });
        const pending = { blob, durationMs, idempotencyKey: crypto.randomUUID() };
        pendingRef.current = pending;
        void submitPending(pending);
      },
      { once: true },
    );
    recorder.stop();
    recorderRef.current = null;
    setState("PROCESSING_ENGLISH");
  }

  async function submitPending(pending: PendingSubmission) {
    setError("");
    setState("PROCESSING_ENGLISH");
    try {
      const result = await submitCourseAnswer(
        getStoredAccessToken(),
        course.id,
        question.id,
        pending.blob,
        pending.durationMs,
        pending.idempotencyKey,
      );
      settleResult(result);
    } catch {
      setError(copy.uploadError);
      setState("RECOVERABLE_FAILURE");
    }
  }

  function settleResult(result: CourseAnswer) {
    setAnswer(result);
    if (result.status === "SAVED") {
      pendingRef.current = null;
      setState("ANSWER_SAVED");
      void loadHistory(question.id);
    } else {
      setError(copy.failure);
      setState("RECOVERABLE_FAILURE");
    }
  }

  async function retry() {
    setError("");
    setState("PROCESSING_ENGLISH");
    try {
      const result = answer
        ? await retryCourseAnswer(getStoredAccessToken(), answer.id)
        : await submitCourseAnswer(
            getStoredAccessToken(),
            course.id,
            question.id,
            pendingRef.current!.blob,
            pendingRef.current!.durationMs,
            pendingRef.current!.idempotencyKey,
          );
      settleResult(result);
    } catch {
      setError(copy.uploadError);
      setState("RECOVERABLE_FAILURE");
    }
  }

  function chooseQuestion(nextQuestion: CourseQuestion) {
    if (recording) {
      setError(copy.leaveBlocked);
      return;
    }
    stopAudio();
    setQuestion(nextQuestion);
    setAnswer(null);
    setError("");
    setState("PREPARING");
    setQuestionsOpen(false);
  }

  function resetAnswer() {
    pendingRef.current = null;
    setAnswer(null);
    setError("");
    setState("PREPARING");
  }

  return (
    <CourseCoreAppShell navigationBlocked={recording}>
      <div className={styles.workspaceToolbar}>
        {recording ? (
          <span className={styles.blockedBack} aria-disabled="true">
            ← {copy.backToCourses}
          </span>
        ) : (
          <Link className={styles.backLink} href="/courses">
            ← {copy.backToCourses}
          </Link>
        )}
        <button type="button" onClick={() => setQuestionsOpen(true)}>
          {copy.openQuestions}
        </button>
        <button type="button" onClick={() => setHistoryOpen(true)}>
          {copy.history} · {selectedHistory.length}
        </button>
      </div>

      <div className={styles.courseWorkspace}>
        <aside className={`${styles.questionRail} ${questionsOpen ? styles.drawerOpen : ""}`}>
          <div className={styles.drawerHeading}>
            <h2>{copy.questions}</h2>
            <button type="button" onClick={() => setQuestionsOpen(false)}>
              {copy.closeQuestions}
            </button>
          </div>
          {questions.map((item) => (
            <button
              className={item.id === question.id ? styles.selectedQuestion : ""}
              disabled={recording || processing}
              key={item.id}
              type="button"
              onClick={() => chooseQuestion(item)}
            >
              <span>{item.kind === "CORE" ? copy.coreQuestion : copy.followUpQuestion}</span>
              <strong>{item.text}</strong>
              <small>
                {(history[item.id] ?? []).length} {copy.historyCount}
              </small>
            </button>
          ))}
        </aside>

        <article className={styles.answerPanel}>
          <p className={styles.eyebrow}>{copy.answerStageEyebrow}</p>
          <h1>{locale === "zh-CN" ? course.name_zh_cn : course.name_en}</h1>
          <p className={styles.questionKind}>
            {question.kind === "CORE" ? copy.coreQuestion : copy.followUpQuestion}
          </p>
          <h2 className={styles.activeQuestion}>{question.text}</h2>

          {state === "PREPARING" && (
            <div className={styles.answerActions}>
              <button
                className={styles.secondaryButton}
                type="button"
                onClick={() =>
                  void playBlob(() =>
                    getQuestionAudio(getStoredAccessToken(), course.id, question.id),
                  )
                }
              >
                {copy.listen}
              </button>
              <button className={styles.primaryButton} type="button" onClick={beginRecording}>
                {copy.startAnswer}
              </button>
              <button className={styles.disabledButton} disabled type="button">
                {copy.answerInChinese} · {copy.stage6Unavailable}
              </button>
            </div>
          )}

          {recording && (
            <div className={styles.recordingPanel} role="status">
              <span className={styles.recordingDot} />
              <strong>{copy.recording}</strong>
              <time>{formatDuration(elapsedMs)}</time>
              <div>
                <button className={styles.secondaryButton} type="button" onClick={discardRecording}>
                  {copy.discard}
                </button>
                <button className={styles.primaryButton} type="button" onClick={finishRecording}>
                  {copy.finish}
                </button>
              </div>
            </div>
          )}

          {state === "PROCESSING_ENGLISH" && (
            <p className={styles.processing} role="status">
              {copy.processing}
            </p>
          )}

          {state === "RECOVERABLE_FAILURE" && (
            <div className={styles.failurePanel}>
              <p role="alert">{error || copy.failure}</p>
              {answer?.audio_available && <small>{copy.failureExpires}</small>}
              <div className={styles.answerActions}>
                {(!answer || answer.audio_available) && (
                  <button className={styles.primaryButton} type="button" onClick={retry}>
                    {copy.retry}
                  </button>
                )}
                <button className={styles.secondaryButton} type="button" onClick={resetAnswer}>
                  {copy.answerAgain}
                </button>
              </div>
            </div>
          )}

          {state === "ANSWER_SAVED" && answer && (
            <div className={styles.savedPanel}>
              <p className={styles.savedLabel}>{copy.saved}</p>
              <p>
                {copy.duration}: {formatDuration(answer.response_duration_ms)}
              </p>
              {answer.transcript && (
                <section className={styles.transcript}>
                  <span>{copy.readOnlyTranscript}</span>
                  <p>{answer.transcript.transcript}</p>
                </section>
              )}
              <section className={styles.feedbackNotice}>
                <strong>{copy.feedback}</strong>
                <p>{copy.feedbackStage5}</p>
              </section>
              <div className={styles.answerActions}>
                <button className={styles.secondaryButton} type="button" onClick={resetAnswer}>
                  {copy.returnQuestion}
                </button>
                <button className={styles.primaryButton} type="button" onClick={resetAnswer}>
                  {copy.answerAgain}
                </button>
              </div>
            </div>
          )}

          {error && state !== "RECOVERABLE_FAILURE" && (
            <p className={styles.error} role="alert">
              {error}
            </p>
          )}
        </article>
      </div>

      {historyOpen && (
        <div className={styles.drawerBackdrop} onClick={() => setHistoryOpen(false)}>
          <aside
            className={styles.historyDrawer}
            aria-label={copy.history}
            onClick={(event) => event.stopPropagation()}
          >
            <div className={styles.drawerHeading}>
              <h2>{copy.history}</h2>
              <button type="button" onClick={() => setHistoryOpen(false)}>
                {copy.close}
              </button>
            </div>
            {selectedHistory.length === 0 && <p>{copy.noHistory}</p>}
            {selectedHistory.map((item) => (
              <article className={styles.historyItem} key={item.id}>
                <time>{item.saved_at ? new Date(item.saved_at).toLocaleString(locale) : ""}</time>
                <p>{item.transcript?.transcript}</p>
                <small>
                  {copy.duration}: {formatDuration(item.response_duration_ms)}
                </small>
                {item.audio_available ? (
                  <button
                    disabled={recording}
                    type="button"
                    onClick={() =>
                      void playBlob(() => getCourseAnswerAudio(getStoredAccessToken(), item.id))
                    }
                  >
                    {copy.playAnswer}
                  </button>
                ) : (
                  <span>{copy.audioExpired}</span>
                )}
              </article>
            ))}
          </aside>
        </div>
      )}
    </CourseCoreAppShell>
  );
}
