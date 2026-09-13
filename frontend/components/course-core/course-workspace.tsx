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
  confirmCourseDraft,
  discardCourseDraft,
  getCourseDrafts,
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
  | "RECORDING_CHINESE"
  | "PROCESSING_CHINESE"
  | "AWAITING_CHINESE_CONFIRMATION"
  | "ANSWER_SAVED"
  | "RECOVERABLE_FAILURE";

type PendingSubmission = {
  blob: Blob;
  durationMs: number;
  idempotencyKey: string;
  language: "ENGLISH" | "CHINESE";
};

type AuxiliaryPanel = "NONE" | "HINTS" | "EXPRESSION_MATERIALS" | "REFERENCE_ANSWER" | "FEEDBACK" | "HISTORY" | "CHINESE_GUIDE";

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
  const [feedbackAnswer, setFeedbackAnswer] = useState<CourseAnswer | null>(null);
  const [drafts, setDrafts] = useState<Record<string, CourseAnswer[]>>({});
  const [restoring, setRestoring] = useState(true);
  const [requestingMicrophone, setRequestingMicrophone] = useState(false);
  const [error, setError] = useState("");
  const [elapsedMs, setElapsedMs] = useState(0);
  const recorderRef = useRef<MediaRecorder | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const recordingStartedRef = useRef(0);
  const pendingRef = useRef<PendingSubmission | null>(null);
  const recordingLanguageRef = useRef<"ENGLISH" | "CHINESE">("ENGLISH");
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const audioUrlRef = useRef<string | null>(null);

  const recording = state === "RECORDING_ENGLISH" || state === "RECORDING_CHINESE";
  const processing = state === "PROCESSING_ENGLISH" || state === "PROCESSING_CHINESE";
  const busy = recording || processing || restoring || requestingMicrophone;
  const audioGenerationRef = useRef(0);
  const recordingActiveRef = useRef(false);
  const mountedRef = useRef(true);
  const selectedHistory = history[question.id] ?? [];

  const stopAudio = useCallback(() => {
    audioGenerationRef.current += 1;
    audioRef.current?.pause();
    audioRef.current = null;
    window.speechSynthesis?.cancel();
    if (audioUrlRef.current) URL.revokeObjectURL(audioUrlRef.current);
    audioUrlRef.current = null;
  }, []);

  const playBlob = useCallback(
    async (load: () => Promise<Blob>) => {
      if (recordingActiveRef.current) return;
      stopAudio();
      const generation = audioGenerationRef.current;
      try {
        const blob = await load();
        if (recordingActiveRef.current || generation !== audioGenerationRef.current) return;
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
    let cancelled = false;
    void Promise.all(questions.map(async (item) => [item.id,
      (await getCourseDrafts(getStoredAccessToken(), course.id, item.id)).answers] as const))
      .then((entries) => {
        if (cancelled) return;
        setDrafts(Object.fromEntries(entries));
      })
      .catch(() => { if (!cancelled) setError(copy.draftRestoreError); })
      .finally(() => { if (!cancelled) setRestoring(false); });
    return () => { cancelled = true; };
  }, [copy.draftRestoreError, course.id, questions]);

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
      setElapsedMs(performance.now() - recordingStartedRef.current);
    }, 250);
    return () => window.clearInterval(timer);
  }, [recording]);

  useEffect(
    () => {
      mountedRef.current = true;
      return () => {
        mountedRef.current = false;
        stopAudio();
        streamRef.current?.getTracks().forEach((track) => track.stop());
      };
    },
    [stopAudio],
  );

  async function beginRecording(language: "ENGLISH" | "CHINESE" = "ENGLISH") {
    if (busy || recordingActiveRef.current) return;
    setRequestingMicrophone(true);
    recordingActiveRef.current = true;
    setError("");
    stopAudio();
    let stream: MediaStream | null = null;
    try {
      const acquiredStream = await navigator.mediaDevices.getUserMedia({ audio: true });
      if (!mountedRef.current) {
        acquiredStream.getTracks().forEach((track) => track.stop());
        return;
      }
      stream = acquiredStream;
      const recorder = new MediaRecorder(acquiredStream);
      recorderRef.current = recorder;
      streamRef.current = acquiredStream;
      chunksRef.current = [];
      pendingRef.current = null;
      recordingLanguageRef.current = language;
      recordingActiveRef.current = true;
      setAnswer(null);
      recorder.addEventListener("dataavailable", (event) => {
        if (event.data.size > 0) chunksRef.current.push(event.data);
      });
      recorder.addEventListener("stop", () => {
        acquiredStream.getTracks().forEach((track) => track.stop());
        streamRef.current = null;
      });
      recorder.addEventListener("start", (event) => {
        recordingStartedRef.current = event.timeStamp;
      }, { once: true });
      setElapsedMs(0);
      recorder.start();
      setState(language === "CHINESE" ? "RECORDING_CHINESE" : "RECORDING_ENGLISH");
    } catch {
      stream?.getTracks().forEach((track) => track.stop());
      recordingActiveRef.current = false;
      setError(copy.micError);
    } finally {
      setRequestingMicrophone(false);
    }
  }

  function discardRecording() {
    if (!window.confirm(copy.discardConfirm)) return;
    const recorder = recorderRef.current;
    recorderRef.current = null;
    if (recorder && recorder.state !== "inactive") recorder.stop();
    chunksRef.current = [];
    recordingActiveRef.current = false;
    pendingRef.current = null;
    setElapsedMs(0);
    setState("PREPARING");
  }

  function finishRecording(event: React.MouseEvent<HTMLButtonElement>) {
    const recorder = recorderRef.current;
    if (!recorder || recorder.state === "inactive") return;
    const durationMs = Math.max(0, Math.round(event.timeStamp - recordingStartedRef.current));
    recorder.addEventListener(
      "stop",
      () => {
        const blob = new Blob(chunksRef.current, {
          type: recorder.mimeType || "audio/webm",
        });
        recordingActiveRef.current = false;
        const pending = { blob, durationMs, idempotencyKey: crypto.randomUUID(), language: recordingLanguageRef.current };
        pendingRef.current = pending;
        void submitPending(pending);
      },
      { once: true },
    );
    recorder.stop();
    recorderRef.current = null;
    setState(recordingLanguageRef.current === "CHINESE" ? "PROCESSING_CHINESE" : "PROCESSING_ENGLISH");
  }

  async function submitPending(pending: PendingSubmission) {
    setError("");
    setState(pending.language === "CHINESE" ? "PROCESSING_CHINESE" : "PROCESSING_ENGLISH");
    try {
      const result = await submitCourseAnswer(
        getStoredAccessToken(),
        course.id,
        question.id,
        pending.blob,
        pending.durationMs,
        pending.idempotencyKey,
        pending.language,
      );
      settleResult(result);
    } catch {
      setError(copy.uploadError);
      setState("RECOVERABLE_FAILURE");
    }
  }

  function settleResult(result: CourseAnswer) {
    setAnswer(result);
    setDrafts((current) => ({ ...current, [result.question_id]: [
      ...(result.answer_language === "CHINESE" && result.status !== "SAVED" ? [result] : []),
      ...(current[result.question_id] ?? []).filter((item) => item.id !== result.id),
    ] }));
    if (result.status === "SAVED") {
      pendingRef.current = null;
      setState("ANSWER_SAVED");
      void loadHistory(question.id);
    } else if (result.status === "AWAITING_CONFIRMATION") {
      pendingRef.current = null;
      setState("AWAITING_CHINESE_CONFIRMATION");
    } else {
      setError(copy.failure);
      setState("RECOVERABLE_FAILURE");
    }
  }

  async function retry() {
    setError("");
    setState((answer?.answer_language ?? pendingRef.current?.language) === "CHINESE" ? "PROCESSING_CHINESE" : "PROCESSING_ENGLISH");
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
            pendingRef.current!.language,
          );
      settleResult(result);
    } catch {
      setError(copy.uploadError);
      setState("RECOVERABLE_FAILURE");
    }
  }

  function chooseQuestion(nextQuestion: CourseQuestion) {
    if (busy) {
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

  async function openSupport(panel: Exclude<AuxiliaryPanel, "NONE" | "FEEDBACK" | "HISTORY" | "CHINESE_GUIDE">) {
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
    setFeedbackAnswer(item);
    setAuxiliaryPanel("FEEDBACK");
    setSupportError("");
  }

  async function retryFeedback() {
    if (!feedbackAnswer) return;
    setSupportLoading(true);
    setSupportError("");
    try {
      const updated = await retryCourseFeedback(getStoredAccessToken(), feedbackAnswer.id);
      setFeedbackAnswer(updated);
      await loadHistory(question.id);
    } catch {
      setSupportError(copy.feedbackError);
    } finally {
      setSupportLoading(false);
    }
  }

  function playReferenceAnswer() {
    if (!referenceAnswer || recording || recordingActiveRef.current) return;
    stopAudio();
    const utterance = new SpeechSynthesisUtterance(referenceAnswer.answer);
    utterance.lang = "en-US";
    window.speechSynthesis.speak(utterance);
  }

  async function confirmDraft() {
    if (!answer || busy) return;
    setError("");
    setState("PROCESSING_CHINESE");
    try { settleResult(await confirmCourseDraft(getStoredAccessToken(), answer.id)); }
    catch { setError(copy.confirmDraftError); setState("AWAITING_CHINESE_CONFIRMATION"); }
  }

  async function abandonDraft(reanswer = false) {
    if (!answer || busy || !window.confirm(copy.discardDraftConfirm)) return;
    try {
      await discardCourseDraft(getStoredAccessToken(), answer.id);
      setDrafts((current) => ({ ...current, [answer.question_id]:
        (current[answer.question_id] ?? []).filter((item) => item.id !== answer.id) }));
      resetAnswer();
      if (reanswer) setAuxiliaryPanel("CHINESE_GUIDE");
    } catch { setError(copy.discardDraftError); }
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
              disabled={busy}
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
              <button disabled={busy} className={styles.primaryButton} type="button" onClick={() => void beginRecording()}>
                {copy.startAnswer}
              </button>
              <button disabled={busy} className={styles.secondaryButton} type="button" onClick={() => setAuxiliaryPanel("CHINESE_GUIDE")}>
                {copy.answerInChinese}
              </button>
            </div>
          )}

          {state === "PREPARING" && (drafts[question.id] ?? []).map((draft) => (
            <div className={styles.failurePanel} key={draft.id}>
              <p>{copy.recoverDraft}</p>
              <button type="button" disabled={busy} onClick={() => settleResult(draft)}>{copy.resumeDraft}</button>
            </div>
          ))}

          {state === "AWAITING_CHINESE_CONFIRMATION" && answer?.transcript && (
            <section className={styles.savedPanel}>
              <p>{copy.draftNotSaved}</p>
              <div className={styles.transcript}><strong>{copy.chineseTranscript}</strong><p>{answer.transcript.transcript}</p></div>
              <div className={styles.transcript}><strong>{copy.organizedEnglish}</strong><p>{answer.transcript.organized_english}</p></div>
              <p>{copy.confirmDraftHelp}</p>
              <div className={styles.answerActions}>
                <button className={styles.primaryButton} type="button" onClick={() => void confirmDraft()}>{copy.confirmDraft}</button>
                <button type="button" onClick={() => void abandonDraft()}>{copy.discard}</button>
                <button type="button" onClick={() => void abandonDraft(true)}>{copy.answerAgain}</button>
              </div>
            </section>
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

          {processing && (
            <p className={styles.processing} role="status">
              {state === "PROCESSING_CHINESE" ? copy.processingChinese : copy.processing}
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
                <button className={styles.secondaryButton} type="button" onClick={() => answer?.answer_language === "CHINESE" ? void abandonDraft(true) : resetAnswer()}>
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
                  {answer.transcript.organized_english && <><strong>{copy.organizedEnglish}</strong><p>{answer.transcript.organized_english}</p></>}
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
                {auxiliaryPanel === "CHINESE_GUIDE" && copy.answerInChinese}
              </h2>
              <button type="button" onClick={() => setAuxiliaryPanel("NONE")}>
                {copy.close}
              </button>
            </div>

            {supportLoading && <p className={styles.processing}>{copy.generating}</p>}
            {supportError && <p className={styles.error}>{supportError}</p>}

            {auxiliaryPanel === "CHINESE_GUIDE" && (
              <div className={styles.supportContent}>
                <p>{copy.chineseGuide}</p>
                <button disabled={busy || state !== "PREPARING"} type="button" onClick={() => void beginRecording("CHINESE")}>{copy.startChineseAnswer}</button>
              </div>
            )}

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

            {auxiliaryPanel === "FEEDBACK" && feedbackAnswer && !supportLoading && (
              <div className={styles.supportContent}>
                {feedbackAnswer.feedback?.status === "READY" ? (
                  <>
                    <p className={styles.feedbackSummary}>{feedbackAnswer.feedback.summary}</p>
                    {(feedbackAnswer.feedback.priority_changes ?? []).map((change, index) => (
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
                    <p>{feedbackAnswer.feedback?.status === "PENDING" ? copy.feedbackPending : copy.feedbackFailed}</p>
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
                    {item.transcript?.organized_english && <><strong>{copy.organizedEnglish}</strong><p>{item.transcript.organized_english}</p></>}
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
