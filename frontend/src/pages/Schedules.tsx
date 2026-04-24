import { useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import ScheduleSectionRowView from '../components/ScheduleSectionRowView';
import AlgorithmWarningsBanner from '../components/AlgorithmWarningsBanner';
import { useScheduleData, type WsStatus } from '../hooks/useScheduleData';
import { getAutomatedCourseSchedulerAPI, type ScheduleResponse } from '../api/generated';
import { useUser } from '../context/UserContext';
import { downloadScheduleCsv } from '../utils/exportCsv';

type ViewMode = 'table' | 'calendar';
type SchedulePersona = 'faculty' | 'admin';

function LiveIndicator({ status }: { status: WsStatus }) {
  const config = {
    connected: { dot: 'bg-green-500', text: 'text-green-700', label: 'Live' },
    connecting: { dot: 'bg-amber-400 animate-pulse', text: 'text-amber-700', label: 'Connecting…' },
    disconnected: { dot: 'bg-red-400', text: 'text-red-700', label: 'Disconnected' },
  }[status];

  return (
    <span className={`inline-flex items-center gap-1.5 text-xs font-medium ${config.text}`}>
      <span className={`w-1.5 h-1.5 rounded-full shrink-0 ${config.dot}`} />
      {config.label}
    </span>
  );
}

function TableIcon({ active }: { active: boolean }) {
  return (
    <svg
      className={`w-4 h-4 ${active ? 'text-burgundy-600' : 'text-gray-400'}`}
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
      className={`w-4 h-4 ${active ? 'text-burgundy-600' : 'text-gray-400'}`}
      fill="none"
      stroke="currentColor"
      viewBox="0 0 24 24"
    >
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.75} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
    </svg>
  );
}

