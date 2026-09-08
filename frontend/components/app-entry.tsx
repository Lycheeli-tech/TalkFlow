"use client";

import { useEffect, useRef, useState, useSyncExternalStore } from "react";
import Link from "next/link";

import { OnboardingFlow } from "@/components/onboarding-flow";
import { VoiceCalibration } from "@/components/voice-calibration";
import { TodaySession } from "@/components/today-session";
import { useInterfaceLocale } from "@/components/interface-locale-provider";
import {
  getApplicationEntry,
  ApplicationEntry,
  ACCESS_TOKEN_STORAGE_KEY,
  ACCESS_TOKEN_STORAGE_EVENT,
} from "@/lib/api";
import { getMessages } from "@/lib/i18n";

function subscribeToAccessToken(onStoreChange: () => void) {
  window.addEventListener("storage", onStoreChange);
  window.addEventListener(ACCESS_TOKEN_STORAGE_EVENT, onStoreChange);
  return () => {
    window.removeEventListener("storage", onStoreChange);
    window.removeEventListener(ACCESS_TOKEN_STORAGE_EVENT, onStoreChange);
  };
}

function getStoredAccessToken(): string {
  if (typeof window === "undefined") return "";
  return sessionStorage.getItem(ACCESS_TOKEN_STORAGE_KEY) ?? "";
}

export function AppEntry() {
  const token = useSyncExternalStore(subscribeToAccessToken, getStoredAccessToken, () => "");
  const [entry, setEntry] = useState<ApplicationEntry | null>(null);
  const [error, setError] = useState("");
  const { locale, setLocale } = useInterfaceLocale();
  const entryCopy = getMessages(locale).m6.entry;
  const entryError = entryCopy.error;
  const entryErrorRef = useRef(entryError);

  useEffect(() => {
    entryErrorRef.current = entryError;
  }, [entryError]);

  useEffect(() => {
    if (!token) return;
    void getApplicationEntry(token)
      .then((nextEntry) => {
        setEntry(nextEntry);
        setError("");
        setLocale(nextEntry.interface_language);
      })
      .catch(() => setError(entryErrorRef.current));
  }, [token, setLocale]);

  if (!token) return <OnboardingFlow />;
  if (!entry && !error) return <main className="page-shell"><p className="notice" role="status">{entryCopy.loading}</p></main>;
  if (error) return <main className="page-shell"><p className="error" role="alert">{error}</p></main>;
  if (entry?.stage === "ONBOARDING") return <OnboardingFlow initialToken={token} initialTargetRole={entry.target_role ?? ""} onReady={() => void getApplicationEntry(token).then(setEntry)} />;
  const messages = getMessages(locale);
  if (entry?.stage === "CALIBRATION") return <AppShell><VoiceCalibration token={token} copy={messages.calibration} onComplete={() => setEntry({ ...entry, stage: "TODAY" })} /></AppShell>;
  return <AppShell><TodaySession token={token} /></AppShell>;
}

export function AppShell({ children }: { children: React.ReactNode }) {
  const { locale, setLocale } = useInterfaceLocale();
  const labels = getMessages(locale).navigation;
  return <div className="app-shell"><nav className="primary-nav" aria-label={labels.label}><Link href="/">{labels.today}</Link><Link href="/practice">{labels.practice}</Link><Link href="/my-english">{labels.myEnglish}</Link><Link href="/journey">{labels.journey}</Link></nav><div className="locale-switch app-locale-switch" aria-label="Interface language"><button data-active={locale === "en"} onClick={() => setLocale("en")}>EN</button><button data-active={locale === "zh-CN"} onClick={() => setLocale("zh-CN")}>中文</button></div><section className="app-content">{children}</section></div>;
}
