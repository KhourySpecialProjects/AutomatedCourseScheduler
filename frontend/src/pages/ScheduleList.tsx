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
  onUpdate,
  onDelete,
}: {
  schedule: ScheduleResponse;
  onClick: () => void;
  isAdmin: boolean;
  onUpdate: (id: number, data: { name?: string; draft?: boolean }) => Promise<void>;
  onDelete: (id: number) => void;
}) {
  const [editing, setEditing] = useState(false);
  const [editName, setEditName] = useState(schedule.name);
  const [editDraft, setEditDraft] = useState(schedule.draft);
  const [saving, setSaving] = useState(false);
  const [confirmDelete, setConfirmDelete] = useState(false);

  function openEdit(e: React.MouseEvent) {
    e.stopPropagation();
    setEditName(schedule.name);
    setEditDraft(schedule.draft);
    setConfirmDelete(false);
    setEditing(true);
  }

  async function handleSave() {
    const changes: { name?: string; draft?: boolean } = {};
    if (editName.trim() !== schedule.name) changes.name = editName.trim();
    if (editDraft !== schedule.draft) changes.draft = editDraft;
    if (Object.keys(changes).length === 0) {
      setEditing(false);
      return;
    }
    setSaving(true);
    try {
      await onUpdate(schedule.schedule_id, changes);
      setEditing(false);
    } finally {
      setSaving(false);
    }
  }

  if (editing) {
    return (
      <div className="bg-white border border-indigo-200 rounded-xl p-5 space-y-4">
        {/* Name */}
        <div>
          <label className="block text-xs font-medium text-gray-500 mb-1">Name</label>
          <input
            type="text"
            value={editName}
            onChange={(e) => setEditName(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
          />
        </div>

        {/* Draft toggle */}
        <div className="flex items-center gap-3">
          <span className="text-sm text-gray-700">Status</span>
          <button
            type="button"
            onClick={() => setEditDraft((d) => !d)}
            className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium transition-colors ${
              editDraft
                ? 'bg-amber-50 text-amber-700 border border-amber-200 hover:bg-amber-100'
                : 'bg-green-50 text-green-700 border border-green-200 hover:bg-green-100'
            }`}
          >
            <span className={`w-1.5 h-1.5 rounded-full ${editDraft ? 'bg-amber-400' : 'bg-green-500'}`} />
            {editDraft ? 'Draft' : 'Published'}
          </button>
        </div>

        {/* Actions */}
        <div className="flex items-center justify-between pt-2 border-t border-gray-100">
          <div>
            {!confirmDelete ? (
              <button
                onClick={() => setConfirmDelete(true)}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-red-600 bg-red-50 border border-red-200 rounded-lg hover:bg-red-100 transition-colors"
              >
                <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                </svg>
                Delete schedule
              </button>
            ) : (
              <div className="flex items-center gap-1.5">
                <span className="text-xs text-red-600 font-medium">Are you sure?</span>
                <button
                  onClick={() => onDelete(schedule.schedule_id)}
                  className="px-2 py-1 text-xs font-medium text-white bg-red-600 rounded-md hover:bg-red-700 transition-colors"
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
          <div className="flex items-center gap-2">
            <button
              onClick={() => setEditing(false)}
              className="px-3 py-1.5 text-xs font-medium text-gray-600 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors"
            >
              Cancel
            </button>
            <button
              onClick={handleSave}
              disabled={saving || !editName.trim()}
              className="px-3 py-1.5 text-xs font-medium text-white bg-indigo-600 rounded-lg hover:bg-indigo-700 disabled:opacity-50 transition-colors"
            >
              {saving ? 'Saving...' : 'Save'}
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="relative group/card">
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
        <button
          onClick={openEdit}
          className="absolute top-4 right-12 p-1.5 rounded-lg text-gray-300 opacity-0 group-hover/card:opacity-100 hover:text-indigo-500 hover:bg-indigo-50 transition-all"
          title="Edit schedule"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" />
          </svg>
        </button>
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

type Step = 'upload' | 'info' | 'generate';

const STEP_LABELS: Record<Step, string> = {
  upload: 'Upload CSV Files',
  info: 'Schedule Details',
  generate: 'Generate Schedule',
};

function StepIndicator({ current }: { current: Step }) {
  const steps: Step[] = ['upload', 'info', 'generate'];
  const idx = steps.indexOf(current);
  return (
    <div className="flex items-center gap-2 mb-5">
      {steps.map((s, i) => (
        <div key={s} className="flex items-center gap-2">
          <div
            className={`flex items-center justify-center w-6 h-6 rounded-full text-xs font-semibold ${
              i < idx
                ? 'bg-indigo-600 text-white'
                : i === idx
                  ? 'bg-indigo-100 text-indigo-700 ring-2 ring-indigo-600'
                  : 'bg-gray-100 text-gray-400'
            }`}
          >
            {i < idx ? (
              <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M5 13l4 4L19 7" />
              </svg>
            ) : (
              i + 1
            )}
          </div>
          <span className={`text-xs font-medium ${i === idx ? 'text-gray-900' : 'text-gray-400'}`}>
            {STEP_LABELS[s]}
          </span>
          {i < steps.length - 1 && <div className="w-6 h-px bg-gray-200" />}
        </div>
      ))}
    </div>
  );
}

function CreateScheduleModal({ onClose, onCreated }: { onClose: () => void; onCreated: (s: ScheduleResponse) => void }) {
  const [step, setStep] = useState<Step>('upload');
  const [createdSchedule, setCreatedSchedule] = useState<ScheduleResponse | null>(null);

  /* ---------- step 1: csv uploads ---------- */
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

  /* ---------- step 2: schedule info ---------- */
  const [name, setName] = useState('');
  const [semesterId, setSemesterId] = useState<number | ''>('');
  const [campusId, setCampusId] = useState<number | ''>('');
  const [semesters, setSemesters] = useState<SemesterResponse[]>([]);
  const [campuses, setCampuses] = useState<CampusResponse[]>([]);
  const [creating, setCreating] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  /* ---------- step 3: generate ---------- */
  const [generating, setGenerating] = useState(false);
  const [generateDone, setGenerateDone] = useState(false);
  const [generateError, setGenerateError] = useState<string | null>(null);

  // fetch semesters + campuses on mount
  useEffect(() => {
    const api = getAutomatedCourseSchedulerAPI();
    api.getAllSemestersSemestersGet().then(setSemesters).catch(() => {});
    api.getAllCampusesCampusesGet().then(setCampuses).catch(() => {});
  }, []);

  async function doUpload(kind: UploadKind, file: File) {
    setUploadError(null);
    setUploadBusy(kind);
    try {
      const formData = new FormData();
      formData.append('file', file);
      const res = await axiosInstance<UploadResponse>({
        url: uploadUrl(kind),
        method: 'POST',
        data: formData,
      });
      setUploadResults((prev) => ({ ...prev, [kind]: res }));
    } catch (e: unknown) {
      const detail =
        (e as { response?: { data?: { detail?: unknown } } })?.response?.data?.detail ??
        (e as { message?: unknown })?.message;
      const message = Array.isArray(detail)
        ? (detail as unknown[]).map(String).join('\n')
        : typeof detail === 'string'
          ? detail
          : 'Upload failed. Please check your CSV and try again.';
      setUploadError(message);
    } finally {
      setUploadBusy(null);
    }
  }

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
      setCreatedSchedule(created);
      onCreated(created);
      setStep('generate');
    } catch (e: unknown) {
      const detail =
        (e as { response?: { data?: { detail?: unknown } } })?.response?.data?.detail ??
        (e as { message?: unknown })?.message;
      setFormError(typeof detail === 'string' ? detail : 'Failed to create schedule.');
    } finally {
      setCreating(false);
    }
  }

  async function handleGenerate() {
    if (!createdSchedule) return;
    setGenerateError(null);
    setGenerating(true);
    try {
      await axiosInstance({
        url: `/schedules/${createdSchedule.schedule_id}/generate`,
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        data: { parameters: {} },
      });
      setGenerateDone(true);
    } catch (e: unknown) {
      const detail =
        (e as { response?: { data?: { detail?: unknown } } })?.response?.data?.detail ??
        (e as { message?: unknown })?.message;
      setGenerateError(typeof detail === 'string' ? detail : 'Failed to start schedule generation.');
    } finally {
      setGenerating(false);
    }
  }

  return (
    // backdrop
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/30" onClick={onClose}>
      {/* modal */}
      <div
        className="bg-white rounded-2xl shadow-xl w-full max-w-2xl mx-4 overflow-hidden"
        onClick={(e) => e.stopPropagation()}
      >
        {/* header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-100">
          <h2 className="text-lg font-semibold text-gray-900">New Schedule</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600 transition-colors">
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* body */}
        <div className="px-6 py-5">
          <StepIndicator current={step} />

          {/* Step 1: CSV uploads */}
          {step === 'upload' && (
            <div className="space-y-4">
              <p className="text-sm text-gray-500">Upload all three CSV files before creating the schedule.</p>

              {uploadError && (
                <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700 whitespace-pre-wrap">{uploadError}</div>
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

          {/* Step 2: Schedule info */}
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

          {/* Step 3: Generate */}
          {step === 'generate' && (
            <div className="space-y-4 text-center py-4">
              {generateError && (
                <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700 text-left">{generateError}</div>
              )}

              {!generateDone ? (
                <>
                  <div className="text-sm text-gray-600">
                    Schedule <span className="font-semibold text-gray-900">{createdSchedule?.name}</span> has been created. Run the algorithm to populate it with sections.
                  </div>
                  <button
                    onClick={handleGenerate}
                    disabled={generating}
                    className="inline-flex items-center gap-2 px-5 py-2.5 text-sm font-medium text-white bg-indigo-600 rounded-lg hover:bg-indigo-700 disabled:opacity-50 transition-colors"
                  >
                    {generating ? (
                      <>
                        <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
                        </svg>
                        Generating...
                      </>
                    ) : (
                      <>
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                        </svg>
                        Run Algorithm
                      </>
                    )}
                  </button>
                </>
              ) : (
                <div className="space-y-2">
                  <svg className="w-10 h-10 text-green-500 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  <div className="text-sm text-gray-600">Algorithm started. Sections are being generated in the background.</div>
                </div>
              )}
            </div>
          )}
        </div>

        {/* footer */}
        <div className="flex items-center justify-end gap-3 px-6 py-4 border-t border-gray-100 bg-gray-50">
          {step === 'upload' && (
            <>
              <button
                onClick={onClose}
                className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={() => setStep('info')}
                disabled={!allUploaded}
                className="px-4 py-2 text-sm font-medium text-white bg-indigo-600 rounded-lg hover:bg-indigo-700 disabled:opacity-50 transition-colors"
              >
                Next
              </button>
            </>
          )}
          {step === 'info' && (
            <>
              <button
                onClick={() => setStep('upload')}
                className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
              >
                Back
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
          {step === 'generate' && (
            <button
              onClick={onClose}
              className="px-4 py-2 text-sm font-medium text-white bg-indigo-600 rounded-lg hover:bg-indigo-700 transition-colors"
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

  async function handleUpdate(scheduleId: number, data: { name?: string; draft?: boolean }) {
    const api = getAutomatedCourseSchedulerAPI();
    const updated = await api.updateScheduleSchedulesScheduleIdPut(scheduleId, data);
    setSchedules((prev) => prev.map((s) => (s.schedule_id === scheduleId ? updated : s)));
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
              onUpdate={handleUpdate}
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
