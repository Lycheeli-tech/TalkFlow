"use client";

import { FormEvent, useCallback, useEffect, useState } from "react";

import { useInterfaceLocale } from "@/components/interface-locale-provider";
import {
  AboutMe,
  addTargetRole,
  deleteAboutMeItem,
  getAboutMe,
  updateSupplementalFacts,
  uploadResume,
} from "@/lib/about-me-api";
import { getStoredAccessToken } from "@/lib/auth-session";
import { getMessages } from "@/lib/i18n";

import { CourseCoreAppShell } from "./app-shell";
import styles from "./course-core.module.css";
import { StageOneEntry } from "./stage-one-entry";

export function AboutMePage() {
  const { locale } = useInterfaceLocale();
  const copy = getMessages(locale).courseCore.aboutMePage;
  const [data, setData] = useState<AboutMe | null>(null);
  const [role, setRole] = useState("");
  const [facts, setFacts] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  const refresh = useCallback(async () => {
    const result = await getAboutMe(getStoredAccessToken());
    setData(result);
    setFacts(result.supplemental_facts.join("\n"));
  }, []);

  useEffect(() => {
    void getAboutMe(getStoredAccessToken())
      .then((result) => {
        setData(result);
        setFacts(result.supplemental_facts.join("\n"));
      })
      .catch(() => setError(copy.loadError));
  }, [copy.loadError]);

  async function run(operation: () => Promise<unknown>) {
    setBusy(true);
    setError("");
    try {
      await operation();
      await refresh();
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : copy.saveError);
    } finally {
      setBusy(false);
    }
  }

  function submitRole(event: FormEvent) {
    event.preventDefault();
    void run(async () => {
      await addTargetRole(getStoredAccessToken(), role);
      setRole("");
    });
  }

  function confirmDelete(path: string) {
    if (!window.confirm(copy.deleteConfirm)) return;
    void run(() => deleteAboutMeItem(getStoredAccessToken(), path));
  }

  return (
    <StageOneEntry>
      <CourseCoreAppShell>
        <section className={styles.pageHeading}>
          <div><p className={styles.eyebrow}>{copy.eyebrow}</p><h1>{copy.title}</h1></div>
          <p>{copy.description}</p>
        </section>
        {!data && !error && <p className={styles.status}>{copy.loading}</p>}
        {error && <p className={styles.error} role="alert">{error}</p>}
        {data && (
          <div className={styles.aboutGrid}>
            <section className={styles.aboutCard}>
              <h2>{copy.roles}</h2><p>{copy.rolesHelp}</p>
              <form className={styles.inlineForm} onSubmit={submitRole}>
                <input required maxLength={160} value={role} onChange={(event) => setRole(event.target.value)} placeholder={copy.rolePlaceholder} />
                <button disabled={busy} type="submit">{copy.add}</button>
              </form>
              <ul>{data.target_roles.map((item) => <li key={item.id}><span>{item.role_name}</span><button disabled={busy} onClick={() => confirmDelete(`target-roles/${item.id}`)}>{copy.delete}</button></li>)}</ul>
              {data.target_roles.length === 0 && <small>{copy.emptyRoles}</small>}
            </section>
            <section className={styles.aboutCard}>
              <h2>{copy.resumes}</h2><p>{copy.resumesHelp}</p>
              <label className={styles.fileInput}>{copy.upload}<input disabled={busy} type="file" accept="application/pdf,.pdf" onChange={(event) => { const file = event.target.files?.[0]; if (file) void run(() => uploadResume(getStoredAccessToken(), file)); event.target.value = ""; }} /></label>
              <ul>{data.resumes.map((item) => <li key={item.id}><span>{item.filename}</span><button disabled={busy} onClick={() => confirmDelete(`resumes/${item.id}`)}>{copy.delete}</button></li>)}</ul>
              {data.resumes.length === 0 && <small>{copy.emptyResumes}</small>}
            </section>
            <section className={`${styles.aboutCard} ${styles.aboutWide}`}>
              <h2>{copy.facts}</h2><p>{copy.factsHelp}</p>
              <textarea rows={7} value={facts} onChange={(event) => setFacts(event.target.value)} placeholder={copy.factsPlaceholder} />
              <button disabled={busy} onClick={() => void run(() => updateSupplementalFacts(getStoredAccessToken(), facts.split("\n")))}>{copy.save}</button>
            </section>
            <section className={`${styles.aboutCard} ${styles.aboutWide}`}>
              <h2>{copy.memories}</h2><p>{copy.memoriesHelp}</p>
              <div className={styles.memoryList}>{data.memories.map((item) => <article key={item.id}><p>{item.content}</p><small>{item.sources.map((source) => source.source_type).join(" · ")}</small><button disabled={busy} onClick={() => confirmDelete(`memories/${item.id}`)}>{copy.deleteMemory}</button></article>)}</div>
              {data.memories.length === 0 && <small>{copy.emptyMemories}</small>}
            </section>
          </div>
        )}
      </CourseCoreAppShell>
    </StageOneEntry>
  );
}
