"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { useInterfaceLocale } from "@/components/interface-locale-provider";
import { CourseCatalog, getCourseCatalog } from "@/lib/course-api";
import { getMessages } from "@/lib/i18n";

import { CourseCoreAppShell } from "./app-shell";
import styles from "./course-core.module.css";
import { StageOneEntry } from "./stage-one-entry";

export function CourseCatalogPage() {
  const { locale } = useInterfaceLocale();
  const copy = getMessages(locale).courseCore;
  const [catalog, setCatalog] = useState<CourseCatalog | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    void getCourseCatalog()
      .then((nextCatalog) => {
        setCatalog(nextCatalog);
        setError("");
      })
      .catch((caught) => setError(caught instanceof Error ? caught.message : copy.catalogError));
  }, [copy.catalogError]);

  return (
    <StageOneEntry>
      <CourseCoreAppShell>
        <section className={styles.pageHeading}>
          <div>
            <p className={styles.eyebrow}>{copy.catalogEyebrow}</p>
            <h1>{copy.catalogTitle}</h1>
          </div>
          <p>{copy.catalogDescription}</p>
        </section>
        {!catalog && !error && <p className={styles.status} role="status">{copy.loading}</p>}
        {error && <p className={styles.error} role="alert">{copy.catalogError}</p>}
        {catalog && (
          <>
            <p className={styles.catalogMeta}>{catalog.version} · {catalog.courses.length} {copy.courseCount}</p>
            <ol className={styles.catalogGrid}>
              {catalog.courses.map((course) => (
                <li key={course.id}>
                  <Link className={styles.courseCard} href={`/courses/${course.id}`}>
                    <span>{String(course.order).padStart(2, "0")}</span>
                    <h2>{locale === "zh-CN" ? course.name_zh_cn : course.name_en}</h2>
                    <p>{course.core_question.text}</p>
                    <small>{course.follow_up_question ? copy.twoQuestions : copy.oneQuestion}</small>
                  </Link>
                </li>
              ))}
            </ol>
          </>
        )}
      </CourseCoreAppShell>
    </StageOneEntry>
  );
}
