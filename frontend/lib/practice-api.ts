import { clearAccessToken, getStoredAccessToken } from "@/lib/auth-session";
import type { CourseQuestion } from "@/lib/course-api";

const BASE = process.env.NEXT_PUBLIC_API_BASE_URL?.replace(/\/$/, "") ?? "http://localhost:8000";
export type PracticeAnswer = { id: string; question_id: string; status: "PROCESSING" | "FAILED" | "SAVED";
  transcript: string | null; duration_ms: number; audio_available: boolean; error_code: string | null };
export type PracticeRun = { id: string; question_count: 3 | 5; questions: CourseQuestion[];
  current_position: number; status: "ACTIVE" | "PAUSED" | "GENERATING"; expires_at: string;
  skipped: string[]; answers: PracticeAnswer[] };
type Evidence = { question_id: string; quote: string; observation: string };
export type PracticeFeedback = { summary: string; strengths: Evidence[]; improvements: Evidence[];
  score: number; prompt_version: string; provider_name: string; model_name: string | null };

async function response(path: string, options?: RequestInit) {
  const result = await fetch(`${BASE}/api/v1/practice${path}`, { ...options,
    headers: { ...options?.headers, Authorization: `Bearer ${getStoredAccessToken()}` } });
  if (result.status === 401) clearAccessToken();
  if (!result.ok) {
    const payload = await result.json().catch(() => null);
    throw new Error(payload?.detail ?? "Practice request failed.");
  }
  return result;
}
async function json<T>(path: string, options?: RequestInit): Promise<T> {
  return (await response(path, options)).json();
}
export const getCurrentPractice = () => json<PracticeRun | null>("/runs/current");
export const getPractice = (id: string) => json<PracticeRun>(`/runs/${id}`);
export const createPractice = (count: 3 | 5, key: string) => json<PracticeRun>("/runs", {
  method: "POST", headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ question_count: count, idempotency_key: key }) });
export const movePractice = (id: string, position: number, paused = false, skip = false) =>
  json<PracticeRun>(`/runs/${id}/position`, { method: "PATCH", headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ position, paused, skip_current: skip }) });
export function submitPractice(id: string, question: string, blob: Blob, duration: number, key: string) {
  const body = new FormData();
  body.append("question_id", question); body.append("recording", blob, "practice.webm");
  body.append("duration_ms", String(duration)); body.append("idempotency_key", key);
  return json<PracticeRun>(`/runs/${id}/answers`, { method: "POST", body });
}
export const retryPracticeAnswer = (id: string, answer: string) =>
  json<PracticeRun>(`/runs/${id}/answers/${answer}/retry`, { method: "POST" });
export const completePractice = (id: string) => json<PracticeFeedback>(`/runs/${id}/complete`, { method: "POST" });
export const abandonPractice = async (id: string) => { await response(`/runs/${id}`, { method: "DELETE" }); };
export const practiceAudio = async (id: string, answer?: string) =>
  (await response(answer ? `/runs/${id}/answers/${answer}/audio` : `/runs/${id}/tts`)).blob();
