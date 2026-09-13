"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { useInterfaceLocale } from "@/components/interface-locale-provider";
import { CourseCatalogItem, getCourse } from "@/lib/course-api";
import { getMessages } from "@/lib/i18n";

import { CourseCoreAppShell } from "./app-shell";
import styles from "./course-core.module.css";
import { CourseWorkspace } from "./course-workspace";
import { StageOneEntry } from "./stage-one-entry";

export function CourseDetailPage({ courseId }: { courseId: string }) {
  const { locale } = useInterfaceLocale();
  const copy = getMessages(locale).courseCore;
  const [course, setCourse] = useState<CourseCatalogItem | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;
    void getCourse(courseId)
      .then((nextCourse) => {
        if (cancelled) return;
        setCourse(nextCourse);
        setError("");
      })
      .catch(() => { if (!cancelled) setError(copy.courseNotFound); });
    return () => { cancelled = true; };
  }, [copy.courseNotFound, courseId]);

  if (course?.id === courseId) {
    return (
      <StageOneEntry>
        <CourseWorkspace key={course.id} course={course} />
      </StageOneEntry>
    );
  }

  return (
    <StageOneEntry>
      <CourseCoreAppShell>
        <Link className={styles.backLink} href="/courses">
          ← {copy.backToCourses}
        </Link>
        {!error && (
          <p className={styles.status} role="status">
            {copy.loading}
          </p>
        )}
        {error && (
          <p className={styles.error} role="alert">
            {error}
          </p>
        )}
      </CourseCoreAppShell>
    </StageOneEntry>
  );
}
