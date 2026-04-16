import { useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  getAutomatedCourseSchedulerAPI,
  type CampusResponse,
  type ScheduleResponse,
  type SemesterResponse,
  type UploadResponse,
} from '../api/generated';
import { axiosInstance } from '../api/axiosInstance';

/* ------------------------------------------------------------------ */
/*  Schedule card                                                      */
/* ------------------------------------------------------------------ */

function ScheduleCard({
  schedule,
  onClick,
  isAdmin,
  onDelete,
}: {
  schedule: ScheduleResponse;
  onClick: () => void;
  isAdmin: boolean;
  onDelete: (id: number) => void;
}) {
  const [confirmDelete, setConfirmDelete] = useState(false);

  return (
    <div className="relative">
      <button
        onClick={onClick}
        className="w-full text-left bg-white border border-gray-200 rounded-xl p-5 hover:border-indigo-300 hover:shadow-sm transition-all group"
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
                <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-indigo-50 text-indigo-700 border border-indigo-200">
                  Active
                </span>
              )}
            </div>
          </div>
          <svg
            className="w-5 h-5 text-gray-300 group-hover:text-indigo-400 shrink-0 mt-0.5 transition-colors"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
          </svg>
        </div>
      </button>

      {isAdmin && (
        <div className="absolute top-4 right-12">
          {!confirmDelete ? (
            <button
              onClick={(e) => {
                e.stopPropagation();
                setConfirmDelete(true);
              }}
              className="p-1.5 rounded-lg text-gray-300 hover:text-red-500 hover:bg-red-50 transition-colors"
              title="Delete schedule"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
              </svg>
            </button>
          ) : (
            <div className="flex items-center gap-1.5" onClick={(e) => e.stopPropagation()}>
              <span className="text-xs text-red-500 font-medium whitespace-nowrap">Are you sure?</span>
              <button
                onClick={() => onDelete(schedule.schedule_id)}
                className="px-2 py-1 text-xs font-medium text-white bg-red-500 rounded-md hover:bg-red-700 transition-colors"
              >
                Yes
              </button>
              <button
                onClick={() => setConfirmDelete(false)}
                className="px-2 py-1 text-xs font-medium text-gray-600 bg-gray-100 rounded-md hover:bg-gray-200 transition-colors"
              >
                No
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

/* ------------------------------------------------------------------ */
/*  CSV upload helpers (reused from old Upload page)                    */
/* ------------------------------------------------------------------ */

type UploadKind = 'courses' | 'faculty-preferences' | 'time-preferences';

const UPLOAD_KINDS: { kind: UploadKind; label: string; description: string }[] = [
  { kind: 'courses', label: 'Courses offered', description: 'Upload the course catalog / offerings CSV.' },
  { kind: 'faculty-preferences', label: 'Course preferences', description: 'Upload faculty course preference rankings CSV.' },
  { kind: 'time-preferences', label: 'Time preferences', description: 'Upload faculty time preference rankings CSV.' },
];

function uploadUrl(kind: UploadKind): string {
  return kind === 'courses'
    ? '/upload/courses'
    : kind === 'faculty-preferences'
      ? '/upload/faculty-preferences'
      : '/upload/time-preferences';
}

/* ------------------------------------------------------------------ */
/*  Create-schedule modal                                              */
/* ------------------------------------------------------------------ */

type Step = 'info' | 'upload';

function CreateScheduleModal({ onClose, onCreated }: { onClose: () => void; onCreated: (s: ScheduleResponse) => void }) {
  const [step, setStep] = useState<Step>('info');

  /* ---------- step 1: schedule info ---------- */
  const [name, setName] = useState('');
  const [semesterId, setSemesterId] = useState<number | ''>('');
  const [campusId, setCampusId] = useState<number | ''>('');
  const [semesters, setSemesters] = useState<SemesterResponse[]>([]);
  const [campuses, setCampuses] = useState<CampusResponse[]>([]);
  const [creating, setCreating] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  /* ---------- step 2: csv uploads ---------- */
  const [uploadResults, setUploadResults] = useState<Record<UploadKind, UploadResponse | null>>({
    courses: null,
    'faculty-preferences': null,
    'time-preferences': null,
  });
  const [uploadBusy, setUploadBusy] = useState<UploadKind | null>(null);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const coursesRef = useRef<HTMLInputElement>(null);
  const prefRef = useRef<HTMLInputElement>(null);
  const timeRef = useRef<HTMLInputElement>(null);
  const refFor = (kind: UploadKind) =>
    kind === 'courses' ? coursesRef : kind === 'faculty-preferences' ? prefRef : timeRef;

  const allUploaded = UPLOAD_KINDS.every((u) => uploadResults[u.kind]?.status === 'success');

  // fetch semesters + campuses on mount
  useEffect(() => {
    const api = getAutomatedCourseSchedulerAPI();
    api.getAllSemestersSemestersGet().then(setSemesters).catch(() => {});
    api.getAllCampusesCampusesGet().then(setCampuses).catch(() => {});
  }, []);

  async function handleCreate() {
    if (!name.trim() || semesterId === '' || campusId === '') {
      setFormError('All fields are required.');
      return;
    }
    setFormError(null);
    setCreating(true);
    try {
      const api = getAutomatedCourseSchedulerAPI();
      const created = await api.createScheduleSchedulesPost({
        name: name.trim(),
        semester_id: semesterId as number,
        campus: campusId as number,
      });
      onCreated(created);
      setStep('upload');
    } catch (e: unknown) {
      const detail =
        (e as { response?: { data?: { detail?: unknown } } })?.response?.data?.detail ??
        (e as { message?: unknown })?.message;
      setFormError(typeof detail === 'string' ? detail : 'Failed to create schedule.');
    } finally {
      setCreating(false);
    }
  }

  async function doUpload(kind: UploadKind, file: File) {
    setUploadError(null);
    setUploadBusy(kind);
    try {
      const formData = new FormData();
      formData.append('file', file);
      const res = await axiosInstance<UploadResponse>({
        url: uploadUrl(kind),
        method: 'POST',
        headers: { 'Content-Type': 'multipart/form-data' },
        data: formData,
      });
      setUploadResults((prev) => ({ ...prev, [kind]: res }));
    } catch (e: unknown) {
      const detail =
        (e as { response?: { data?: { detail?: unknown } } })?.response?.data?.detail ??
        (e as { message?: unknown })?.message;
      setUploadError(typeof detail === 'string' ? detail : 'Upload failed. Please check your CSV and try again.');
    } finally {
      setUploadBusy(null);
    }
  }

  return (
    // backdrop
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/30" onClick={onClose}>
      {/* modal */}
      <div
        className="bg-white rounded-2xl shadow-xl w-full max-w-lg mx-4 overflow-hidden"
        onClick={(e) => e.stopPropagation()}
      >
        {/* header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-100">
          <h2 className="text-lg font-semibold text-gray-900">
            {step === 'info' ? 'New Schedule' : 'Upload CSV Files'}
          </h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600 transition-colors">
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* body */}
        <div className="px-6 py-5">
          {step === 'info' && (
            <div className="space-y-4">
              {formError && (
                <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">{formError}</div>
              )}

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Schedule name</label>
                <input
                  type="text"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="e.g. Fall 2026 CS Draft"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Semester</label>
                <select
                  value={semesterId}
                  onChange={(e) => setSemesterId(e.target.value ? Number(e.target.value) : '')}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                >
                  <option value="">Select a semester</option>
                  {semesters.map((s) => (
                    <option key={s.semester_id} value={s.semester_id}>
                      {s.season} {s.year}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Campus</label>
                <select
                  value={campusId}
                  onChange={(e) => setCampusId(e.target.value ? Number(e.target.value) : '')}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                >
                  <option value="">Select a campus</option>
                  {campuses.map((c) => (
                    <option key={c.campus_id} value={c.campus_id}>
                      {c.name}
                    </option>
                  ))}
                </select>
              </div>
            </div>
          )}

          {step === 'upload' && (
            <div className="space-y-4">
              <p className="text-sm text-gray-500">Upload all three CSV files for this schedule.</p>

              {uploadError && (
                <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">{uploadError}</div>
              )}

              {UPLOAD_KINDS.map((u) => {
                const result = uploadResults[u.kind];
                const isDone = result?.status === 'success';
                return (
                  <div key={u.kind} className="flex items-center justify-between gap-4">
                    <div className="min-w-0">
                      <div className="text-sm font-semibold text-gray-900 flex items-center gap-2">
                        {u.label}
                        {isDone && (
                          <svg className="w-4 h-4 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                          </svg>
                        )}
                      </div>
                      <div className="text-xs text-gray-500">{u.description}</div>
                      {result?.errors?.length ? (
                        <ul className="mt-1 list-disc list-inside text-xs text-amber-700 space-y-0.5">
                          {result.errors.slice(0, 4).map((e, i) => (
                            <li key={i}>{e}</li>
                          ))}
                          {result.errors.length > 4 && <li>...and {result.errors.length - 4} more</li>}
                        </ul>
                      ) : null}
                    </div>
                    <div className="shrink-0">
                      <input
                        ref={refFor(u.kind)}
                        type="file"
                        accept=".csv,text/csv"
                        className="hidden"
                        onChange={(e) => {
                          const file = e.target.files?.[0];
                          if (!file) return;
                          void doUpload(u.kind, file);
                          e.currentTarget.value = '';
                        }}
                      />
                      <button
                        type="button"
                        disabled={uploadBusy !== null}
                        onClick={() => refFor(u.kind).current?.click()}
                        className={`px-3 py-2 text-xs font-medium rounded-lg transition-colors disabled:opacity-50 ${
                          isDone
                            ? 'bg-green-50 text-green-700 border border-green-200 hover:bg-green-100'
                            : 'bg-indigo-600 text-white hover:bg-indigo-700'
                        }`}
                      >
                        {uploadBusy === u.kind ? 'Uploading...' : isDone ? 'Re-upload' : 'Upload CSV'}
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* footer */}
        <div className="flex items-center justify-end gap-3 px-6 py-4 border-t border-gray-100 bg-gray-50">
          {step === 'info' && (
            <>
              <button
                onClick={onClose}
                className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleCreate}
                disabled={creating}
                className="px-4 py-2 text-sm font-medium text-white bg-indigo-600 rounded-lg hover:bg-indigo-700 disabled:opacity-50 transition-colors"
              >
                {creating ? 'Creating...' : 'Create Schedule'}
              </button>
            </>
          )}
          {step === 'upload' && (
            <button
              onClick={onClose}
              disabled={!allUploaded}
              className="px-4 py-2 text-sm font-medium text-white bg-indigo-600 rounded-lg hover:bg-indigo-700 disabled:opacity-50 transition-colors"
            >
              Done
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/*  Main page                                                          */
/* ------------------------------------------------------------------ */

export default function ScheduleList() {
  const [schedules, setSchedules] = useState<ScheduleResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showCreate, setShowCreate] = useState(false);
  const [isAdmin, setIsAdmin] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    const api = getAutomatedCourseSchedulerAPI();
    api.getSchedulesSchedulesGet()
      .then((data) => {
        setSchedules(data);
        setLoading(false);
      })
      .catch(() => {
        setError('Failed to load schedules.');
        setLoading(false);
      });
    api.getMeApiUsersMeGet()
      .then((me) => setIsAdmin(me.role === 'ADMIN'))
      .catch(() => {});
  }, []);

  function handleCreated(s: ScheduleResponse) {
    setSchedules((prev) => [s, ...prev]);
  }

  async function handleDelete(scheduleId: number) {
    try {
      const api = getAutomatedCourseSchedulerAPI();
      await api.deleteScheduleSchedulesScheduleIdDelete(scheduleId);
      setSchedules((prev) => prev.filter((s) => s.schedule_id !== scheduleId));
    } catch {
      setError('Failed to delete schedule.');
    }
  }

  return (
    <div className="max-w-2xl">
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Schedules</h1>
          <p className="mt-1 text-sm text-gray-500">Select a schedule to view and edit its sections.</p>
        </div>
        {isAdmin && (
          <button
            onClick={() => setShowCreate(true)}
            className="inline-flex items-center gap-1.5 px-4 py-2 text-sm font-medium text-white bg-indigo-600 rounded-lg hover:bg-indigo-700 transition-colors"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
            </svg>
            New Schedule
          </button>
        )}
      </div>

      {loading && (
        <div className="flex items-center gap-2 text-gray-400 text-sm mt-8">
          <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
          </svg>
          Loading schedules...
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
              isAdmin={isAdmin}
              onClick={() => navigate(`/schedules/${s.schedule_id}`)}
              onDelete={handleDelete}
            />
          ))}
        </div>
      )}

      {showCreate && (
        <CreateScheduleModal
          onClose={() => setShowCreate(false)}
          onCreated={handleCreated}
        />
      )}
    </div>
  );
}
