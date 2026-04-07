import { useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import ScheduleSectionRowView from '../components/ScheduleSectionRowView';
import { useScheduleSections } from '../hooks/useScheduleSections';
import { getAutomatedCourseSchedulerAPI, type ScheduleResponse } from '../api/generated';

type ViewMode = 'table' | 'calendar';

function TableIcon({ active }: { active: boolean }) {
  return (
    <svg
      className={`w-4 h-4 ${active ? 'text-indigo-600' : 'text-gray-400'}`}
      fill="none"
      stroke="currentColor"
      viewBox="0 0 24 24"
    >
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.75} d="M3 10h18M3 6h18M3 14h18M3 18h18" />
    </svg>
  );
}

function CalendarIcon({ active }: { active: boolean }) {
  return (
    <svg
      className={`w-4 h-4 ${active ? 'text-indigo-600' : 'text-gray-400'}`}
      fill="none"
      stroke="currentColor"
      viewBox="0 0 24 24"
    >
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.75} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
    </svg>
  );
}

function ScheduleView({ scheduleId }: { scheduleId: number }) {
  const { sections, loading, error } = useScheduleSections(scheduleId);
  const [viewMode] = useState<ViewMode>('table');
  const [schedule, setSchedule] = useState<ScheduleResponse | null>(null);

  useEffect(() => {
    const { getScheduleSchedulesScheduleIdGet } = getAutomatedCourseSchedulerAPI();
    getScheduleSchedulesScheduleIdGet(scheduleId)
      .then(setSchedule)
      .catch(() => {});
  }, [scheduleId]);

  const scheduleName = schedule?.name ?? `Schedule ${scheduleId}`;

  return (
    <div>
      {/* Breadcrumb */}
      <nav className="flex items-center gap-1.5 text-sm text-gray-400 mb-4">
        <Link to="/schedules" className="hover:text-gray-600 transition-colors">
          Schedules
        </Link>
        <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
        </svg>
        <span className="text-gray-700 font-medium">{scheduleName}</span>
      </nav>

      {/* Header row */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">{scheduleName}</h1>
          {schedule && (
            <p className="mt-0.5 text-sm text-gray-500">Semester {schedule.semester_id}</p>
          )}
        </div>

        {/* View toggle */}
        <div className="flex items-center gap-1 bg-gray-100 rounded-lg p-1">
          <button
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium transition-colors ${
              viewMode === 'table'
                ? 'bg-white text-gray-900 shadow-sm'
                : 'text-gray-500 hover:text-gray-700'
            }`}
          >
            <TableIcon active={viewMode === 'table'} />
            Table
          </button>
          <button
            disabled
            title="Calendar view coming soon"
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium text-gray-400 cursor-not-allowed opacity-60"
          >
            <CalendarIcon active={false} />
            Calendar
          </button>
        </div>
      </div>

      {loading && (
        <div className="flex items-center gap-2 text-gray-400 text-sm mt-8">
          <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
          </svg>
          Loading sections…
        </div>
      )}

      {error && (
        <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">
          {error}
        </div>
      )}

      {!loading && !error && (
        <ScheduleSectionRowView sections={sections} scheduleId={scheduleId} />
      )}
    </div>
  );
}

export default function Schedules() {
  const { scheduleId } = useParams<{ scheduleId: string }>();
  const id = parseInt(scheduleId ?? '', 10);

  if (isNaN(id)) {
    return <div className="text-sm text-red-600 mt-4">Invalid schedule ID.</div>;
  }

  return <ScheduleView scheduleId={id} />;
}
