import { useEffect, useMemo, useState } from 'react';
import {
  getAutomatedCourseSchedulerAPI,
  type CourseResponse,
  type ScheduleResponse,
  type SectionRichResponse,
} from '../api/generated';
import { formatCourseLabel } from '../utils/courseFormat';

export default function Courses() {
  const [schedules, setSchedules] = useState<ScheduleResponse[]>([]);
  const [scheduleId, setScheduleId] = useState<number | null>(null);
  const [sections, setSections] = useState<SectionRichResponse[]>([]);
  const [catalogCourses, setCatalogCourses] = useState<CourseResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const api = getAutomatedCourseSchedulerAPI();
    api
      .getSchedulesSchedulesGet()
      .then((ss) => {
        setSchedules(ss);
        const first = ss[0]?.schedule_id ?? null;
        setScheduleId(first);
      })
      .catch(() => setError('Failed to load schedules.'))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    const api = getAutomatedCourseSchedulerAPI();
    api
      .getCoursesCoursesGet()
      .then((cs) => setCatalogCourses(cs))
      .catch(() => {});
  }, []);

  useEffect(() => {
    if (!scheduleId) return;
    const api = getAutomatedCourseSchedulerAPI();
    api
      .getScheduleSectionsRichSchedulesScheduleIdSectionsRichGet(scheduleId)
      .then((result) => { setSections(result); setError(null); })
      .catch(() => setError('Failed to load schedule courses.'));
  }, [scheduleId]);

  const courses = useMemo(() => {
    const byId = new Map<
      number,
      { course_id: number; name: string; credits: number; subject?: string; code?: number }
    >();
    const catalogById = new Map<number, CourseResponse>();
    for (const c of catalogCourses) catalogById.set(c.course_id, c);

    for (const s of sections) {
      if (!byId.has(s.course.course_id)) {
        const cat = catalogById.get(s.course.course_id);
        byId.set(s.course.course_id, {
          course_id: s.course.course_id,
          name: cat?.name ?? s.course.name,
          credits: s.course.credits,
          subject: cat?.subject,
          code: cat?.code,
        });
      }
    }
    return [...byId.values()].sort((a, b) => {
      const la = formatCourseLabel(a);
      const lb = formatCourseLabel(b);
      return la.localeCompare(lb) || a.name.localeCompare(b.name);
    });
  }, [sections, catalogCourses]);

  return (
    <div className="max-w-2xl">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Courses</h1>
        <p className="mt-1 text-sm text-gray-500">Courses included in a schedule.</p>
      </div>

      {error && (
        <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">{error}</div>
      )}

      <div className="mb-4 flex items-center gap-3">
        <label className="text-xs font-semibold text-gray-500 uppercase tracking-wider">Schedule</label>
        <select
          value={scheduleId ?? ''}
          onChange={(e) => setScheduleId(e.target.value ? Number(e.target.value) : null)}
          className="text-sm border border-gray-200 rounded-lg px-3 py-2 bg-white focus:outline-none focus:ring-2 focus:ring-burgundy-500"
        >
          {schedules.map((s) => (
            <option key={s.schedule_id} value={s.schedule_id}>
              {s.name ?? `Schedule ${s.schedule_id}`}
            </option>
          ))}
        </select>
        <span className="text-xs text-gray-400 ml-auto">{courses.length} course{courses.length === 1 ? '' : 's'}</span>
      </div>

      <div className="bg-white border border-gray-200 rounded-xl overflow-hidden">
        {loading ? (
          <div className="p-6 text-sm text-gray-400">Loading…</div>
        ) : courses.length === 0 ? (
          <div className="p-6 text-sm text-gray-400">No courses found for this schedule.</div>
        ) : (
          <ul className="divide-y divide-gray-100">
            {courses.map((c) => (
              <li key={c.course_id} className="px-5 py-3 flex items-center justify-between gap-4">
                <span className="text-sm font-medium text-gray-900 truncate">
                  {formatCourseLabel(c)}
                </span>
                <span className="text-xs text-gray-500 shrink-0 truncate max-w-[16rem]">
                  {c.name}
                </span>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}
