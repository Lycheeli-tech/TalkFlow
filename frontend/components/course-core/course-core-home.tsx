"use client";

import Link from "next/link";

import { useInterfaceLocale } from "@/components/interface-locale-provider";
import { COURSE_CORE_FEATURES } from "@/lib/course-core-flags";
import { getMessages } from "@/lib/i18n";

import { CourseCoreAppShell } from "./app-shell";
import styles from "./course-core.module.css";
import { StageOneEntry } from "./stage-one-entry";

export function CourseCoreHome() {
  const { locale } = useInterfaceLocale();
  const copy = getMessages(locale).courseCore;
  const entries = [
    { key: "courses", label: copy.courses, description: copy.coursesDescription, href: "/courses", enabled: COURSE_CORE_FEATURES.courses },
    { key: "practice", label: copy.practice, description: copy.practiceDescription, href: "/practice", enabled: COURSE_CORE_FEATURES.practice },
    { key: "about-me", label: copy.aboutMe, description: copy.aboutMeDescription, href: "/about-me", enabled: COURSE_CORE_FEATURES.aboutMe },
  ];

  return (
    <StageOneEntry>
      <CourseCoreAppShell>
        <section className={styles.hero}>
          <p className={styles.eyebrow}>{copy.homeEyebrow}</p>
          <h1>{copy.homeTitle}</h1>
          <p>{copy.homeDescription}</p>
        </section>
        <section className={styles.entryGrid} aria-label={copy.entryLabel}>
          {entries.map((entry, index) => (
            <article className={styles.entryCard} key={entry.key}>
              <span className={styles.entryNumber}>0{index + 1}</span>
              <h2>{entry.label}</h2>
              <p>{entry.description}</p>
              {entry.enabled ? (
                <Link className={styles.cardAction} href={entry.href}>{copy.open}</Link>
              ) : (
                <span className={styles.comingSoon}>{copy.comingSoon}</span>
              )}
            </article>
          ))}
        </section>
      </CourseCoreAppShell>
    </StageOneEntry>
  );
}
