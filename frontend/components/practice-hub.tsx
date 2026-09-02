"use client";

import { useEffect, useState } from "react";
import Link from "next/link";

import { evaluateMockInterview, getMockInterviewPrompt, getQuickReview, MockInterviewPrompt, MockInterviewResult, QuickReviewItem } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";

export function PracticeHub({ token }: { token: string }) {
  const [review, setReview] = useState<QuickReviewItem[]>([]);
  const [prompt, setPrompt] = useState<MockInterviewPrompt | null>(null);
  const [result, setResult] = useState<MockInterviewResult | null>(null);
  const [transcript, setTranscript] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!token) return;
    void getQuickReview(token).then(setReview).catch(() => setError("Practice data is unavailable right now."));
  }, [token]);

  async function startInterview() {
    setBusy(true); setError("");
    try { setPrompt(await getMockInterviewPrompt(token)); setResult(null); setTranscript(""); }
    catch (caught) { setError(caught instanceof Error ? caught.message : "Interview is unavailable."); }
    finally { setBusy(false); }
  }

  async function submitInterview() {
    if (!prompt || !transcript.trim()) return;
    setBusy(true); setError("");
    try { setResult(await evaluateMockInterview(token, prompt.question_id, transcript)); }
    catch (caught) { setError(caught instanceof Error ? caught.message : "Analysis is unavailable."); }
    finally { setBusy(false); }
  }

  return <main className="page-shell practice-shell">
    <header className="practice-header"><div><p className="eyebrow">FluentLoop · Practice</p><h1>Practice with purpose.</h1><p className="hero-copy">Review what is due, then try one complete interview answer without interruption.</p></div><Link className="button button-secondary" href="/">Back to Today</Link></header>
    {!token && <p className="notice" role="status">Sign in through Today to load your personal practice data.</p>}
    <section className="practice-grid">
      <Card className="practice-card"><p className="eyebrow">Quick Review</p><h2>Keep due expressions warm.</h2>{review.length ? <ul className="review-list">{review.map((item) => <li key={item.expression_id}><strong>{item.text}</strong><span>{item.meaning}</span></li>)}</ul> : <p className="card-copy">No expressions are due right now.</p>}</Card>
      <Card className="practice-card"><p className="eyebrow">Mock Interview</p><h2>One answer, no mid-answer correction.</h2>{!prompt && <Button disabled={!token || busy} onClick={() => void startInterview()}>{busy ? "Preparing…" : "Start mock interview"}</Button>}{prompt && !result && <div className="form-stack"><p className="interview-question">{prompt.question}</p><label className="field"><span>Your complete answer</span><textarea rows={7} value={transcript} onChange={(event) => setTranscript(event.target.value)} placeholder="Answer in your own words…" /></label><Button disabled={busy || !transcript.trim()} onClick={() => void submitInterview()}>{busy ? "Analyzing…" : "Submit answer"}</Button></div>}{result && <div className="transcript"><strong>Answer reviewed</strong><p>Fluency: {result.analysis.fluency} · Structure: {result.analysis.structure}</p><p className="card-copy">{result.analysis.focus_areas[0] ?? "Keep building specific, confident answers."}</p><Button className="button-secondary" onClick={() => setResult(null)}>Try another answer</Button></div>}</Card>
    </section>{error && <p className="error" role="alert">{error}</p>}
  </main>;
}
