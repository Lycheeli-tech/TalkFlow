"use client";

import Link from "next/link";
import { ReactNode } from "react";

import { useInterfaceLocale } from "@/components/interface-locale-provider";
import { clearAccessToken } from "@/lib/auth-session";
import { COURSE_CORE_FEATURES } from "@/lib/course-core-flags";
import { getMessages } from "@/lib/i18n";

import styles from "./course-core.module.css";

export function CourseCoreAppShell({ children }: { children: ReactNode }) {
  const { locale, setLocale } = useInterfaceLocale();
  const copy = getMessages(locale).courseCore;

  return (
    <div className={styles.shell}>
      <header className={styles.appHeader}>
        <Link className={styles.wordmark} href="/">FluentLoop</Link>
        <nav className={styles.navigation} aria-label={copy.navigationLabel}>
          <Link href="/courses">{copy.courses}</Link>
          {COURSE_CORE_FEATURES.practice ? <Link href="/practice">{copy.practice}</Link> : <span aria-disabled="true">{copy.practice}</span>}
          {COURSE_CORE_FEATURES.aboutMe ? <Link href="/about-me">{copy.aboutMe}</Link> : <span aria-disabled="true">{copy.aboutMe}</span>}
        </nav>
        <div className={styles.headerActions}>
          <div className={styles.localeSwitch} aria-label={copy.languageLabel}>
            <button type="button" aria-pressed={locale === "en"} onClick={() => setLocale("en")}>EN</button>
            <button type="button" aria-pressed={locale === "zh-CN"} onClick={() => setLocale("zh-CN")}>中文</button>
          </div>
          <button className={styles.signOut} type="button" onClick={clearAccessToken}>{copy.signOut}</button>
        </div>
      </header>
      <main className={styles.content}>{children}</main>
    </div>
  );
}
