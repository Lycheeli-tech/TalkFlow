"use client";

import { useEffect, useState } from "react";
import Link from "next/link";

import { getMyEnglish, MyEnglishResponse } from "@/lib/api";
import { Card } from "@/components/ui/card";
import { useInterfaceLocale } from "@/components/interface-locale-provider";
import { getMessages } from "@/lib/i18n";

export function MyEnglish({ token }: { token: string }) {
  const [memory, setMemory] = useState<MyEnglishResponse | null>(null);
  const [error, setError] = useState("");
  const { locale } = useInterfaceLocale();
  const copy = getMessages(locale).m6.myEnglish;
  const unavailable = copy.unavailable;

  useEffect(() => {
    if (!token) return;
    void getMyEnglish(token).then(setMemory).catch(() => setError(unavailable));
  }, [token, unavailable]);

  return <main className="page-shell my-english-shell">
    <header className="practice-header"><div><p className="eyebrow">{copy.eyebrow}</p><h1>{copy.title}</h1><p className="hero-copy">{copy.copy}</p></div><Link className="button button-secondary" href="/practice">{copy.practice}</Link></header>
    {!token && <p className="notice" role="status">{copy.signin}</p>}
    {memory && <section className="my-english-grid">
      <MemoryCard title={copy.expressions} empty={copy.expressionEmpty}>{memory.expressions.map((item) => <li key={item.id}><strong>{item.text}</strong><span>{item.meaning} · {item.status}</span></li>)}</MemoryCard>
      <MemoryCard title={copy.patterns} empty={copy.patternEmpty}>{memory.patterns.map((item) => <li key={item.id}><strong>{item.pattern_type}</strong><span>{item.original_example} · {item.status}</span></li>)}</MemoryCard>
      <MemoryCard title={copy.stories} empty={copy.storyEmpty}>{memory.stories.map((item) => <li key={item.id}><strong>{item.title}</strong><span>{item.content}</span></li>)}</MemoryCard>
    </section>}
    {!memory && token && !error && <p className="notice" role="status">{copy.loading}</p>}
    {error && <p className="error" role="alert">{error}</p>}
  </main>;
}

function MemoryCard({ title, empty, children }: { title: string; empty: string; children: React.ReactNode }) {
  const items = Array.isArray(children) ? children : [children];
  return <Card className="memory-card"><p className="eyebrow">{title}</p>{items.length && items[0] ? <ul className="review-list">{children}</ul> : <p className="card-copy">{empty}</p>}</Card>;
}
