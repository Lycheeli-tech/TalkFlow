"use client";

import Link from "next/link";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import { useInterfaceLocale } from "@/components/interface-locale-provider";
import { getStoredAccessToken } from "@/lib/auth-session";
import {
  CourseAnswer,
  CourseExpressionMaterials,
  CourseHints,
  CourseReferenceAnswer,
  deleteCourseAnswer,
  CourseCatalogItem,
  CourseQuestion,
  generateCourseExpressionMaterials,
  generateCourseHints,
  generateCourseReferenceAnswer,
  getCourseAnswerAudio,
  getCourseHistory,
  getQuestionAudio,
  retryCourseAnswer,
  retryCourseFeedback,
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

type AuxiliaryPanel = "NONE" | "HINTS" | "EXPRESSION_MATERIALS" | "REFERENCE_ANSWER" | "FEEDBACK" | "HISTORY";

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
  const [auxiliaryPanel, setAuxiliaryPanel] = useState<AuxiliaryPanel>("NONE");
  const [questionsOpen, setQuestionsOpen] = useState(false);
  const [hints, setHints] = useState<CourseHints | null>(null);
  const [materials, setMaterials] = useState<CourseExpressionMaterials | null>(null);
  const [referenceAnswer, setReferenceAnswer] = useState<CourseReferenceAnswer | null>(null);
  const [supportLoading, setSupportLoading] = useState(false);
  const [supportError, setSupportError] = useState("");
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
    window.speechSynthesis?.cancel();
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
    setAuxiliaryPanel("NONE");
    setHints(null);
    setMaterials(null);
    setReferenceAnswer(null);
    setSupportError("");
    setQuestionsOpen(false);
  }

  function resetAnswer() {
    pendingRef.current = null;
    setAnswer(null);
    setError("");
    setState("PREPARING");
  }

  async function removeAnswer(answerId: string) {
    if (!window.confirm(copy.deleteAnswerConfirm)) return;
    setError("");
    try {
      await deleteCourseAnswer(getStoredAccessToken(), answerId);
      stopAudio();
      if (answer?.id === answerId) resetAnswer();
      await loadHistory(question.id);
    } catch {
      setError(copy.deleteAnswerError);
    }
  }

  async function openSupport(panel: Exclude<AuxiliaryPanel, "NONE" | "FEEDBACK" | "HISTORY">) {
    setAuxiliaryPanel(panel);
    setSupportError("");
    const token = getStoredAccessToken();
    if (
      (panel === "HINTS" && hints) ||
      (panel === "EXPRESSION_MATERIALS" && materials) ||
      (panel === "REFERENCE_ANSWER" && referenceAnswer)
    ) return;
    setSupportLoading(true);
    try {
      if (panel === "HINTS") setHints(await generateCourseHints(token, course.id, question.id));
      if (panel === "EXPRESSION_MATERIALS") {
        setMaterials(await generateCourseExpressionMaterials(token, course.id, question.id));
      }
      if (panel === "REFERENCE_ANSWER") {
        setReferenceAnswer(await generateCourseReferenceAnswer(token, course.id, question.id));
      }
    } catch {
      setSupportError(copy.supportError);
    } finally {
      setSupportLoading(false);
    }
  }

  function openFeedback(item: CourseAnswer) {
    setAnswer(item);
    setAuxiliaryPanel("FEEDBACK");
    setSupportError("");
  }

  async function retryFeedback() {
    if (!answer) return;
    setSupportLoading(true);
    setSupportError("");
    try {
      const updated = await retryCourseFeedback(getStoredAccessToken(), answer.id);
      setAnswer(updated);
      await loadHistory(question.id);
    } catch {
      setSupportError(copy.feedbackError);
    } finally {
      setSupportLoading(false);
    }
  }

  function playReferenceAnswer() {
    if (!referenceAnswer || recording) return;
    stopAudio();
    const utterance = new SpeechSynthesisUtterance(referenceAnswer.answer);
    utterance.lang = "en-US";
    window.speechSynthesis.speak(utterance);
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
        <button type="button" onClick={() => setAuxiliaryPanel("HISTORY")}>
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

          <div className={styles.supportActions} aria-label={copy.aiSupport}>
            <button type="button" onClick={() => void openSupport("HINTS")}>
              {copy.hints}
            </button>
            <button type="button" onClick={() => void openSupport("EXPRESSION_MATERIALS")}>
              {copy.expressionMaterials}
            </button>
            <button type="button" onClick={() => void openSupport("REFERENCE_ANSWER")}>
              {copy.referenceAnswer}
            </button>
          </div>

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
              <button
                className={styles.feedbackButton}
                type="button"
                onClick={() => openFeedback(answer)}
              >
                {answer.feedback?.status === "READY" ? copy.viewFeedback : copy.feedback}
              </button>
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

        {auxiliaryPanel !== "NONE" && (
          <aside className={styles.auxiliaryPanel} aria-label={copy.aiSupport}>
            <div className={styles.drawerHeading}>
              <h2>
                {auxiliaryPanel === "HINTS" && copy.hints}
                {auxiliaryPanel === "EXPRESSION_MATERIALS" && copy.expressionMaterials}
                {auxiliaryPanel === "REFERENCE_ANSWER" && copy.referenceAnswer}
                {auxiliaryPanel === "FEEDBACK" && copy.feedback}
                {auxiliaryPanel === "HISTORY" && copy.history}
              </h2>
              <button type="button" onClick={() => setAuxiliaryPanel("NONE")}>
                {copy.close}
              </button>
            </div>

            {supportLoading && <p className={styles.processing}>{copy.generating}</p>}
            {supportError && <p className={styles.error}>{supportError}</p>}

            {auxiliaryPanel === "HINTS" && hints && !supportLoading && (
              <div className={styles.supportContent}>
                <section>
                  <strong>{copy.answerFocus}</strong>
                  <p>{hints.static_answer_focus}</p>
                </section>
                <section><strong>{copy.keywords}</strong><ul>{hints.keywords.map((item) => <li key={item}>{item}</li>)}</ul></section>
                <section><strong>{copy.phrases}</strong><ul>{hints.phrases.map((item) => <li key={item}>{item}</li>)}</ul></section>
                <section><strong>{copy.sentenceFrames}</strong><ul>{hints.sentence_frames.map((item) => <li key={item}>{item}</li>)}</ul></section>
                {hints.personalization_note && <small>{hints.personalization_note}</small>}
              </div>
            )}

            {auxiliaryPanel === "EXPRESSION_MATERIALS" && materials && !supportLoading && (
              <div className={styles.supportContent}>
                {materials.materials.map((item, index) => (
                  <section key={`${item.kind}-${index}`}>
                    <small>{copy.materialKinds[item.kind]}</small>
                    <p>{item.text}</p>
                  </section>
                ))}
                {materials.personalization_note && <small>{materials.personalization_note}</small>}
              </div>
            )}

            {auxiliaryPanel === "REFERENCE_ANSWER" && referenceAnswer && !supportLoading && (
              <div className={styles.supportContent}>
                <p>{referenceAnswer.answer}</p>
                <button disabled={recording} type="button" onClick={playReferenceAnswer}>
                  {copy.playReference}
                </button>
                {referenceAnswer.personalization_note && <small>{referenceAnswer.personalization_note}</small>}
              </div>
            )}

            {auxiliaryPanel === "FEEDBACK" && answer && !supportLoading && (
              <div className={styles.supportContent}>
                {answer.feedback?.status === "READY" ? (
                  <>
                    <p className={styles.feedbackSummary}>{answer.feedback.summary}</p>
                    {(answer.feedback.priority_changes ?? []).map((change, index) => (
                      <section key={index}>
                        <strong>{copy.originalQuote}</strong>
                        <blockquote>{String(change.original_quote ?? "")}</blockquote>
                        <strong>{copy.suggestion}</strong>
                        <p>{String(change.suggestion ?? "")}</p>
                      </section>
                    ))}
                  </>
                ) : (
                  <div>
                    <p>{answer.feedback?.status === "PENDING" ? copy.feedbackPending : copy.feedbackFailed}</p>
                    <button type="button" onClick={() => void retryFeedback()}>{copy.retryFeedback}</button>
                  </div>
                )}
              </div>
            )}

            {auxiliaryPanel === "HISTORY" && (
              <div>
                {selectedHistory.length === 0 && <p>{copy.noHistory}</p>}
                {selectedHistory.map((item) => (
                  <article className={styles.historyItem} key={item.id}>
                    <time>{item.saved_at ? new Date(item.saved_at).toLocaleString(locale) : ""}</time>
                    <p>{item.transcript?.transcript}</p>
                    <small>{copy.duration}: {formatDuration(item.response_duration_ms)}</small>
                    {item.audio_available ? (
                      <button disabled={recording} type="button" onClick={() => void playBlob(() => getCourseAnswerAudio(getStoredAccessToken(), item.id))}>{copy.playAnswer}</button>
                    ) : <span>{copy.audioExpired}</span>}
                    <button type="button" onClick={() => openFeedback(item)}>{copy.viewFeedback}</button>
                    <button className={styles.dangerButton} disabled={recording} type="button" onClick={() => void removeAnswer(item.id)}>{copy.deleteAnswer}</button>
                  </article>
                ))}
              </div>
            )}
          </aside>
        )}
      </div>
    </CourseCoreAppShell>
  );
}
