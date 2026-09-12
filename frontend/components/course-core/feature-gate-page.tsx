"use client";

import { useInterfaceLocale } from "@/components/interface-locale-provider";
import { getMessages } from "@/lib/i18n";

import { CourseCoreAppShell } from "./app-shell";
import styles from "./course-core.module.css";
import { StageOneEntry } from "./stage-one-entry";

export function FeatureGatePage({ feature }: { feature: "practice" | "aboutMe" }) {
  const { locale } = useInterfaceLocale();
  const copy = getMessages(locale).courseCore;
  const title = feature === "practice" ? copy.practice : copy.aboutMe;

  return (
    <StageOneEntry>
      <CourseCoreAppShell>
        <section className={styles.featureGate}>
          <p className={styles.eyebrow}>{copy.featureGateEyebrow}</p>
          <h1>{title}</h1>
          <p>{copy.featureGateDescription}</p>
        </section>
      </CourseCoreAppShell>
    </StageOneEntry>
  );
}
