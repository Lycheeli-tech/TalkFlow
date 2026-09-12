import { clearAccessToken } from "@/lib/auth-session";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL?.replace(/\/$/, "") ?? "http://localhost:8000";

export type CourseQuestion = {
  id: string;
  kind: "CORE" | "FOLLOW_UP";
  text: string;
};

export type CourseCatalogItem = {
  id: string;
  order: number;
  name_en: string;
  name_zh_cn: string;
  answer_focus_en: string;
  answer_focus_zh_cn: string;
  core_question: CourseQuestion;
  follow_up_question: CourseQuestion | null;
};

export type CourseCatalog = {
  version: "course_catalog_v1";
  courses: CourseCatalogItem[];
};

export type CourseAnswer = {
  id: string;
  catalog_version: string;
  course_id: string;
  question_id: string;
  answer_language: "ENGLISH" | "CHINESE";
  status: "PROCESSING" | "SAVED" | "PROCESSING_FAILED" | "DISCARDED";
  response_duration_ms: number | null;
  audio_available: boolean;
  audio_retention_status: "RETAINED" | "PENDING_CLEANUP" | "EXPIRED" | "CLEANUP_FAILED";
  provider_error_code: string | null;
  failure_expires_at: string | null;
  created_at: string;
  saved_at: string | null;
  transcript: {
    source_language: "ENGLISH" | "CHINESE";
    transcript: string;
    organized_english: string | null;
    stt_provider: string;
    stt_model: string | null;
    created_at: string;
  } | null;
  feedback: {
    status: "NOT_REQUESTED" | "PENDING" | "READY" | "FAILED";
    summary: string | null;
    priority_changes: Record<string, unknown>[] | null;
  } | null;
};

export type CourseHistory = {
  course_id: string;
  question_id: string;
  count: number;
  answers: CourseAnswer[];
};

export type CourseHints = {
  static_answer_focus: string;
  keywords: string[];
  phrases: string[];
  sentence_frames: string[];
  personalization_note: string | null;
  prompt_version: string;
  provider_name: string;
  model_name: string | null;
};

export type CourseExpressionMaterials = {
  materials: {
    kind: "PHRASE" | "SENTENCE_FRAME" | "NATURAL_EXPRESSION" | "FACT_BASED_SENTENCE";
    text: string;
    source_excerpt: string | null;
  }[];
  personalization_note: string | null;
  prompt_version: string;
  provider_name: string;
  model_name: string | null;
};

export type CourseReferenceAnswer = {
  answer: string;
  personalization_note: string | null;
  prompt_version: string;
  provider_name: string;
  model_name: string | null;
};

async function catalogFetch<T>(path: string): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`);
  if (!response.ok) {
    const payload = (await response.json().catch(() => null)) as { detail?: string } | null;
    throw new Error(payload?.detail ?? `Request failed with status ${response.status}.`);
  }
  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}

async function authenticatedFetch<T>(token: string, path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: { Authorization: `Bearer ${token}`, ...init?.headers },
  });
  if (response.status === 401) clearAccessToken();
  if (!response.ok) {
    const payload = (await response.json().catch(() => null)) as { detail?: string } | null;
    throw new Error(payload?.detail ?? `Request failed with status ${response.status}.`);
  }
  return response.json() as Promise<T>;
}

export function getCourseCatalog(): Promise<CourseCatalog> {
  return catalogFetch<CourseCatalog>("/api/v1/courses");
}

export function getCourse(courseId: string): Promise<CourseCatalogItem> {
  return catalogFetch<CourseCatalogItem>(`/api/v1/courses/${encodeURIComponent(courseId)}`);
}

export function getCourseHistory(
  token: string,
  courseId: string,
  questionId: string,
): Promise<CourseHistory> {
  return authenticatedFetch<CourseHistory>(
    token,
    `/api/v1/courses/${encodeURIComponent(courseId)}/questions/${encodeURIComponent(questionId)}/history`,
  );
}

export function submitCourseAnswer(
  token: string,
  courseId: string,
  questionId: string,
  recording: Blob,
  durationMs: number,
  idempotencyKey: string,
): Promise<CourseAnswer> {
  const form = new FormData();
  form.append("idempotency_key", idempotencyKey);
  form.append("response_duration_ms", String(durationMs));
  form.append("recording", recording, "course-answer.webm");
  return authenticatedFetch<CourseAnswer>(
    token,
    `/api/v1/courses/${encodeURIComponent(courseId)}/questions/${encodeURIComponent(questionId)}/answers`,
    { method: "POST", body: form },
  );
}

function postQuestionSupport<T>(
  token: string,
  courseId: string,
  questionId: string,
  operation: "hints" | "expression-materials" | "reference-answer",
): Promise<T> {
  return authenticatedFetch<T>(
    token,
    `/api/v1/courses/${encodeURIComponent(courseId)}/questions/${encodeURIComponent(questionId)}/${operation}`,
    { method: "POST" },
  );
}

export function generateCourseHints(
  token: string,
  courseId: string,
  questionId: string,
): Promise<CourseHints> {
  return postQuestionSupport(token, courseId, questionId, "hints");
}

export function generateCourseExpressionMaterials(
  token: string,
  courseId: string,
  questionId: string,
): Promise<CourseExpressionMaterials> {
  return postQuestionSupport(token, courseId, questionId, "expression-materials");
}

export function generateCourseReferenceAnswer(
  token: string,
  courseId: string,
  questionId: string,
): Promise<CourseReferenceAnswer> {
  return postQuestionSupport(token, courseId, questionId, "reference-answer");
}

export function retryCourseAnswer(token: string, answerId: string): Promise<CourseAnswer> {
  return authenticatedFetch<CourseAnswer>(
    token,
    `/api/v1/course-answers/${encodeURIComponent(answerId)}/retry`,
    { method: "POST" },
  );
}

export function retryCourseFeedback(token: string, answerId: string): Promise<CourseAnswer> {
  return authenticatedFetch<CourseAnswer>(
    token,
    `/api/v1/course-answers/${encodeURIComponent(answerId)}/feedback/retry`,
    { method: "POST" },
  );
}

async function authenticatedAudio(token: string, path: string): Promise<Blob> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (response.status === 401) clearAccessToken();
  if (!response.ok) {
    const payload = (await response.json().catch(() => null)) as { detail?: string } | null;
    throw new Error(payload?.detail ?? `Request failed with status ${response.status}.`);
  }
  return response.blob();
}

export function getQuestionAudio(token: string, courseId: string, questionId: string): Promise<Blob> {
  return authenticatedAudio(
    token,
    `/api/v1/courses/${encodeURIComponent(courseId)}/questions/${encodeURIComponent(questionId)}/tts`,
  );
}

export function getCourseAnswerAudio(token: string, answerId: string): Promise<Blob> {
  return authenticatedAudio(token, `/api/v1/course-answers/${encodeURIComponent(answerId)}/audio`);
}

export function deleteCourseAnswer(token: string, answerId: string): Promise<void> {
  return authenticatedFetch<void>(token, `/api/v1/course-answers/${encodeURIComponent(answerId)}`, {
    method: "DELETE",
  });
}
