"use client";

import { FormEvent, ReactNode, useState, useSyncExternalStore } from "react";

import { useInterfaceLocale } from "@/components/interface-locale-provider";
import { signIn, signUp } from "@/lib/auth";
import {
  ACCESS_TOKEN_STORAGE_EVENT,
  clearAccessToken,
  getStoredAccessToken,
  storeAccessToken,
} from "@/lib/auth-session";
import { getMessages } from "@/lib/i18n";

import styles from "./stage-one-entry.module.css";

function subscribeToAccessToken(onStoreChange: () => void) {
  window.addEventListener("storage", onStoreChange);
  window.addEventListener(ACCESS_TOKEN_STORAGE_EVENT, onStoreChange);
  return () => {
    window.removeEventListener("storage", onStoreChange);
    window.removeEventListener(ACCESS_TOKEN_STORAGE_EVENT, onStoreChange);
  };
}

function useAccessToken(): string {
  return useSyncExternalStore(subscribeToAccessToken, getStoredAccessToken, () => "");
}

export function StageOneEntry({ children }: { children?: ReactNode }) {
  const accessToken = useAccessToken();
  const { locale, setLocale } = useInterfaceLocale();
  const copy = getMessages(locale).courseCoreStageOne;
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const [notice, setNotice] = useState("");
  const [error, setError] = useState("");

  async function authenticate(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const submitter = (event.nativeEvent as SubmitEvent).submitter as HTMLButtonElement | null;
    const mode = submitter?.value === "sign-up" ? "sign-up" : "sign-in";
    setBusy(true);
    setNotice("");
    setError("");
    try {
      const nextToken = mode === "sign-in"
        ? await signIn(email, password)
        : await signUp(email, password);
      if (nextToken) {
        storeAccessToken(nextToken);
      } else {
        setNotice(copy.confirmationSent);
      }
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : copy.error);
    } finally {
      setBusy(false);
    }
  }

  if (accessToken && children) return children;

  return (
    <main className={styles.page}>
      <header className={styles.header}>
        <span className={styles.wordmark}>{copy.brand}</span>
        <div className={styles.localeSwitch} aria-label={copy.languageLabel}>
          <button type="button" aria-pressed={locale === "en"} onClick={() => setLocale("en")}>EN</button>
          <button type="button" aria-pressed={locale === "zh-CN"} onClick={() => setLocale("zh-CN")}>中文</button>
        </div>
      </header>

      <section className={styles.panel}>
        <p className={styles.eyebrow}>{copy.eyebrow}</p>
        <h1>{accessToken ? copy.signedInTitle : copy.title}</h1>
        <p className={styles.description}>{accessToken ? copy.signedInCopy : copy.description}</p>

        {accessToken ? (
          <div className={styles.signedIn}>
            <p role="status">{copy.status}</p>
            <button className={styles.secondaryAction} type="button" onClick={clearAccessToken}>
              {copy.signOut}
            </button>
          </div>
        ) : (
          <form className={styles.form} onSubmit={authenticate}>
            <h2>{copy.signInTitle}</h2>
            <label>
              <span>{copy.email}</span>
              <input
                type="email"
                autoComplete="email"
                required
                value={email}
                onChange={(event) => setEmail(event.target.value)}
              />
            </label>
            <label>
              <span>{copy.password}</span>
              <input
                type="password"
                autoComplete="current-password"
                minLength={8}
                required
                value={password}
                onChange={(event) => setPassword(event.target.value)}
              />
            </label>
            <div className={styles.actions}>
              <button className={styles.primaryAction} name="auth-action" value="sign-in" disabled={busy} type="submit">
                {busy ? copy.working : copy.signIn}
              </button>
              <button className={styles.secondaryAction} name="auth-action" value="sign-up" disabled={busy} type="submit">
                {copy.signUp}
              </button>
            </div>
          </form>
        )}

        {notice && <p className={styles.notice} role="status">{notice}</p>}
        {error && <p className={styles.error} role="alert">{error}</p>}
      </section>
    </main>
  );
}
