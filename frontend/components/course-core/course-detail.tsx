"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { useInterfaceLocale } from "@/components/interface-locale-provider";
import { CourseCatalogItem, getCourse } from "@/lib/course-api";
import { getMessages } from "@/lib/i18n";

import { CourseCoreAppShell } from "./app-shell";
import styles from "./course-core.module.css";
import { StageOneEntry } from "./stage-one-entry";

export function CourseDetailPage({ courseId }: { courseId: string }) {
  const { locale } = useInterfaceLocale();
  const copy = getMessages(locale).courseCore;
  const [course, setCourse] = useState<CourseCatalogItem | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    void getCourse(courseId)
      .then((nextCourse) => {
        setCourse(nextCourse);
        setError("");
      })
      .catch(() => setError(copy.courseNotFound));
  }, [copy.courseNotFound, courseId]);

  return (
    <StageOneEntry>
      <CourseCoreAppShell>
        <Link className={styles.backLink} href="/courses">← {copy.backToCourses}</Link>
        {!course && !error && <p className={styles.status} role="status">{copy.loading}</p>}
        {error && <p className={styles.error} role="alert">{error}</p>}
        {course && (
          <article className={styles.detail}>
            <p className={styles.eyebrow}>{copy.course} {String(course.order).padStart(2, "0")}</p>
            <h1>{locale === "zh-CN" ? course.name_zh_cn : course.name_en}</h1>
            <section className={styles.focus}>
              <span>{copy.answerFocus}</span>
              <p>{locale === "zh-CN" ? course.answer_focus_zh_cn : course.answer_focus_en}</p>
            </section>
            <div className={styles.questionList}>
              <section>
                <span>{copy.coreQuestion}</span>
                <h2>{course.core_question.text}</h2>
              </section>
              {course.follow_up_question && (
                <section>
                  <span>{copy.followUpQuestion}</span>
                  <h2>{course.follow_up_question.text}</h2>
                </section>
              )}
            </div>
            <p className={styles.featureNote}>{copy.answeringComingSoon}</p>
          </article>
        )}
      </CourseCoreAppShell>
    </StageOneEntry>
  );
}
