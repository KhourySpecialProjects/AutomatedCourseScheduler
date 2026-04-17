import { useEffect, useMemo, useState } from 'react';
import {
  getAutomatedCourseSchedulerAPI,
  type CourseCreate,
  type CourseResponse,
  type UserResponse,
} from '../api/generated';

// ── Shared form fields ─────────────────────────────────────────────────────────

interface CourseFormFields {
  subject: string;
  code: number;
  name: string;
  description: string;
  credits: number;
  priority: boolean;
}

function CourseForm({
  form,
  onChange,
  error,
  saving,
  submitLabel,
  onCancel,
}: {
  form: CourseFormFields;
  onChange: <K extends keyof CourseFormFields>(k: K, v: CourseFormFields[K]) => void;
  error: string | null;
  saving: boolean;
  submitLabel: string;
  onCancel: () => void;
}) {
  return (
    <>
      {error && (
        <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">
          {error}
        </div>
      )}

      <div className="space-y-4">
        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">Subject</label>
            <input
              required
              maxLength={10}
              value={form.subject}
              onChange={(e) => onChange('subject', e.target.value)}
              placeholder="CS"
              className="w-full text-sm border border-gray-200 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-burgundy-500"
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">Code</label>
            <input
              required
              type="number"
              value={form.code || ''}
              onChange={(e) => onChange('code', Number(e.target.value))}
              placeholder="4500"
              className="w-full text-sm border border-gray-200 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-burgundy-500"
            />
          </div>
        </div>

        <div>
          <label className="block text-xs font-medium text-gray-600 mb-1">Name</label>
          <input
            required
            value={form.name}
            onChange={(e) => onChange('name', e.target.value)}
            placeholder="Algorithms"
            className="w-full text-sm border border-gray-200 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-burgundy-500"
          />
        </div>

        <div>
          <label className="block text-xs font-medium text-gray-600 mb-1">Description</label>
          <textarea
            required
            rows={2}
            value={form.description}
            onChange={(e) => onChange('description', e.target.value)}
            placeholder="Course description…"
            className="w-full text-sm border border-gray-200 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-burgundy-500 resize-none"
          />
        </div>

        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">Credits</label>
            <input
              required
              type="number"
              min={0}
              value={form.credits || ''}
              onChange={(e) => onChange('credits', Number(e.target.value))}
              placeholder="4"
              className="w-full text-sm border border-gray-200 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-burgundy-500"
            />
          </div>
          <div className="flex items-end pb-2">
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={form.priority}
                onChange={(e) => onChange('priority', e.target.checked)}
                className="w-4 h-4 accent-burgundy-600"
              />
              <span className="text-sm text-gray-700">Priority</span>
            </label>
          </div>
        </div>

        <div className="flex justify-end gap-2 pt-2">
          <button
            type="button"
            onClick={onCancel}
            className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
          >
            Cancel
          </button>
          <button
            type="submit"
            disabled={saving}
            className="px-4 py-2 text-sm font-medium text-white bg-burgundy-600 rounded-lg hover:bg-burgundy-700 disabled:opacity-50 transition-colors"
          >
            {saving ? `${submitLabel.replace(/.$/, '…')}` : submitLabel}
          </button>
        </div>
      </div>
    </>
  );
}

// ── Create modal ───────────────────────────────────────────────────────────────

