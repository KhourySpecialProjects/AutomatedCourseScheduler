import { useParams } from 'react-router-dom';
import ScheduleSectionRowView from '../components/ScheduleSectionRowView';
import { useScheduleSections } from '../hooks/useScheduleSections';

function ScheduleView({ scheduleId }: { scheduleId: number }) {
  const { sections, loading, error } = useScheduleSections(scheduleId);

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900">Schedule</h1>
        <p className="mt-1 text-sm text-gray-500">
          Click any row for details · Hover a professor for preferences and load
        </p>
      </div>

      {loading && (
        <div className="flex items-center gap-2 text-gray-500 mt-8">
          <svg className="w-5 h-5 animate-spin" fill="none" viewBox="0 0 24 24">
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
  const { scheduleId } = useParams<{ scheduleId?: string }>();
  // FLAG: hardcoded schedule ID, in prod first grab all schedules, then get specific sections using schedule_id
  const id = scheduleId ? parseInt(scheduleId, 10) : 1;

  return <ScheduleView scheduleId={id} />;
}
