"use client";

import { useEffect, useState } from "react";
import Link from "next/link";

import { getJourney, JourneyResponse } from "@/lib/api";
import { Card } from "@/components/ui/card";

const phaseCopy = {
  BUILD: "Build",
  TRANSFER: "Transfer",
  PERFORM: "Perform",
} as const;

export function JourneyMap({ token }: { token: string }) {
  const [journey, setJourney] = useState<JourneyResponse | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!token) return;
    void getJourney(token).then(setJourney).catch(() => setError("Journey is unavailable right now."));
  }, [token]);

  return <main className="page-shell journey-shell">
    <header className="practice-header"><div><p className="eyebrow">FluentLoop · Journey</p><h1>Your 30-day path.</h1><p className="hero-copy">A steady progression from building language to transferring it, then performing under interview conditions.</p></div><Link className="button button-secondary" href="/practice">Practice</Link></header>
    {!token && <p className="notice" role="status">Sign in through Today to see your personal journey.</p>}
    {journey && <Card className="journey-card"><div className="journey-summary"><div><p className="eyebrow">Today</p><h2>Day {journey.current_day} · {phaseCopy[journey.current_phase]}</h2></div><p className="card-copy">Each phase keeps the same learning loop while gradually reducing scaffolding.</p></div><ol className="journey-grid" aria-label="30-day journey">{journey.days.map((item) => <li key={item.day} data-phase={item.phase} data-status={item.status}><span>Day {item.day}</span><strong>{phaseCopy[item.phase]}</strong></li>)}</ol></Card>}
    {!journey && token && !error && <p className="notice" role="status">Loading your journey…</p>}
    {error && <p className="error" role="alert">{error}</p>}
  </main>;
}
