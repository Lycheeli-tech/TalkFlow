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
