import { useEffect, useMemo, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import ScheduleSectionRowView from '../components/ScheduleSectionRowView';
import { useScheduleWebSocket, type WsStatus } from '../hooks/useScheduleWebSocket';
import { getAutomatedCourseSchedulerAPI, type ScheduleResponse, type UserResponse } from '../api/generated';
import FacultyLinkTools from '../components/FacultyLinkTools';

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

function ScheduleView({ scheduleId, readOnly }: { scheduleId: number; readOnly?: boolean }) {
  const { sections, locks, loading, status } = useScheduleWebSocket(scheduleId);
  const [viewMode, setViewMode] = useState<ViewMode>('table');
  const [selectedCourseCount, setSelectedCourseCount] = useState(0);
  const [schedule, setSchedule] = useState<ScheduleResponse | null>(null);
  const [campusName, setCampusName] = useState<string | null>(null);
  const [me, setMe] = useState<UserResponse | null>(null);
  const [meError, setMeError] = useState<string | null>(null);
  const [forceFacultyView, setForceFacultyView] = useState(false);
  const [invitePanel, setInvitePanel] = useState<string | null>(null);

  useEffect(() => {
    const api = getAutomatedCourseSchedulerAPI();
    api.getMeApiUsersMeGet()
      .then((u) => setMe(u))
      .catch((err: unknown) => {
        const status = (err as { response?: { status?: number } })?.response?.status;
        if (status === 403) {
          setMeError('Your Auth0 account is not linked to a DB user yet. Ask an admin to invite you or run bootstrap_admin.py.');
        } else {
          setMeError('Could not load your user profile.');
        }
      });
    api.getScheduleSchedulesScheduleIdGet(scheduleId)
      .then((s) => {
        setSchedule(s);
        // Resolve campus name for drawer filtering
        return api.getAllCampusesCampusesGet().then((campuses) => {
          const match = campuses.find((c) => c.campus_id === s.campus);
          if (match) setCampusName(match.name);
        });
      })
      .catch(() => {});
  }, [scheduleId]);

  const scheduleName = schedule?.name ?? `Schedule ${scheduleId}`;
  const isAdmin = me?.role === 'ADMIN';
  const effectiveReadOnly = Boolean(readOnly) || forceFacultyView || (!isAdmin && !readOnly);
  const modeLabel = effectiveReadOnly ? 'Faculty view' : isAdmin ? 'Admin view' : 'Viewer';

  const toggleLabel = useMemo(() => (effectiveReadOnly ? 'Switch to admin view' : 'Switch to faculty view'), [effectiveReadOnly]);
  const calendarAllowed = selectedCourseCount > 0 && selectedCourseCount < 5;

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
                effectiveReadOnly
                  ? 'bg-slate-100 text-slate-700 border-slate-200'
                  : isAdmin
                    ? 'bg-indigo-50 text-indigo-700 border-indigo-200'
                    : 'bg-gray-100 text-gray-700 border-gray-200'
              }`}
              title={modeLabel}
            >
              {modeLabel}
            </span>
          </div>
          {schedule && (
            <p className="mt-0.5 text-sm text-gray-500">Semester {schedule.semester_id}</p>
          )}
          {meError && (
            <div className="mt-3 text-sm text-amber-800 bg-amber-50 border border-amber-200 rounded-lg px-3 py-2">
              {meError}
            </div>
          )}
        </div>

        <div className="flex items-center gap-3">
          {!readOnly && (
            <>
              <button
                onClick={() => setForceFacultyView((v) => !v)}
                className="px-3 py-2 text-xs font-medium bg-white border border-gray-200 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
                title="Temporary toggle for testing; invite link will eventually land here"
              >
                {toggleLabel}
              </button>
              <FacultyLinkTools
                disabled={!isAdmin}
                onGenerate={(facultyNuid) => {
                  if (!facultyNuid) {
                    setInvitePanel('Pick a faculty member first.');
                    return;
                  }
                  setInvitePanel('To be implemented');
                }}
              />
            </>
          )}

          {/* View toggle */}
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
            title={!calendarAllowed ? 'Calendar view supports up to 4 selected courses.' : 'Calendar'}
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

      {!readOnly && invitePanel && (
        <div className="mb-4 bg-white border border-gray-200 rounded-xl p-4">
          <div className="flex items-start justify-between gap-3">
            <div className="min-w-0">
              <div className="text-xs font-semibold text-gray-500 uppercase tracking-wider">Faculty link</div>
              <div className="mt-1 text-sm text-gray-700">{invitePanel}</div>
            </div>
            <button
              onClick={() => setInvitePanel(null)}
              className="px-3 py-2 text-xs font-medium bg-white border border-gray-200 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
            >
              Dismiss
            </button>
          </div>
        </div>
      )}

      {loading && (
        <div className="flex items-center gap-2 text-gray-400 text-sm mt-8">
          <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
          </svg>
          Connecting…
        </div>
      )}

      {!loading && (
        <ScheduleSectionRowView
          sections={sections}
          scheduleId={scheduleId}
          locks={locks}
          campusName={campusName}
          readOnly={effectiveReadOnly}
          viewMode={effectiveViewMode}
          onSelectedCourseCountChange={setSelectedCourseCount}
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
