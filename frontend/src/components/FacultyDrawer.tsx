import { useEffect, useMemo, useState } from 'react';
import {
  getAutomatedCourseSchedulerAPI,
  type CampusResponse,
  type SectionRichResponse,
  type TimeBlockInfo,
} from '../api/generated';
import SectionCalendarGrid from './SectionCalendarGrid';
import SearchableSelect, { type SelectOption } from './SearchableSelect';

// The generated FacultyResponse type uses stale PascalCase field names.
// These local interfaces match what the backend actually serializes.
export interface FacultyRecord {
  nuid: number;
  first_name: string | null;
  last_name: string | null;
  email: string | null;
  title: string | null;
  campus: number | null;
  active: boolean | null;
  maxLoad: number | null;
}

interface FacultyProfile {
  nuid: number;
  needsAdminReview?: boolean;
  course_preferences: Array<{ course_id: number; course_name: string; preference: string }>;
  meeting_preferences: Array<{ time_block_id: number; preference: string }>;
}

interface Props {
  mode: 'create' | 'edit';
  faculty: FacultyRecord | null;
  sections: SectionRichResponse[];
  campuses: CampusResponse[];
  scheduleId: number | null;
  onClose: () => void;
  onSaved: (f: FacultyRecord) => void;
  onDeleted: (nuid: number) => void;
}

function Label({ children }: { children: React.ReactNode }) {
  return (
    <label className="block text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1.5">
      {children}
    </label>
  );
}

function SectionHeader({ children }: { children: React.ReactNode }) {
  return (
    <div className="text-xs font-semibold text-gray-500 uppercase tracking-wider">{children}</div>
  );
}

const PREF_STYLES: Record<string, string> = {
  'Eager to teach': 'bg-green-100 text-green-800',
  'Ready to teach': 'bg-blue-100 text-blue-800',
  'Willing to teach': 'bg-amber-100 text-amber-800',
  'Not my cup of tea': 'bg-red-100 text-red-800',
};

function PreferenceBadge({ preference }: { preference: string }) {
  const cls = PREF_STYLES[preference] ?? 'bg-gray-100 text-gray-700';
  return (
    <span className={`shrink-0 inline-block px-2 py-0.5 text-xs font-medium rounded-full ${cls}`}>
      {preference}
    </span>
  );
}

const INPUT_CLS =
  'w-full text-sm border border-gray-200 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-500';

