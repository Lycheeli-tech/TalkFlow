"use client";

import { useEffect, useState } from "react";
import Link from "next/link";

import { getMyEnglish, MyEnglishResponse } from "@/lib/api";
import { Card } from "@/components/ui/card";

export function MyEnglish({ token }: { token: string }) {
  const [memory, setMemory] = useState<MyEnglishResponse | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!token) return;
    void getMyEnglish(token).then(setMemory).catch(() => setError("My English is unavailable right now."));
  }, [token]);

  return <main className="page-shell my-english-shell">
    <header className="practice-header"><div><p className="eyebrow">FluentLoop · My English</p><h1>Your usable language.</h1><p className="hero-copy">A calm view of what you are building: expressions, patterns, and confirmed stories.</p></div><Link className="button button-secondary" href="/practice">Practice</Link></header>
    {!token && <p className="notice" role="status">Sign in through Today to see your personal learning memory.</p>}
    {memory && <section className="my-english-grid">
      <MemoryCard title="Expressions" empty="Expressions you learn and retrieve will appear here.">{memory.expressions.map((item) => <li key={item.id}><strong>{item.text}</strong><span>{item.meaning} · {item.status}</span></li>)}</MemoryCard>
      <MemoryCard title="Patterns" empty="Patterns are added only after repeated evidence.">{memory.patterns.map((item) => <li key={item.id}><strong>{item.pattern_type}</strong><span>{item.original_example} · {item.status}</span></li>)}</MemoryCard>
      <MemoryCard title="Stories" empty="Only stories you confirm are saved here.">{memory.stories.map((item) => <li key={item.id}><strong>{item.title}</strong><span>{item.content}</span></li>)}</MemoryCard>
    </section>}
    {!memory && token && !error && <p className="notice" role="status">Loading your learning memory…</p>}
    {error && <p className="error" role="alert">{error}</p>}
  </main>;
}

function MemoryCard({ title, empty, children }: { title: string; empty: string; children: React.ReactNode }) {
  const items = Array.isArray(children) ? children : [children];
  return <Card className="memory-card"><p className="eyebrow">{title}</p>{items.length && items[0] ? <ul className="review-list">{children}</ul> : <p className="card-copy">{empty}</p>}</Card>;
}
