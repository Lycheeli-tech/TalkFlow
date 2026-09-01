"use client";

import { FormEvent, useState } from "react";

import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { signIn, signUp } from "@/lib/auth";
import {
  CandidateProfile,
  confirmProfile,
  importProfilePdf,
  importProfileText,
  savePreferences,
} from "@/lib/api";
import { getMessages, InterfaceLocale } from "@/lib/i18n";

type Step = "auth" | "goal" | "source" | "review" | "complete";
type ListField = "education" | "work_experience" | "projects" | "skills" | "industries" | "technical_keywords" | "potential_story_candidates";

function LinesField({
  label,
  value,
  hint,
  onChange,
}: {
  label: string;
  value: string[];
  hint: string;
  onChange: (value: string[]) => void;
}) {
  return (
    <label className="field field-wide">
      <span>{label}</span>
      <textarea
        rows={3}
        value={value.join("\n")}
        placeholder={hint}
        onChange={(event) =>
          onChange(event.target.value.split("\n").map((item) => item.trim()).filter(Boolean))
        }
      />
    </label>
  );
}

export function OnboardingFlow() {
  const [locale, setLocale] = useState<InterfaceLocale>("en");
  const [step, setStep] = useState<Step>("auth");
  const [token, setToken] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [targetRole, setTargetRole] = useState("");
  const [supportLanguage, setSupportLanguage] = useState<InterfaceLocale>("en");
  const [sessionLength, setSessionLength] = useState<10 | 20 | 30 | 60>(20);
  const [importMode, setImportMode] = useState<"pdf" | "text">("pdf");
  const [resume, setResume] = useState<File | null>(null);
  const [background, setBackground] = useState("");
  const [sourceId, setSourceId] = useState("");
  const [candidate, setCandidate] = useState<CandidateProfile | null>(null);
  const [busy, setBusy] = useState(false);
  const [notice, setNotice] = useState("");
  const [error, setError] = useState("");
  const messages = getMessages(locale).onboarding;

  async function run(action: () => Promise<void>) {
    setBusy(true);
    setError("");
    setNotice("");
    try {
      await action();
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : messages.error);
    } finally {
      setBusy(false);
    }
  }

  function authenticate(event: FormEvent, mode: "in" | "up") {
    event.preventDefault();
    void run(async () => {
      const accessToken = mode === "in" ? await signIn(email, password) : await signUp(email, password);
      if (accessToken) {
        setToken(accessToken);
        setStep("goal");
      } else {
        setNotice(messages.confirmationSent);
      }
    });
  }

  function submitGoal(event: FormEvent) {
    event.preventDefault();
    void run(async () => {
      await savePreferences(token, {
        interface_language: locale,
        support_language: supportLanguage,
        default_session_length: sessionLength,
        target_role: targetRole,
      });
      setStep("source");
    });
  }

  function submitSource(event: FormEvent) {
    event.preventDefault();
    void run(async () => {
      if (importMode === "pdf" && !resume) throw new Error("Select a PDF to continue.");
      const result =
        importMode === "pdf"
          ? await importProfilePdf(token, targetRole, resume as File)
          : await importProfileText(token, targetRole, background);
      setSourceId(result.source_id);
      setCandidate(result.candidate);
      setStep("review");
    });
  }

  function updateList(field: ListField, value: string[]) {
    if (candidate) setCandidate({ ...candidate, [field]: value });
  }

  function submitConfirmation(event: FormEvent) {
    event.preventDefault();
    if (!candidate) return;
    void run(async () => {
      await confirmProfile(token, sourceId, candidate);
      setStep("complete");
    });
  }

  return (
    <main className="onboarding-shell">
      <header className="app-header">
        <span className="wordmark">{messages.brand}</span>
        <div className="locale-switch" aria-label="Interface language">
          <button data-active={locale === "en"} onClick={() => setLocale("en")}>EN</button>
          <button data-active={locale === "zh-CN"} onClick={() => setLocale("zh-CN")}>中文</button>
        </div>
      </header>

      <section className="onboarding-grid">
        <div className="onboarding-intro">
          <div className="eyebrow">{messages.brand} · MVP</div>
          <h1>{messages.promise}</h1>
          <p>{messages.intro}</p>
          <ol className="step-track" aria-label="Onboarding progress">
            {["auth", "goal", "source", "review"].map((item, index) => (
              <li key={item} data-active={item === step} data-complete={index < ["auth", "goal", "source", "review", "complete"].indexOf(step)}>
                <span>{index + 1}</span>
              </li>
            ))}
          </ol>
        </div>

        <Card className="onboarding-card">
          {step === "auth" && (
            <form className="form-stack" onSubmit={(event) => authenticate(event, "in")}>
              <h2>{messages.signInTitle}</h2>
              <label className="field"><span>{messages.email}</span><input type="email" required value={email} onChange={(event) => setEmail(event.target.value)} /></label>
              <label className="field"><span>{messages.password}</span><input type="password" minLength={8} required value={password} onChange={(event) => setPassword(event.target.value)} /></label>
              <div className="form-actions">
                <Button disabled={busy} type="submit">{busy ? messages.working : messages.signIn}</Button>
                <Button className="button-secondary" disabled={busy} type="button" onClick={(event) => authenticate(event as unknown as FormEvent, "up")}>{messages.signUp}</Button>
              </div>
            </form>
          )}

          {step === "goal" && (
            <form className="form-stack" onSubmit={submitGoal}>
              <h2>{messages.goalTitle}</h2>
              <label className="field"><span>{messages.targetRole}</span><input required maxLength={160} placeholder={messages.targetRolePlaceholder} value={targetRole} onChange={(event) => setTargetRole(event.target.value)} /></label>
              <div className="field-row">
                <label className="field"><span>{messages.supportLanguage}</span><select value={supportLanguage} onChange={(event) => setSupportLanguage(event.target.value as InterfaceLocale)}><option value="en">English</option><option value="zh-CN">简体中文</option></select></label>
                <label className="field"><span>{messages.sessionLength}</span><select value={sessionLength} onChange={(event) => setSessionLength(Number(event.target.value) as 10 | 20 | 30 | 60)}>{[10, 20, 30, 60].map((minutes) => <option key={minutes} value={minutes}>{minutes} {messages.minutes}</option>)}</select></label>
              </div>
              <Button disabled={busy} type="submit">{busy ? messages.working : messages.continue}</Button>
            </form>
          )}

          {step === "source" && (
            <form className="form-stack" onSubmit={submitSource}>
              <h2>{messages.sourceTitle}</h2><p className="card-copy">{messages.sourceIntro}</p>
              <div className="segmented"><button type="button" data-active={importMode === "pdf"} onClick={() => setImportMode("pdf")}>{messages.uploadPdf}</button><button type="button" data-active={importMode === "text"} onClick={() => setImportMode("text")}>{messages.pasteText}</button></div>
              {importMode === "pdf" ? <label className="file-drop"><input type="file" accept="application/pdf,.pdf" onChange={(event) => setResume(event.target.files?.[0] ?? null)} /><strong>{resume?.name ?? messages.uploadPdf}</strong><span>PDF · 5 MB max</span></label> : <label className="field"><span>{messages.pasteText}</span><textarea rows={9} required value={background} placeholder={messages.backgroundPlaceholder} onChange={(event) => setBackground(event.target.value)} /></label>}
              <div className="form-actions"><Button disabled={busy} type="submit">{busy ? messages.working : messages.extract}</Button><Button className="button-ghost" type="button" onClick={() => setStep("goal")}>{messages.back}</Button></div>
            </form>
          )}

          {step === "review" && candidate && (
            <form className="form-stack" onSubmit={submitConfirmation}>
              <h2>{messages.reviewTitle}</h2><p className="card-copy">{messages.reviewIntro}</p>
              <div className="review-grid">
                {([ ["work_experience", messages.workExperience], ["projects", messages.projects], ["skills", messages.skills], ["industries", messages.industries], ["education", messages.education], ["technical_keywords", messages.keywords] ] as [ListField, string][]).map(([field, label]) => <LinesField key={field} label={label} value={candidate[field]} hint={messages.onePerLine} onChange={(value) => updateList(field, value)} />)}
                <label className="field field-wide"><span>{messages.careerTransition}</span><textarea rows={3} value={candidate.career_transition ?? ""} onChange={(event) => setCandidate({ ...candidate, career_transition: event.target.value || null })} /></label>
                <div className="candidate-note field-wide"><strong>{messages.storyCandidates}</strong><p>{messages.storyWarning}</p>{candidate.potential_story_candidates.map((story) => <span key={story}>{story}</span>)}</div>
              </div>
              <div className="form-actions"><Button disabled={busy} type="submit">{busy ? messages.working : messages.confirm}</Button><Button className="button-ghost" type="button" onClick={() => setStep("source")}>{messages.back}</Button></div>
            </form>
          )}

          {step === "complete" && <div className="completion"><span className="completion-mark">✓</span><h2>{messages.completeTitle}</h2><p>{messages.completeCopy}</p></div>}
          {notice && <p className="notice" role="status">{notice}</p>}
          {error && <p className="error" role="alert"><strong>{messages.error}:</strong> {error}</p>}
        </Card>
      </section>
    </main>
  );
}
