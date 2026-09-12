import { CourseDetailPage } from "@/components/course-core/course-detail";

export default async function CoursePage({
  params,
}: {
  params: Promise<{ courseId: string }>;
}) {
  const { courseId } = await params;
  return <CourseDetailPage courseId={courseId} />;
}
