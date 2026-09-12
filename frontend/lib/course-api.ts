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

async function catalogFetch<T>(path: string): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`);
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