export default function FacultyDrawer({
  mode,
  faculty,
  sections,
  campuses,
  scheduleId,
  onClose,
  onSaved,
  onDeleted,
}: Props) {
  const isEdit = mode === 'edit' && faculty !== null;

  // Form state
  const [nuid, setNuid] = useState<number | ''>('');
  const [firstName, setFirstName] = useState(faculty?.first_name ?? '');
  const [lastName, setLastName] = useState(faculty?.last_name ?? '');
  const [email, setEmail] = useState(faculty?.email ?? '');
  const [phone, setPhone] = useState('');
  const [titleVal, setTitleVal] = useState(faculty?.title ?? '');
  const [campusId, setCampusId] = useState<number | null>(faculty?.campus ?? null);
  const [maxLoad, setMaxLoad] = useState<number | ''>(faculty?.maxLoad ?? 3);
  const [active, setActive] = useState(faculty?.active ?? true);

  // Preferences profile (edit mode only)
  const [profile, setProfile] = useState<FacultyProfile | null>(null);
  const [loadingProfile, setLoadingProfile] = useState(isEdit);

  // UI state
  const [sectionView, setSectionView] = useState<'list' | 'calendar'>('list');
  const [saving, setSaving] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [confirmingDelete, setConfirmingDelete] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Build time-block lookup from the sections prop for readable meeting preference labels.
  const timeBlockMap = useMemo(() => {
    const map = new Map<number, TimeBlockInfo>();
    for (const s of sections) {
      if (!map.has(s.time_block.time_block_id)) map.set(s.time_block.time_block_id, s.time_block);
    }
    return map;
  }, [sections]);

  // Sections assigned to this faculty member in the selected schedule.
  const assignedSections = useMemo(
    () => (faculty ? sections.filter((s) => s.instructors.some((i) => i.nuid === faculty.nuid)) : []),
    [sections, faculty],
  );

  // Fetch preferences profile in edit mode.
  useEffect(() => {
    if (!isEdit || !faculty) return;
    let cancelled = false;
    getAutomatedCourseSchedulerAPI()
      .getFacultyProfileFacultyNuidGet(faculty.nuid)
      .then((data) => {
        if (!cancelled) setProfile(data as unknown as FacultyProfile);
      })
      .catch(() => {})
      .finally(() => { if (!cancelled) setLoadingProfile(false); });
    return () => { cancelled = true; };
  }, [isEdit, faculty]);

  const campusOptions: SelectOption<number>[] = campuses.map((c) => ({
    value: c.campus_id,
    label: c.name,
  }));

  async function handleSave() {
    setError(null);
    if (!firstName.trim() || !lastName.trim() || !email.trim()) {
      setError('First name, last name, and email are required.');
      return;
    }
    if (campusId === null) {
      setError('Campus is required.');
      return;
    }
    if (maxLoad === '' || Number(maxLoad) < 1) {
      setError('Max load must be at least 1.');
      return;
    }

    setSaving(true);
    const api = getAutomatedCourseSchedulerAPI();
    try {
      // Cast through unknown to bypass stale generated type constraints.
      const patchFn = api.updateFacultyFacultyNuidPatch as unknown as (
        nuid: number,
        body: object,
      ) => Promise<FacultyRecord>;
      const createFn = api.createFacultyFacultyPost as unknown as (
        body: object,
      ) => Promise<FacultyRecord>;

      const baseBody = {
        first_name: firstName.trim(),
        last_name: lastName.trim(),
        email: email.trim(),
        campus: campusId,
        phone_number: phone.trim() || null,
        title: titleVal.trim() || null,
        active,
        max_load: Number(maxLoad),
      };

      let result: FacultyRecord;
      if (isEdit && faculty) {
        result = await patchFn(faculty.nuid, baseBody);
      } else {
        if (nuid === '') {
          setError('NUID is required.');
          setSaving(false);
          return;
        }
        result = await createFn({ nuid: Number(nuid), ...baseBody });
      }
      onSaved(result);
    } catch (err: unknown) {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setError(detail ?? 'Failed to save. Please try again.');
      setSaving(false);
    }
  }

  async function handleDelete() {
    if (!faculty) return;
    setDeleting(true);
    try {
      await getAutomatedCourseSchedulerAPI().deleteFacultyFacultyNuidDelete(faculty.nuid);
      onDeleted(faculty.nuid);
    } catch {
      setError('Failed to delete faculty member. Please try again.');
      setDeleting(false);
      setConfirmingDelete(false);
    }
  }

  const drawerWidth = sectionView === 'calendar' && isEdit ? 'w-[56rem]' : 'w-[28rem]';
  const drawerTitle = isEdit
    ? `${faculty.first_name ?? ''} ${faculty.last_name ?? ''}`.trim() || 'Edit Faculty'
    : 'Add Faculty';

  return (
    <>
      {/* Backdrop */}
      <div className="fixed inset-0 bg-black/20 z-40" onClick={onClose} />

      {/* Drawer */}
      <div
        className={`fixed right-0 top-0 h-full ${drawerWidth} bg-white shadow-xl z-50 flex flex-col`}
        style={{ transition: 'width 200ms ease' }}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-5 border-b border-gray-100 shrink-0">
          <div>
            <h2 className="text-base font-semibold text-gray-900">{drawerTitle}</h2>
            {isEdit && !faculty.active && (
              <span className="text-xs text-gray-400 italic">Inactive</span>
            )}
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 p-1 rounded transition-colors"
            aria-label="Close"
          >
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Body */}
        <div className="flex-1 overflow-y-auto p-6 space-y-7">

          {/* ── Section A: Edit form ── */}
          <div className="space-y-4">
            <SectionHeader>Details</SectionHeader>

            {/* NUID (create only) */}
            {!isEdit && (
              <div>
                <Label>NUID</Label>
                <input
                  type="number"
                  min={1}
                  value={nuid}
                  onChange={(e) => setNuid(e.target.value ? Number(e.target.value) : '')}
                  className={INPUT_CLS}
                  placeholder="e.g. 123456789"
                />
              </div>
            )}

            {/* Name row */}
            <div className="grid grid-cols-2 gap-3">
              <div>
                <Label>First Name</Label>
                <input
                  type="text"
                  value={firstName}
                  onChange={(e) => setFirstName(e.target.value)}
                  className={INPUT_CLS}
                />
              </div>
              <div>
                <Label>Last Name</Label>
                <input
                  type="text"
                  value={lastName}
                  onChange={(e) => setLastName(e.target.value)}
                  className={INPUT_CLS}
                />
              </div>
            </div>

            {/* Email */}
            <div>
              <Label>Email</Label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className={INPUT_CLS}
              />
            </div>

            {/* Phone */}
            <div>
              <Label>Phone (optional)</Label>
              <input
                type="text"
                value={phone}
                onChange={(e) => setPhone(e.target.value)}
                className={INPUT_CLS}
                placeholder="e.g. 617-555-0100"
              />
            </div>

            {/* Title */}
            <div>
              <Label>Title (optional)</Label>
              <input
                type="text"
                value={titleVal}
                onChange={(e) => setTitleVal(e.target.value)}
                className={INPUT_CLS}
                placeholder="e.g. Associate Professor"
              />
            </div>

            {/* Campus + Max Load */}
            <div className="grid grid-cols-2 gap-3">
              <div>
                <Label>Campus</Label>
                <SearchableSelect
                  options={campusOptions}
                  value={campusId}
                  onChange={setCampusId}
                  placeholder="Select campus…"
                />
              </div>
              <div>
                <Label>Max Load</Label>
                <input
                  type="number"
                  min={1}
                  max={10}
                  value={maxLoad}
                  onChange={(e) => setMaxLoad(e.target.value ? Number(e.target.value) : '')}
                  className={INPUT_CLS}
                />
              </div>
            </div>

            {/* Active */}
            <div className="flex items-center gap-2.5">
              <input
                id="faculty-active"
                type="checkbox"
                checked={active}
                onChange={(e) => setActive(e.target.checked)}
                className="h-4 w-4 rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
              />
              <label
                htmlFor="faculty-active"
                className="text-sm font-medium text-gray-700 cursor-pointer select-none"
              >
                Active
              </label>
            </div>
          </div>

          {/* ── Section B: Assigned sections ── */}
          {isEdit && (
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <SectionHeader>
                  Assigned Sections
                  {scheduleId !== null && ` (${assignedSections.length})`}
                </SectionHeader>
                <div className="flex gap-1">
                  {(['list', 'calendar'] as const).map((v) => (
                    <button
                      key={v}
                      onClick={() => setSectionView(v)}
                      className={`px-2.5 py-1 text-xs font-medium rounded transition-colors ${
                        sectionView === v
                          ? 'bg-indigo-600 text-white'
                          : 'bg-white border border-gray-200 text-gray-600 hover:bg-gray-50'
                      }`}
                    >
                      {v === 'list' ? 'List' : 'Calendar'}
                    </button>
                  ))}
                </div>
              </div>

              {scheduleId === null ? (
                <p className="text-sm text-gray-400">
                  Select a schedule above to view assigned sections.
                </p>
              ) : sectionView === 'list' ? (
                assignedSections.length === 0 ? (
                  <p className="text-sm text-gray-400">
                    No sections assigned in this schedule.
                  </p>
                ) : (
                  <div className="overflow-hidden rounded-lg border border-gray-200">
                    <table className="min-w-full divide-y divide-gray-100">
                      <tbody className="bg-white divide-y divide-gray-100">
                        {assignedSections.map((s) => (
                          <tr key={s.section_id}>
                            <td className="px-3 py-2 text-sm font-medium text-gray-900 truncate max-w-[10rem]">
                              {s.course.name}
                            </td>
                            <td className="px-3 py-2 text-sm text-gray-500 whitespace-nowrap">
                              §{s.section_number}
                            </td>
                            <td className="px-3 py-2 text-sm text-gray-500 whitespace-nowrap">
                              {s.time_block.days}&nbsp;{s.time_block.start_time}–{s.time_block.end_time}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )
              ) : (
                <SectionCalendarGrid
                  sections={sections}
                  displaySections={assignedSections}
                  emptyMessage="No sections assigned in this schedule."
                />
              )}
            </div>
          )}

          {/* ── Section C: Preferences (read-only) ── */}
          {isEdit && (
            <div className="space-y-4">
              <SectionHeader>Preferences</SectionHeader>

              {loadingProfile ? (
                <div className="flex items-center gap-2 text-sm text-gray-400">
                  <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
                  </svg>
                  Loading…
                </div>
              ) : (
                <>
                  {profile?.needsAdminReview && (
                    <div className="p-3 bg-amber-50 border border-amber-200 rounded-lg text-sm text-amber-800">
                      No preferences on record. Update via the CSV upload flow.
                    </div>
                  )}

                  {/* Course preferences */}
                  <div>
                    <div className="text-xs font-medium text-gray-500 mb-2">Courses</div>
                    {!profile?.course_preferences.length ? (
                      <p className="text-sm text-gray-400">None recorded.</p>
                    ) : (
                      <div className="space-y-1.5">
                        {profile.course_preferences.map((cp) => (
                          <div key={cp.course_id} className="flex items-center justify-between gap-2">
                            <span className="text-sm text-gray-700 truncate">{cp.course_name}</span>
                            <PreferenceBadge preference={cp.preference} />
                          </div>
                        ))}
                      </div>
                    )}
                  </div>

                  {/* Meeting preferences */}
                  <div>
                    <div className="text-xs font-medium text-gray-500 mb-2">Time Slots</div>
                    {!profile?.meeting_preferences.length ? (
                      <p className="text-sm text-gray-400">None recorded.</p>
                    ) : (
                      <div className="space-y-1.5">
                        {profile.meeting_preferences.map((mp, i) => {
                          const tb = timeBlockMap.get(mp.time_block_id);
                          const label = tb
                            ? `${tb.days} ${tb.start_time}–${tb.end_time}`
                            : `Block #${mp.time_block_id}`;
                          return (
                            <div key={i} className="flex items-center justify-between gap-2">
                              <span className="text-sm text-gray-700 whitespace-nowrap">{label}</span>
                              <PreferenceBadge preference={mp.preference} />
                            </div>
                          );
                        })}
                      </div>
                    )}
                  </div>
                </>
              )}
            </div>
          )}

          {/* Error */}
          {error && (
            <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">
              {error}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="border-t border-gray-100 px-6 py-4 flex items-center justify-between gap-3 shrink-0">
          {confirmingDelete ? (
            <>
              <span className="text-sm text-red-600">Delete this faculty member?</span>
              <div className="flex items-center gap-2 ml-auto">
                <button
                  onClick={() => setConfirmingDelete(false)}
                  disabled={deleting}
                  className="px-4 py-2 text-sm font-medium text-gray-600 hover:text-gray-900 disabled:opacity-50 transition-colors"
                >
                  Cancel
                </button>
                <button
                  onClick={handleDelete}
                  disabled={deleting}
                  className="px-4 py-2 text-sm font-medium bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-50 transition-colors"
                >
                  {deleting ? 'Deleting…' : 'Delete'}
                </button>
              </div>
            </>
          ) : (
            <>
              {isEdit ? (
                <button
                  onClick={() => setConfirmingDelete(true)}
                  className="flex items-center gap-1.5 text-sm text-red-500 hover:text-red-700 transition-colors"
                >
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={1.75}
                      d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
                    />
                  </svg>
                  Delete
                </button>
              ) : (
                <div />
              )}
              <div className="flex items-center gap-2 ml-auto">
                <button
                  onClick={onClose}
                  className="px-4 py-2 text-sm font-medium text-gray-600 hover:text-gray-900 transition-colors"
                >
                  Cancel
                </button>
                <button
                  onClick={handleSave}
                  disabled={saving}
                  className="px-4 py-2 text-sm font-medium bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50 transition-colors"
                >
                  {saving ? 'Saving…' : isEdit ? 'Save changes' : 'Add faculty'}
                </button>
              </div>
            </>
          )}
        </div>
      </div>
    </>
  );
}
