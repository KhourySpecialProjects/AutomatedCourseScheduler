export type CourseLike = {
  name: string;
  subject?: string;
  code?: number;
};

export function formatCourseCode(course: CourseLike): string | null {
  const subject = course.subject?.trim();
  const code = course.code;
  if (!subject || code == null || Number.isNaN(Number(code))) return null;
  return `${subject}${code}`;
}

export function formatCourseLabel(course: CourseLike): string {
  const code = formatCourseCode(course);
  return code ? `${code} - ${course.name}` : course.name;
}

