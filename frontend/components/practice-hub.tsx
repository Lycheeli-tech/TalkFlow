"use client";

import { useEffect, useState } from "react";
import Link from "next/link";

import { createDailySession, evaluateMockInterview, getMockInterviewPrompt, getQuickReview, MockInterviewPrompt, MockInterviewResult, QuickReviewItem, RetrievalOpportunityResponse, RetrievalResult, startQuickReview, submitQuickReview } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { useInterfaceLocale } from "@/components/interface-locale-provider";
import { getMessages } from "@/lib/i18n";

export function PracticeHub({ token }: { token: string }) {
  const [review, setReview] = useState<QuickReviewItem[]>([]);
  const [reviewOpportunity, setReviewOpportunity] = useState<RetrievalOpportunityResponse | null>(null);
  const [reviewResult, setReviewResult] = useState<RetrievalResult | null>(null);
  const [reviewTranscript, setReviewTranscript] = useState("");
  const [prompt, setPrompt] = useState<MockInterviewPrompt | null>(null);
  const [result, setResult] = useState<MockInterviewResult | null>(null);
  const [transcript, setTranscript] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const { locale } = useInterfaceLocale();
  const copy = getMessages(locale).m6.practice;
  const unavailable = copy.unavailable;

  useEffect(() => {
    if (!token) return;
    void getQuickReview(token).then(setReview).catch(() => setError(unavailable));
  }, [token, unavailable]);

  async function startInterview() {
    setBusy(true); setError("");
    try { setPrompt(await getMockInterviewPrompt(token)); setResult(null); setTranscript(""); }
    catch (caught) { setError(caught instanceof Error ? caught.message : copy.interviewUnavailable); }
    finally { setBusy(false); }
  }

  async function beginReview() {
    setBusy(true); setError("");
    try {
      const session = await createDailySession(token);
      setReviewOpportunity(await startQuickReview(token, session.session_id));
      setReviewResult(null); setReviewTranscript("");
    } catch (caught) { setError(caught instanceof Error ? caught.message : copy.reviewUnavailable); }
    finally { setBusy(false); }
  }

  async function submitReview() {
    if (!reviewOpportunity || !reviewTranscript.trim()) return;
    setBusy(true); setError("");
    try { setReviewResult(await submitQuickReview(token, reviewOpportunity.opportunity_id, reviewTranscript)); setReview((items) => items.slice(1)); }
    catch (caught) { setError(caught instanceof Error ? caught.message : copy.reviewUnavailable); }
    finally { setBusy(false); }
  }

  async function submitInterview() {
    if (!prompt || !transcript.trim()) return;
    setBusy(true); setError("");
    try { setResult(await evaluateMockInterview(token, prompt.question_id, transcript)); }
    catch (caught) { setError(caught instanceof Error ? caught.message : copy.analysisUnavailable); }
    finally { setBusy(false); }
  }

  return <main className="page-shell practice-shell">
    <header className="practice-header"><div><p className="eyebrow">{copy.eyebrow}</p><h1>{copy.title}</h1><p className="hero-copy">{copy.copy}</p></div><Link className="button button-secondary" href="/">{copy.back}</Link></header>
    {!token && <p className="notice" role="status">{copy.copy}</p>}
    <section className="practice-grid">
      <Card className="practice-card"><p className="eyebrow">Quick Review</p><h2>{copy.reviewTitle}</h2>{reviewResult ? <div className="transcript"><strong>{copy.reviewSaved}</strong><p>{reviewResult.recorded ? copy.reviewRecorded : copy.reviewReplay}</p></div> : reviewOpportunity ? <div className="form-stack"><p className="interview-question">{reviewOpportunity.question_text}</p><label className="field"><span>{copy.reviewPrompt}</span><textarea rows={5} value={reviewTranscript} onChange={(event) => setReviewTranscript(event.target.value)} placeholder={copy.reviewPlaceholder} /></label><Button disabled={busy || !reviewTranscript.trim()} onClick={() => void submitReview()}>{busy ? copy.reviewSaving : copy.submitReview}</Button></div> : review.length ? <><p className="card-copy">{copy.reviewCopy}</p><Button disabled={busy || !token} onClick={() => void beginReview()}>{busy ? copy.reviewPreparing : copy.startReview}</Button></> : <p className="card-copy">{copy.noDue}</p>}</Card>
      <Card className="practice-card"><p className="eyebrow">Mock Interview</p><h2>{copy.interviewTitle}</h2>{!prompt && <Button disabled={!token || busy} onClick={() => void startInterview()}>{busy ? copy.reviewPreparing : copy.startInterview}</Button>}{prompt && !result && <div className="form-stack"><p className="interview-question">{prompt.question}</p><label className="field"><span>{copy.answer}</span><textarea rows={7} value={transcript} onChange={(event) => setTranscript(event.target.value)} placeholder={copy.answerPlaceholder} /></label><Button disabled={busy || !transcript.trim()} onClick={() => void submitInterview()}>{busy ? copy.analyzing : copy.submit}</Button></div>}{result && <div className="transcript"><strong>{copy.reviewed}</strong><p>{result.analysis.fluency} · {result.analysis.structure}</p><p className="card-copy">{result.analysis.focus_areas[0] ?? copy.copy}</p><Button className="button-secondary" onClick={() => setResult(null)}>{copy.tryAnother}</Button></div>}</Card>
    </section>{error && <p className="error" role="alert">{error}</p>}
  </main>;
}
