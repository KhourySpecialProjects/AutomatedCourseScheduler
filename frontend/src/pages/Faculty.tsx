import { useEffect, useMemo, useState } from 'react';
import { getAutomatedCourseSchedulerAPI, type ScheduleResponse, type SectionRichResponse } from '../api/generated';
import SearchableSelect, { type SelectOption } from '../components/SearchableSelect';

type BucketKey = 'first' | 'second' | 'third' | 'none';

function bucketLabel(k: BucketKey) {
  switch (k) {
    case 'first':
      return '1st choice';
    case 'second':
      return '2nd choice';
    case 'third':
      return '3rd choice';
    case 'none':
      return 'No preference';
  }
}

function bucketStyle(k: BucketKey) {
  switch (k) {
    case 'first':
      return 'bg-green-600';
    case 'second':
      return 'bg-amber-500';
    case 'third':
      return 'bg-red-500';
    case 'none':
      return 'bg-slate-300';
  }
}

function preferenceToBucket(pref?: string): BucketKey {
  if (pref === 'Eager to teach') return 'first';
  if (pref === 'Willing to teach') return 'second';
  if (pref === 'Not my cup of tea') return 'third';
  return 'none';
}

function Bar({ label, value, total, color }: { label: string; value: number; total: number; color: string }) {
  const pct = total > 0 ? Math.round((value / total) * 100) : 0;
  return (
    <div>
      <div className="flex items-center justify-between text-sm mb-1">
        <span className="text-gray-700">{label}</span>
        <span className="text-gray-500">{value} ({pct}%)</span>
      </div>
      <div className="h-2 rounded-full bg-gray-100 overflow-hidden">
        <div className={`h-full ${color}`} style={{ width: `${pct}%` }} />
      </div>
    </div>
  );
}

export default function Faculty() {
  const [schedules, setSchedules] = useState<ScheduleResponse[]>([]);
  const [selectedScheduleId, setSelectedScheduleId] = useState<number | null>(null);
  const [sections, setSections] = useState<SectionRichResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const scheduleOptions: SelectOption<number>[] = useMemo(
    () =>
      schedules.map((s) => ({
        value: s.schedule_id,
        label: s.name,
        sublabel: `Semester ${s.semester_id}`,
      })),
    [schedules],
  );

  useEffect(() => {
    const api = getAutomatedCourseSchedulerAPI();
    api.getSchedulesSchedulesGet()
      .then((data) => {
        setSchedules(data);
        if (data.length > 0) {
          setSelectedScheduleId((prev) => prev ?? data[0].schedule_id);
        }
      })
      .catch(() => setError('Failed to load schedules.'));
  }, []);

  useEffect(() => {
    if (!selectedScheduleId) return;
    queueMicrotask(() => {
      setLoading(true);
      setError(null);
    });
    const api = getAutomatedCourseSchedulerAPI();
    api.getScheduleSectionsRichSchedulesScheduleIdSectionsRichGet(selectedScheduleId)
      .then((secs) => {
        setSections(secs);
        setLoading(false);
      })
      .catch(() => {
        setError('Failed to load schedule sections.');
        setLoading(false);
      });
  }, [selectedScheduleId]);

  const counts = useMemo(() => {
    const c: Record<BucketKey, number> = { first: 0, second: 0, third: 0, none: 0 };
    for (const s of sections) {
      for (const inst of s.instructors) {
        const pref = inst.course_preferences.find((cp) => cp.course_id === s.course.course_id)?.preference;
        c[preferenceToBucket(pref)] += 1;
      }
    }
    return c;
  }, [sections]);

  const totalAssignments = counts.first + counts.second + counts.third + counts.none;

  return (
    <div className="max-w-3xl">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Faculty</h1>
        <p className="mt-1 text-sm text-gray-500">
          Preference satisfaction overview (based on instructor course preferences).
        </p>
      </div>

      <div className="bg-white border border-gray-200 rounded-xl p-5">
        <div className="flex items-center justify-between gap-4 mb-5">
          <div>
            <div className="text-sm font-semibold text-gray-900">Histogram</div>
            <div className="text-xs text-gray-500">
              Counts instructor-to-section assignments by preference bucket.
            </div>
          </div>
          <div className="w-72">
            <SearchableSelect
              options={scheduleOptions}
              value={selectedScheduleId}
              onChange={setSelectedScheduleId}
              placeholder="Select schedule…"
              disabled={schedules.length === 0}
            />
          </div>
        </div>

        {loading && <div className="text-sm text-gray-500">Loading…</div>}
        {error && (
          <div className="mt-2 p-4 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">
            {error}
          </div>
        )}

        {!loading && !error && (
          <div className="space-y-4">
            <Bar label={bucketLabel('first')} value={counts.first} total={totalAssignments} color={bucketStyle('first')} />
            <Bar label={bucketLabel('second')} value={counts.second} total={totalAssignments} color={bucketStyle('second')} />
            <Bar label={bucketLabel('third')} value={counts.third} total={totalAssignments} color={bucketStyle('third')} />
            <Bar label={bucketLabel('none')} value={counts.none} total={totalAssignments} color={bucketStyle('none')} />
          </div>
        )}
      </div>
    </div>
  );
}
