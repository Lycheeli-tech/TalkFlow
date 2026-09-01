export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL?.replace(/\/$/, "") ?? "http://localhost:8000";

export type CandidateProfile = {
  target_role: string;
  primary_goal: "english_interview";
  education: string[];
  work_experience: string[];
  projects: string[];
  skills: string[];
  industries: string[];
  career_transition: string | null;
  technical_keywords: string[];
  potential_story_candidates: string[];
};

type CandidateResponse = {
  source_id: string;
  extractor_version: string;
  candidate: CandidateProfile;
};

async function apiFetch<T>(path: string, token: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: {
      Authorization: `Bearer ${token}`,
      ...(init?.body instanceof FormData ? {} : { "Content-Type": "application/json" }),
      ...init?.headers,
    },
  });
  if (!response.ok) {
    const payload = (await response.json().catch(() => null)) as { detail?: string } | null;
    throw new Error(payload?.detail ?? `Request failed with status ${response.status}.`);
  }
  return response.json() as Promise<T>;
}

export async function savePreferences(
  token: string,
  preferences: {
    interface_language: "en" | "zh-CN";
    support_language: "en" | "zh-CN";
    default_session_length: 10 | 20 | 30 | 60;
    target_role: string;
  },
) {
  return apiFetch("/api/v1/users/me", token, {
    method: "PATCH",
    body: JSON.stringify(preferences),
  });
}

export function importProfileText(token: string, targetRole: string, rawText: string) {
  return apiFetch<CandidateResponse>("/api/v1/profiles/sources/text", token, {
    method: "POST",
    body: JSON.stringify({ target_role: targetRole, raw_text: rawText }),
  });
}

export function importProfilePdf(token: string, targetRole: string, file: File) {
  const body = new FormData();
  body.set("target_role", targetRole);
  body.set("resume", file);
  return apiFetch<CandidateResponse>("/api/v1/profiles/sources/pdf", token, {
    method: "POST",
    body,
  });
}

export function confirmProfile(token: string, sourceId: string, candidate: CandidateProfile) {
  return apiFetch("/api/v1/profiles/confirm", token, {
    method: "POST",
    body: JSON.stringify({ source_id: sourceId, candidate }),
  });
}

export type CalibrationQuestion = { category: "EXPERIENCE" | "MOTIVATION" | "PROJECT"; text: string };
export type CalibrationSession = { id: string; status: "IN_PROGRESS" | "COMPLETED"; questions: CalibrationQuestion[] };
export type VoiceAttempt = { id: string; question_type: CalibrationQuestion["category"]; transcript: string | null; status: "AUDIO_SAVED" | "STT_FAILED" | "TRANSCRIBED" | "ANALYSIS_FAILED" | "ANALYZED"; provider_error: string | null };
export type LearnerAssessment = { fluency: string; naturalness: string; grammar: string; retrieval: string; structure: string; strengths: string[]; primary_focus: string; secondary_focus: string | null; observed_patterns: string[]; assessment_version: string };

export function startCalibration(token: string) {
  return apiFetch<CalibrationSession>("/api/v1/calibration/sessions", token, { method: "POST" });
}

export async function calibrationTts(token: string, sessionId: string, category: string) {
  const response = await fetch(`${API_BASE_URL}/api/v1/calibration/sessions/${sessionId}/questions/${category}/tts`, { headers: { Authorization: `Bearer ${token}` } });
  if (!response.ok) throw new Error("Question audio is unavailable. Read the question and continue.");
  return response.blob();
}

export function submitCalibrationAttempt(token: string, sessionId: string, category: string, recording: Blob, durationMs: number) {
  const body = new FormData();
  body.set("category", category);
  body.set("response_duration_ms", String(durationMs));
  body.set("recording", recording, "calibration.webm");
  return apiFetch<VoiceAttempt>(`/api/v1/calibration/sessions/${sessionId}/attempts`, token, { method: "POST", body });
}

export function retryCalibrationAttempt(token: string, attemptId: string) {
  return apiFetch<VoiceAttempt>(`/api/v1/calibration/attempts/${attemptId}/retry`, token, { method: "POST" });
}

export function getCalibration(token: string, sessionId: string) {
  return apiFetch<{ session: CalibrationSession; attempts: VoiceAttempt[]; assessment: LearnerAssessment | null }>(`/api/v1/calibration/sessions/${sessionId}`, token);
}
