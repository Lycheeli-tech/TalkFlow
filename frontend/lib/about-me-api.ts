import { clearAccessToken } from "@/lib/auth-session";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL?.replace(/\/$/, "") ?? "http://localhost:8000";

export type TargetRole = { id: string; role_name: string; created_at: string };
export type ResumeDocument = {
  id: string;
  filename: string;
  parse_status: string;
  created_at: string;
};
export type MemorySource = {
  id: string;
  source_type: "PROFILE" | "SOURCE_DOCUMENT" | "USER_INPUT" | "COURSE_ANSWER";
  source_excerpt: string;
  source_field_path: string | null;
};
export type MemoryItem = {
  id: string;
  content: string;
  updated_at: string;
  sources: MemorySource[];
};
export type AboutMe = {
  supplemental_facts: string[];
  target_roles: TargetRole[];
  resumes: ResumeDocument[];
  memories: MemoryItem[];
};

async function request<T>(token: string, path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: { Authorization: `Bearer ${token}`, ...init?.headers },
  });
  if (response.status === 401) clearAccessToken();
  if (!response.ok) {
    const payload = (await response.json().catch(() => null)) as { detail?: string } | null;
    throw new Error(payload?.detail ?? `Request failed with status ${response.status}.`);
  }
  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}

export function getAboutMe(token: string): Promise<AboutMe> {
  return request(token, "/api/v1/about-me");
}

export function updateSupplementalFacts(token: string, facts: string[]): Promise<AboutMe> {
  return request(token, "/api/v1/about-me", {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ supplemental_facts: facts }),
  });
}

export function addTargetRole(token: string, roleName: string): Promise<TargetRole> {
  return request(token, "/api/v1/about-me/target-roles", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ role_name: roleName }),
  });
}

export function uploadResume(token: string, file: File): Promise<ResumeDocument> {
  const body = new FormData();
  body.append("resume", file);
  return request(token, "/api/v1/about-me/resumes", { method: "POST", body });
}

export function deleteAboutMeItem(token: string, path: string): Promise<void> {
  return request(token, `/api/v1/about-me/${path}`, { method: "DELETE" });
}
