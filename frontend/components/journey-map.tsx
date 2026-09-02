"use client";

import { useEffect, useState } from "react";
import Link from "next/link";

import { getJourney, JourneyResponse } from "@/lib/api";
import { Card } from "@/components/ui/card";
import { useInterfaceLocale } from "@/components/interface-locale-provider";
import { getMessages } from "@/lib/i18n";

const phaseCopy = {
  BUILD: "Build",
  TRANSFER: "Transfer",
  PERFORM: "Perform",
} as const;

export function JourneyMap({ token }: { token: string }) {
  const [journey, setJourney] = useState<JourneyResponse | null>(null);
  const [error, setError] = useState("");
  const { locale } = useInterfaceLocale();
  const copy = getMessages(locale).m6.journey;
  const unavailable = copy.unavailable;

  useEffect(() => {
    if (!token) return;
    void getJourney(token).then(setJourney).catch(() => setError(unavailable));
  }, [token, unavailable]);

  return <main className="page-shell journey-shell">
    <header className="practice-header"><div><p className="eyebrow">{copy.eyebrow}</p><h1>{copy.title}</h1><p className="hero-copy">{copy.copy}</p></div><Link className="button button-secondary" href="/practice">{copy.practice}</Link></header>
    {!token && <p className="notice" role="status">{copy.signin}</p>}
    {journey && <Card className="journey-card"><div className="journey-summary"><div><p className="eyebrow">Today</p><h2>Day {journey.current_day} · {phaseCopy[journey.current_phase]}</h2></div><p className="card-copy">Each phase keeps the same learning loop while gradually reducing scaffolding.</p></div><ol className="journey-grid" aria-label="30-day journey">{journey.days.map((item) => <li key={item.day} data-phase={item.phase} data-status={item.status}><span>Day {item.day}</span><strong>{phaseCopy[item.phase]}</strong></li>)}</ol></Card>}
    {!journey && token && !error && <p className="notice" role="status">{copy.loading}</p>}
    {error && <p className="error" role="alert">{error}</p>}
  </main>;
}