function ScheduleView({ scheduleId, readOnly }: { scheduleId: number; readOnly?: boolean }) {
  const { sections, locks, warnings, loading, status } = useScheduleData(scheduleId);
  const [viewMode, setViewMode] = useState<ViewMode>('table');
  const [schedulePersona, setSchedulePersona] = useState<SchedulePersona>('admin');
  const [selectedCourseCount, setSelectedCourseCount] = useState(0);
  const [selectedInstructorCount, setSelectedInstructorCount] = useState(0);
  const { me, meError } = useUser();
  const [schedule, setSchedule] = useState<ScheduleResponse | null>(null);
  const [campusName, setCampusName] = useState<string | null>(null);
  const [semesterLabel, setSemesterLabel] = useState<string | null>(null);

  useEffect(() => {
    const api = getAutomatedCourseSchedulerAPI();
    api.getScheduleSchedulesScheduleIdGet(scheduleId)
      .then((s) => {
        setSchedule(s);
        api.getSemesterSemestersSemesterIdGet(s.semester_id)
          .then((sem) => setSemesterLabel(`${sem.season} ${sem.year}`))
          .catch(() => {});
        // Resolve campus name for drawer filtering
        return api.getAllCampusesCampusesGet().then((campuses) => {
          const match = campuses.find((c) => c.campus_id === s.campus);
          if (match) setCampusName(match.name);
        });
      })
      .catch(() => {});
  }, [scheduleId]);

  async function handleExportCsv() {
    try {
      await downloadScheduleCsv(scheduleId);
    } catch {
      alert('Failed to export CSV. Please try again.');
    }
  }

  const scheduleName = schedule?.name ?? `Schedule ${scheduleId}`;
  const apiIsAdmin = me?.role === 'ADMIN';
  const userRoleLoaded = me != null || meError != null;
  const canTogglePersona = Boolean(apiIsAdmin) && !readOnly;
  const sectionsEditable = canTogglePersona && schedulePersona === 'admin';
  const facultyUiMode = Boolean(readOnly) || !apiIsAdmin || (canTogglePersona && schedulePersona === 'faculty');
  const modeLabel = facultyUiMode ? 'Faculty view' : 'Admin view';
  const calendarAllowed =
    (selectedInstructorCount > 0 && selectedInstructorCount <= 4) ||
    (selectedCourseCount > 0 && selectedCourseCount <= 4);

  const effectiveViewMode: ViewMode = !calendarAllowed && viewMode === 'calendar' ? 'table' : viewMode;

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
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold text-gray-900">{scheduleName}</h1>
            <LiveIndicator status={status} />
            <span
              className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium border ${
                facultyUiMode
                  ? 'bg-slate-100 text-slate-700 border-slate-200'
                  : apiIsAdmin
                    ? 'bg-burgundy-50 text-burgundy-700 border-burgundy-200'
                    : 'bg-gray-100 text-gray-700 border-gray-200'
              }`}
              title={modeLabel}
            >
              {modeLabel}
            </span>
          </div>
          {schedule && semesterLabel && (
            <p className="mt-0.5 text-sm text-gray-500">{semesterLabel}</p>
          )}
          {meError && (
            <div className="mt-3 text-sm text-amber-800 bg-amber-50 border border-amber-200 rounded-lg px-3 py-2">
              {meError}
            </div>
          )}
        </div>

        <div className="flex items-center gap-3">
          {schedule && !schedule.draft && (
            <button
              type="button"
              onClick={() => { void handleExportCsv(); }}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium bg-burgundy-600 text-white hover:bg-burgundy-700 transition-colors"
            >
              <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
              </svg>
              Export CSV
            </button>
          )}
          {canTogglePersona && (
            <div className="flex items-center gap-1 bg-gray-100 rounded-lg p-1" role="group" aria-label="Schedule mode">
              <button
                type="button"
                onClick={() => setSchedulePersona('faculty')}
                className={`px-3 py-1.5 rounded-md text-xs font-medium transition-colors ${
                  schedulePersona === 'faculty'
                    ? 'bg-white text-gray-900 shadow-sm'
                    : 'text-gray-500 hover:text-gray-700'
                }`}
              >
                Faculty
              </button>
              <button
                type="button"
                onClick={() => setSchedulePersona('admin')}
                className={`px-3 py-1.5 rounded-md text-xs font-medium transition-colors ${
                  schedulePersona === 'admin'
                    ? 'bg-white text-gray-900 shadow-sm'
                    : 'text-gray-500 hover:text-gray-700'
                }`}
              >
                Admin
              </button>
            </div>
          )}
          {/* Table / Calendar toggle */}
          <div className="flex items-center gap-1 bg-gray-100 rounded-lg p-1">
            <button
              type="button"
              onClick={() => setViewMode('table')}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium transition-colors ${
                effectiveViewMode === 'table'
                  ? 'bg-white text-gray-900 shadow-sm'
                  : 'text-gray-500 hover:text-gray-700'
              }`}
            >
              <TableIcon active={effectiveViewMode === 'table'} />
              Table
            </button>
            <button
              type="button"
              disabled={!calendarAllowed}
              onClick={() => setViewMode('calendar')}
              title={
                !calendarAllowed
                  ? 'To use Calendar view, choose 4 or fewer professors OR 4 or fewer courses.'
                  : 'Calendar'
              }
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium transition-colors ${
                effectiveViewMode === 'calendar'
                  ? 'bg-white text-gray-900 shadow-sm'
                  : calendarAllowed
                    ? 'text-gray-500 hover:text-gray-700'
                    : 'text-gray-400 cursor-not-allowed opacity-60'
              }`}
            >
              <CalendarIcon active={effectiveViewMode === 'calendar'} />
              Calendar
            </button>
          </div>
        </div>
      </div>

      {loading && (
        <div className="flex items-center gap-2 text-gray-400 text-sm mt-8">
          <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
          </svg>
          Connecting…
        </div>
      )}

      {!loading && !facultyUiMode && (
        <AlgorithmWarningsBanner
          warnings={warnings.filter((w) => w.section_id == null && !w.dismissed)}
        />
      )}

      {!loading && (
        <ScheduleSectionRowView
          sections={sections}
          scheduleId={scheduleId}
          locks={locks}
          warnings={warnings}
          campusName={campusName}
          campusId={schedule?.campus ?? null}
          viewMode={effectiveViewMode}
          onSelectedCourseCountChange={setSelectedCourseCount}
          onSelectedInstructorCountChange={setSelectedInstructorCount}
          isAdmin={sectionsEditable}
          userRoleLoaded={userRoleLoaded}
        />
      )}
    </div>
  );
}

export default function Schedules({ readOnly }: { readOnly?: boolean }) {
  const { scheduleId } = useParams<{ scheduleId: string }>();
  const id = parseInt(scheduleId ?? '', 10);

  if (isNaN(id)) {
    return <div className="text-sm text-red-600 mt-4">Invalid schedule ID.</div>;
  }

  return <ScheduleView scheduleId={id} readOnly={readOnly} />;
}