function CreateModal({
  onClose,
  onCreated,
}: {
  onClose: () => void;
  onCreated: (course: CourseResponse) => void;
}) {
  const [form, setForm] = useState<CourseCreate>({
    subject: '',
    code: 0,
    name: '',
    description: '',
    credits: 0,
    priority: false,
  });
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function onChange<K extends keyof CourseFormFields>(k: K, v: CourseFormFields[K]) {
    setForm((prev) => ({ ...prev, [k]: v }));
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    setError(null);
    try {
      const api = getAutomatedCourseSchedulerAPI();
      const created = await api.createCourseCoursesPost(form);
      onCreated(created);
    } catch (err: unknown) {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setError(typeof detail === 'string' ? detail : 'Failed to create course.');
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/30">
      <div className="bg-white rounded-2xl shadow-xl w-full max-w-md mx-4 p-6">
        <h2 className="text-base font-semibold text-gray-900 mb-4">Add Course</h2>
        <form onSubmit={handleSubmit}>
          <CourseForm
            form={form as CourseFormFields}
            onChange={onChange}
            error={error}
            saving={saving}
            submitLabel="Create Course"
            onCancel={onClose}
          />
        </form>
      </div>
    </div>
  );
}

// ── Edit modal ─────────────────────────────────────────────────────────────────

function EditModal({
  course,
  onClose,
  onSaved,
  onDeleted,
}: {
  course: CourseResponse;
  onClose: () => void;
  onSaved: (course: CourseResponse) => void;
  onDeleted: (courseId: number) => void;
}) {
  const [form, setForm] = useState<CourseFormFields>({
    subject: course.subject,
    code: course.code,
    name: course.name,
    description: course.description ?? '',
    credits: course.credits,
    priority: course.priority ?? false,
  });
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [confirmDelete, setConfirmDelete] = useState(false);
  const [deleting, setDeleting] = useState(false);

  function onChange<K extends keyof CourseFormFields>(k: K, v: CourseFormFields[K]) {
    setForm((prev) => ({ ...prev, [k]: v }));
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    setError(null);
    try {
      const api = getAutomatedCourseSchedulerAPI();
      const updated = await api.updateCourseCoursesCourseIdPatch(course.course_id, {
        subject: form.subject,
        code: form.code,
        name: form.name,
        description: form.description,
        credits: form.credits,
        priority: form.priority,
      });
      onSaved(updated);
    } catch (err: unknown) {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setError(typeof detail === 'string' ? detail : 'Failed to save changes.');
    } finally {
      setSaving(false);
    }
  }

  async function handleDelete() {
    setDeleting(true);
    try {
      await getAutomatedCourseSchedulerAPI().deleteCourseCoursesCourseIdDelete(course.course_id);
      onDeleted(course.course_id);
    } catch (err: unknown) {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setError(typeof detail === 'string' ? detail : 'Failed to delete course. It may still have sections assigned.');
      setConfirmDelete(false);
    } finally {
      setDeleting(false);
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/30">
      <div className="bg-white rounded-2xl shadow-xl w-full max-w-md mx-4 p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-base font-semibold text-gray-900">Edit Course</h2>
          {!confirmDelete ? (
            <button
              onClick={() => setConfirmDelete(true)}
              className="text-xs text-gray-400 hover:text-red-600 transition-colors"
            >
              Delete
            </button>
          ) : (
            <span className="inline-flex items-center gap-2">
              <span className="text-xs text-gray-500">Delete?</span>
              <button
                onClick={handleDelete}
                disabled={deleting}
                className="text-xs font-medium text-red-600 hover:text-red-800 disabled:opacity-50"
              >
                {deleting ? 'Deleting…' : 'Confirm'}
              </button>
              <button
                onClick={() => setConfirmDelete(false)}
                className="text-xs text-gray-400 hover:text-gray-600"
              >
                Cancel
              </button>
            </span>
          )}
        </div>
        <form onSubmit={handleSubmit}>
          <CourseForm
            form={form}
            onChange={onChange}
            error={error}
            saving={saving}
            submitLabel="Save Changes"
            onCancel={onClose}
          />
        </form>
      </div>
    </div>
  );
}

// ── Star icon ──────────────────────────────────────────────────────────────────

function StarIcon() {
  return (
    <svg className="w-3.5 h-3.5 text-amber-400 shrink-0" viewBox="0 0 20 20" fill="currentColor" aria-label="Priority">
      <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.286 3.957a1 1 0 00.95.69h4.162c.969 0 1.371 1.24.588 1.81l-3.37 2.448a1 1 0 00-.364 1.118l1.287 3.957c.3.921-.755 1.688-1.54 1.118l-3.37-2.448a1 1 0 00-1.175 0l-3.37 2.448c-.784.57-1.838-.197-1.539-1.118l1.287-3.957a1 1 0 00-.364-1.118L2.063 9.384c-.783-.57-.38-1.81.588-1.81h4.162a1 1 0 00.95-.69L9.049 2.927z" />
    </svg>
  );
}

// ── Main page ──────────────────────────────────────────────────────────────────

export default function Courses() {
  const [me, setMe] = useState<UserResponse | null>(null);
  const [meLoading, setMeLoading] = useState(true);

  const [courses, setCourses] = useState<CourseResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [search, setSearch] = useState('');
  const [showCreate, setShowCreate] = useState(false);
  const [editing, setEditing] = useState<CourseResponse | null>(null);

  const api = getAutomatedCourseSchedulerAPI();

  useEffect(() => {
    api.getMeApiUsersMeGet().then(setMe).catch(() => {}).finally(() => setMeLoading(false));
  }, []);

  useEffect(() => {
    api
      .getCoursesCoursesGet()
      .then((cs) => setCourses([...cs].sort((a, b) => a.name.localeCompare(b.name))))
      .catch(() => setError('Failed to load courses.'))
      .finally(() => setLoading(false));
  }, []);

  const filtered = useMemo(() => {
    const q = search.trim().toLowerCase();
    if (!q) return courses;
    return courses.filter(
      (c) =>
        c.name.toLowerCase().includes(q) ||
        `${c.subject} ${c.code}`.toLowerCase().includes(q) ||
        String(c.code).includes(q),
    );
  }, [courses, search]);

  function handleCreated(course: CourseResponse) {
    setCourses((prev) => [...prev, course].sort((a, b) => a.name.localeCompare(b.name)));
    setShowCreate(false);
  }

  function handleSaved(updated: CourseResponse) {
    setCourses((prev) =>
      [...prev.map((c) => (c.course_id === updated.course_id ? updated : c))].sort((a, b) =>
        a.name.localeCompare(b.name),
      ),
    );
    setEditing(null);
  }

  function handleDeleted(courseId: number) {
    setCourses((prev) => prev.filter((c) => c.course_id !== courseId));
    setEditing(null);
  }

  const isAdmin = me?.role === 'ADMIN';

  if (meLoading) {
    return (
      <div className="flex items-center gap-2 text-gray-400 text-sm">
        <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
        </svg>
        Loading…
      </div>
    );
  }

  return (
    <div className="max-w-3xl">
      {showCreate && (
        <CreateModal onClose={() => setShowCreate(false)} onCreated={handleCreated} />
      )}
      {editing && (
        <EditModal
          course={editing}
          onClose={() => setEditing(null)}
          onSaved={handleSaved}
          onDeleted={handleDeleted}
        />
      )}

      <div className="flex items-start justify-between gap-4 mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Courses</h1>
          <p className="mt-1 text-sm text-gray-500">All courses in the system.</p>
        </div>
        <div className="flex items-center gap-2 mt-1 shrink-0">
          <div className="relative">
            <svg className="absolute left-2.5 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400 pointer-events-none" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-4.35-4.35M17 11A6 6 0 115 11a6 6 0 0112 0z" />
            </svg>
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search name or code…"
              className="pl-8 pr-3 py-1.5 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-burgundy-500 w-48"
            />
          </div>
          {isAdmin && (
            <button
              onClick={() => setShowCreate(true)}
              className="flex items-center gap-1.5 px-3 py-1.5 text-sm font-medium bg-burgundy-600 text-white rounded-lg hover:bg-burgundy-700 transition-colors"
            >
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
              </svg>
              Add Course
            </button>
          )}
        </div>
      </div>

      {error && (
        <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">{error}</div>
      )}

      <div className="bg-white border border-gray-200 rounded-xl overflow-hidden">
        {loading ? (
          <div className="p-6 text-sm text-gray-400">Loading…</div>
        ) : courses.length === 0 ? (
          <div className="p-6 text-sm text-gray-400">No courses found.</div>
        ) : (
          <>
            <table className="min-w-full divide-y divide-gray-100">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-5 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Course</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Credits</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-100">
                {filtered.map((c) => (
                  <tr
                    key={c.course_id}
                    onClick={() => isAdmin && setEditing(c)}
                    className={`transition-colors ${isAdmin ? 'cursor-pointer hover:bg-burgundy-50/40' : 'hover:bg-gray-50'}`}
                  >
                    <td className="px-5 py-3">
                      <div className="flex items-center gap-1.5">
                        <span className="text-sm font-medium text-gray-900">{c.name}</span>
                        {c.priority && <StarIcon />}
                      </div>
                      <div className="text-xs text-gray-400">{c.subject} {c.code}</div>
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-700">{c.credits} cr</td>
                  </tr>
                ))}
              </tbody>
            </table>
            <div className="px-5 py-3 border-t border-gray-100 text-xs text-gray-400">
              {filtered.length}{filtered.length !== courses.length && ` of ${courses.length}`} course{courses.length !== 1 ? 's' : ''}
            </div>
          </>
        )}
      </div>
    </div>
  );
}
