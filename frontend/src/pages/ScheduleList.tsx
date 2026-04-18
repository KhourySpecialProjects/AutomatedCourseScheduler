import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { getAutomatedCourseSchedulerAPI, type ScheduleResponse } from '../api/generated';

function ScheduleCard({ schedule, onClick }: { schedule: ScheduleResponse; onClick: () => void }) {
  return (
    <button
      onClick={onClick}
      className="w-full text-left bg-white border border-gray-200 rounded-xl p-5 hover:border-burgundy-300 hover:shadow-sm transition-all group"
    >
      <div className="flex items-start justify-between gap-4">
        <div className="min-w-0">
          <h3 className="text-base font-semibold text-gray-900 truncate">
            {schedule.name}
          </h3>
          <p className="mt-0.5 text-sm text-gray-500">Semester {schedule.semester_id}</p>
          <div className="mt-3 flex items-center gap-2">
            {schedule.draft ? (
              <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-amber-50 text-amber-700 border border-amber-200">
                <span className="w-1.5 h-1.5 rounded-full bg-amber-400" />
                Draft
              </span>
            ) : (
              <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-green-50 text-green-700 border border-green-200">
                <span className="w-1.5 h-1.5 rounded-full bg-green-500" />
                Published
              </span>
            )}
            {schedule.active && (
              <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-burgundy-50 text-burgundy-700 border border-burgundy-200">
                Active
              </span>
            )}
          </div>
        </div>
        <svg
          className="w-5 h-5 text-gray-300 group-hover:text-burgundy-400 shrink-0 mt-0.5 transition-colors"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
        </svg>
      </div>
    </button>
  );
}

export default function ScheduleList() {
  const [schedules, setSchedules] = useState<ScheduleResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();

  useEffect(() => {
    const { getSchedulesSchedulesGet } = getAutomatedCourseSchedulerAPI();
    getSchedulesSchedulesGet()
      .then((data) => {
        setSchedules(data);
        setLoading(false);
      })
      .catch(() => {
        setError('Failed to load schedules.');
        setLoading(false);
      });
  }, []);

  return (
    <div className="max-w-2xl">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Schedules</h1>
        <p className="mt-1 text-sm text-gray-500">Select a schedule to view and edit its sections.</p>
      </div>

      {loading && (
        <div className="flex items-center gap-2 text-gray-400 text-sm mt-8">
          <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
          </svg>
          Loading schedules…
        </div>
      )}

      {error && (
        <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">
          {error}
        </div>
      )}

      {!loading && !error && schedules.length === 0 && (
        <div className="mt-8 text-center text-sm text-gray-400">
          No schedules found.
        </div>
      )}

      {!loading && !error && schedules.length > 0 && (
        <div className="space-y-3">
          {schedules.map((s) => (
            <ScheduleCard
              key={s.schedule_id}
              schedule={s}
              onClick={() => navigate(`/schedules/${s.schedule_id}`)}
            />
          ))}
        </div>
      )}
    </div>
  );
}
