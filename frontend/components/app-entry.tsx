"use client";

import { useEffect, useState } from "react";
import Link from "next/link";

import { OnboardingFlow } from "@/components/onboarding-flow";
import { VoiceCalibration } from "@/components/voice-calibration";
import { TodaySession } from "@/components/today-session";
import { useInterfaceLocale } from "@/components/interface-locale-provider";
import { getApplicationEntry, ApplicationEntry } from "@/lib/api";
import { getMessages } from "@/lib/i18n";

export function AppEntry() {
  const [token] = useState(() => (typeof window === "undefined" ? "" : sessionStorage.getItem("fluentloop_access_token") ?? ""));
  const [entry, setEntry] = useState<ApplicationEntry | null>(null);
  const [error, setError] = useState("");
  const { locale, setLocale } = useInterfaceLocale();
  const entryCopy = getMessages(locale).m6.entry;
  const entryError = entryCopy.error;

  useEffect(() => {
    if (!token) return;
    void getApplicationEntry(token)
      .then((nextEntry) => {
        setEntry(nextEntry);
        setLocale(nextEntry.interface_language);
      })
      .catch(() => setError(entryError));
  }, [token, entryError, setLocale]);

  if (!token) return <OnboardingFlow />;
  if (!entry && !error) return <main className="page-shell"><p className="notice" role="status">{entryCopy.loading}</p></main>;
  if (error) return <main className="page-shell"><p className="error" role="alert">{error}</p></main>;
  if (entry?.stage === "ONBOARDING") return <OnboardingFlow initialToken={token} initialTargetRole={entry.target_role ?? ""} onReady={() => void getApplicationEntry(token).then(setEntry)} />;
  const messages = getMessages(locale);
  if (entry?.stage === "CALIBRATION") return <AppShell><VoiceCalibration token={token} copy={messages.calibration} onComplete={() => setEntry({ ...entry, stage: "TODAY" })} /></AppShell>;
  return <AppShell><TodaySession token={token} /></AppShell>;
}

export function AppShell({ children }: { children: React.ReactNode }) {
  const { locale } = useInterfaceLocale();
  const labels = getMessages(locale).navigation;
  return <div className="app-shell"><nav className="primary-nav" aria-label={labels.label}><Link href="/">{labels.today}</Link><Link href="/practice">{labels.practice}</Link><Link href="/my-english">{labels.myEnglish}</Link><Link href="/journey">{labels.journey}</Link></nav><section className="app-content">{children}</section></div>;
}
