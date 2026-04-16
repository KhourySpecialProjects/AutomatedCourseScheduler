import { useEffect, useMemo, useState } from 'react';
import {
  getAutomatedCourseSchedulerAPI,
  type CourseResponse,
  type FacultyResponse,
  type InstructorInfo,
  type SectionCreate,
  type SectionRichResponse,
  type TimeBlockInfo,
} from '../api/generated';
import SearchableSelect, { type SelectOption } from './SearchableSelect';
import MultiSearchableSelect from './MultiSearchableSelect';
import SectionComments from './SectionComments';

function courseOptionFromApi(c: CourseResponse): SelectOption<number> {
  const r = c as unknown as Record<string, unknown>;
  const id = Number(r.CourseID ?? r.course_id ?? 0);
  const name = String(r.CourseName ?? r.name ?? `Course ${id}`);
  const subj = r.CourseSubject ?? r.subject;
  const no = r.CourseNo ?? r.code;
  const sub = [subj, no].filter((x) => x != null && x !== '').join(' ');
  return { value: id, label: name, sublabel: sub || undefined };
}

function facultyOptionFromApi(f: FacultyResponse): SelectOption<number> {
  const r = f as unknown as Record<string, unknown>;
  const nuid = Number(r.NUID ?? r.nuid ?? 0);
  const fn = String(r.FirstName ?? r.first_name ?? '').trim();
  const ln = String(r.LastName ?? r.last_name ?? '').trim();
  const title = r.Title ?? r.title;
  const label = [fn, ln].filter(Boolean).join(' ').trim() || `NUID ${nuid}`;
  const sublabel =
    typeof title === 'string' && title.trim() ? title.trim() : undefined;
  return { value: nuid, label, sublabel };
}

/** Lower = sort earlier. Eager first, then willing, unknown, not interested. */
function rankCoursePreferenceForSort(preference: string | undefined): number {
  switch (preference) {
    case 'Eager to teach':
      return 0;
    case 'Willing to teach':
      return 1;
    case 'Not my cup of tea':
      return 3;
    default:
      return 2;
  }
}

function coursePreferenceHintForSelectedCourse(
  preference: string | undefined,
): string | null {
  switch (preference) {
    case 'Eager to teach':
      return 'Eager for this course';
    case 'Willing to teach':
      return 'Willing to teach this course';
    case 'Not my cup of tea':
      return 'Not interested in this course';
    default:
      return null;
  }
}

function preferenceForCourse(ins: InstructorInfo | undefined, courseId: number | null): string | undefined {
  if (!ins || courseId === null) return undefined;
  return ins.course_preferences.find((p) => p.course_id === courseId)?.preference;
}

interface BaseProps {
  scheduleId: number;
  timeBlocks: TimeBlockInfo[];
  campusName: string | null;
  onClose: () => void;
}

interface CreateProps extends BaseProps {
  mode: 'create';
}

interface EditProps extends BaseProps {
  mode: 'edit';
  section: SectionRichResponse;
}

type Props = CreateProps | EditProps;

function Label({ children }: { children: React.ReactNode }) {
  return (
    <label className="block text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1.5">
      {children}
    </label>
  );
}

export default function SectionMutationDrawer(props: Props) {
  const { scheduleId, timeBlocks, campusName, onClose } = props;
  const isEdit = props.mode === 'edit';
  const section = isEdit ? props.section : null;
  const [originalCrosslistedId, setOriginalCrosslistedId] = useState<number | null>(
    section?.crosslisted_section_id ?? null,
  );

  // Form state
  const [courseId, setCourseId] = useState<number | null>(section?.course.course_id ?? null);
  const [timeBlockId, setTimeBlockId] = useState<number | null>(section?.time_block.time_block_id ?? null);
  const [capacity, setCapacity] = useState<number | ''>(section?.capacity ?? '');
  const [sectionNumber, setSectionNumber] = useState<number | ''>(section?.section_number ?? '');
  const [room, setRoom] = useState(section?.room ?? '');
  const [selectedNuids, setSelectedNuids] = useState<number[]>(
    section?.instructors.map((i) => i.nuid) ?? [],
  );
  const [crosslistedSectionId, setCrosslistedSectionId] = useState<number | null>(
    section?.crosslisted_section_id ?? null,
  );

  // Remote data
  const [courses, setCourses] = useState<CourseResponse[]>([]);
  const [faculty, setFaculty] = useState<FacultyResponse[]>([]);
  const [scheduleSections, setScheduleSections] = useState<SectionRichResponse[]>([]);
  const [loadingData, setLoadingData] = useState(true);

  // Submission state
  const [saving, setSaving] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [confirmingDelete, setConfirmingDelete] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const api = getAutomatedCourseSchedulerAPI();
    Promise.allSettled([
      // All catalog courses — "must already exist" means in the catalog, not in this schedule
      api.getCoursesCoursesGet(),
      // Faculty scoped to this campus; active only
      api.getFacultyFacultyGet(
        campusName ? { campus: campusName, active_only: true } : { active_only: true },
      ),
      // Schedule sections, to detect double-booking conflicts
      api.getScheduleSectionsRichSchedulesScheduleIdSectionsRichGet(scheduleId),
    ]).then(([courseResult, facultyResult, sectionsResult]) => {
      if (courseResult.status === 'fulfilled') setCourses(courseResult.value);
      if (facultyResult.status === 'fulfilled') setFaculty(facultyResult.value);
      if (sectionsResult.status === 'fulfilled') setScheduleSections(sectionsResult.value);
      setLoadingData(false);
    });
  }, [campusName, scheduleId]);

  useEffect(() => {
    if (section) {
      queueMicrotask(() => {
        setCrosslistedSectionId(section.crosslisted_section_id ?? null);
        setOriginalCrosslistedId(section.crosslisted_section_id ?? null);
      });
    }
  }, [section]);

  const crosslistOptions = useMemo((): SelectOption<number | null>[] => {
    const none: SelectOption<number | null> = { value: null, label: 'Not crosslisted' };
    if (!section) return [none];
    const unavailableTargets = new Set<number>();
    for (const s of scheduleSections) {
      if (s.section_id === section.section_id) continue;
      if (s.crosslisted_section_id != null) {
        unavailableTargets.add(s.crosslisted_section_id);
      }
    }
    const partners = scheduleSections
      .filter((s) => s.section_id !== section.section_id)
      .filter(
        (s) => !unavailableTargets.has(s.section_id) || s.section_id === crosslistedSectionId,
      )
      .map((s) => ({
        value: s.section_id,
        label: `${s.course.name} Section ${s.section_number}`,
        sublabel: `${s.time_block.days} ${s.time_block.start_time} – ${s.time_block.end_time}`,
      }))
      .sort((a, b) => a.label.localeCompare(b.label));
    return [none, ...partners];
  }, [scheduleSections, section, crosslistedSectionId]);

  const crosslistPartnerLabel = useMemo(() => {
    if (crosslistedSectionId == null) return null;
    const p = scheduleSections.find((s) => s.section_id === crosslistedSectionId);
    if (!p) return null;
    return `${p.course.name} Section ${p.section_number}`;
  }, [scheduleSections, crosslistedSectionId]);

  const uncrosslistWarning = useMemo(() => {
    if (!isEdit) return null;
    if (originalCrosslistedId == null) return null;
    if (crosslistedSectionId != null) return null;
    const p = scheduleSections.find((s) => s.section_id === originalCrosslistedId);
    const label = p ? `${p.course.name} Section ${p.section_number}` : `section #${originalCrosslistedId}`;
    return `You are uncrosslisting from ${label}. Both sections will keep their current time block and instructors; review both rows after saving.`;
  }, [isEdit, originalCrosslistedId, crosslistedSectionId, scheduleSections]);

  const changeCrosslistPartnerWarning = useMemo(() => {
    if (!isEdit) return null;
    if (originalCrosslistedId == null) return null;
    if (crosslistedSectionId == null) return null;
    if (crosslistedSectionId === originalCrosslistedId) return null;
    const prev = scheduleSections.find((s) => s.section_id === originalCrosslistedId);
    const next = scheduleSections.find((s) => s.section_id === crosslistedSectionId);
    const prevLabel = prev ? `${prev.course.name} Section ${prev.section_number}` : `section #${originalCrosslistedId}`;
    const nextLabel = next ? `${next.course.name} Section ${next.section_number}` : `section #${crosslistedSectionId}`;
    return `This section will be uncrosslisted with ${prevLabel} and crosslisted with ${nextLabel} when you save.`;
  }, [isEdit, originalCrosslistedId, crosslistedSectionId, scheduleSections]);

  const showNewCrosslistSyncNotice = useMemo(() => {
    if (!isEdit) return false;
    return originalCrosslistedId == null && crosslistedSectionId != null;
  }, [isEdit, originalCrosslistedId, crosslistedSectionId]);

  /** Create mode: same course + section # already on this schedule. */
  const duplicateCourseSectionMessage = useMemo(() => {
    if (isEdit || courseId === null || sectionNumber === '') return null;
    const n = Number(sectionNumber);
    if (Number.isNaN(n) || n < 1) return null;
    const existing = scheduleSections.find(
      (s) => s.course.course_id === courseId && s.section_number === n,
    );
    if (!existing) return null;
    return `This schedule already has ${existing.course.name} Section ${n}. Use a different section number or course.`;
  }, [isEdit, courseId, sectionNumber, scheduleSections]);

  /** Only when at least one selected instructor is already assigned to another section in this time block. */
  const doubleBookWarning = useMemo<string | null>(() => {
    if (timeBlockId === null || selectedNuids.length === 0) return null;

    const selected = new Set(selectedNuids);
    const conflicts = scheduleSections
      .filter((s) => (section ? s.section_id !== section.section_id : true))
      .filter((s) => {
        if (crosslistedSectionId != null && s.section_id === crosslistedSectionId) return false;
        if (section && s.crosslisted_section_id === section.section_id) return false;
        return true;
      })
      .filter((s) => s.time_block.time_block_id === timeBlockId)
      .flatMap((s) =>
        s.instructors
          .filter((i) => selected.has(i.nuid))
          .map((i) => ({
            nuid: i.nuid,
            name: `${i.first_name} ${i.last_name}`.trim(),
            course: s.course.name,
            sectionNo: s.section_number,
          })),
      );

    if (conflicts.length === 0) return null;

    const lines = conflicts
      .map(
        (c) =>
          `${c.name || `NUID ${c.nuid}`} is already assigned to ${c.course} Section ${c.sectionNo}`,
      )
      .slice(0, 4);
    const more = conflicts.length > 4 ? ` (+${conflicts.length - 4} more)` : '';
    return `Professor double-booked: ${lines.join('; ')}${more}`;
  }, [scheduleSections, section, selectedNuids, timeBlockId, crosslistedSectionId]);

  /** Preferences for faculty appear on schedule rows */
  const instructorByNuid = useMemo(() => {
    const m = new Map<number, InstructorInfo>();
    for (const s of scheduleSections) {
      for (const ins of s.instructors) {
        if (!m.has(ins.nuid)) m.set(ins.nuid, ins);
      }
    }
    return m;
  }, [scheduleSections]);

  // Build typed SelectOption arrays once data is loaded
  const courseOptions: SelectOption<number>[] = courses.map(courseOptionFromApi);

  const timeBlockOptions: SelectOption<number>[] = timeBlocks.map((tb) => ({
    value: tb.time_block_id,
    label: `${tb.days}  ${tb.start_time} – ${tb.end_time}`,
  }));

  const facultyOptions: SelectOption<number>[] = useMemo(() => {
    const rows = faculty.map((f) => {
      const base = facultyOptionFromApi(f);
      const ins = instructorByNuid.get(base.value);
      const pref = preferenceForCourse(ins, courseId);
      const hint = coursePreferenceHintForSelectedCourse(pref);
      const subParts = [hint, base.sublabel].filter((x) => x && String(x).trim());
      return {
        value: base.value,
        label: base.label,
        sublabel: subParts.length ? subParts.join(' · ') : base.sublabel,
      };
    });
    rows.sort((a, b) => {
      const pa = preferenceForCourse(instructorByNuid.get(a.value), courseId);
      const pb = preferenceForCourse(instructorByNuid.get(b.value), courseId);
      const ra = rankCoursePreferenceForSort(pa);
      const rb = rankCoursePreferenceForSort(pb);
      if (ra !== rb) return ra - rb;
      return a.label.localeCompare(b.label);
    });
    return rows;
  }, [faculty, instructorByNuid, courseId]);

  async function handleDelete() {
    if (!section) return;
    setDeleting(true);
    try {
      await getAutomatedCourseSchedulerAPI().deleteSectionSectionsSectionIdDelete(section.section_id);
      onClose();
    } catch {
      setError('Failed to delete section. Please try again.');
      setDeleting(false);
      setConfirmingDelete(false);
    }
  }

  async function handleSave() {
    setError(null);
    if (courseId === null) {
      setError('Course is required.');
      return;
    }
    if (isEdit && section) {
      if (timeBlockId === null || capacity === '') {
        setError('Time block and capacity are required.');
        return;
      }
    } else if (!isEdit) {
      if (timeBlockId === null || sectionNumber === '') {
        setError('Course, time block, and section number are required.');
        return;
      }
      if (duplicateCourseSectionMessage) {
        setError(duplicateCourseSectionMessage);
        return;
      }
    }

    setSaving(true);
    const api = getAutomatedCourseSchedulerAPI();

    try {
      if (isEdit && section) {
        await api.updateSectionSectionsSectionIdPatch(section.section_id, {
          course_id: courseId,
          time_block_id: timeBlockId,
          capacity: capacity as number,
          room: room || null,
          crosslisted_section_id: crosslistedSectionId,
          faculty_nuids: selectedNuids,
        });
        setOriginalCrosslistedId(crosslistedSectionId);
      } else {
        const body: SectionCreate = {
          schedule_id: scheduleId,
          course_id: courseId,
          time_block_id: timeBlockId!,
          section_number: sectionNumber as number,
        };
        if (capacity !== '') body.capacity = capacity as number;
        if (selectedNuids.length > 0) body.faculty_nuids = selectedNuids;
        await api.createSectionSectionsPost(body);
      }
      onClose();
    } catch (err: unknown) {
      const res = (err as { response?: { status?: number; data?: { detail?: unknown } } })?.response;
      const status = res?.status;
      const detail = res?.data?.detail;
      const detailStr = typeof detail === 'string' ? detail : null;
      if (status === 423) {
        setError('This section is locked by another user. Please try again later.');
      } else {
        setError(detailStr ?? 'Failed to save. Please try again.');
      }
      setSaving(false);
    }
  }

  const title = isEdit
    ? `Edit ${section!.course.name} Section ${section!.section_number}`
    : 'Add Section';

  return (
    <>
      {/* Backdrop */}
      <div className="fixed inset-0 bg-black/20 z-40" onClick={onClose} />

      {/* Drawer */}
      <div className="fixed right-0 top-0 h-full w-[28rem] bg-white shadow-xl z-50 flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-5 border-b border-gray-100">
          <h2 className="text-base font-semibold text-gray-900">{title}</h2>
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
        <div className="flex-1 overflow-y-auto p-6 space-y-5">
          {loadingData ? (
            <div className="flex items-center gap-2 text-gray-400 text-sm">
              <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
              </svg>
              Loading…
            </div>
          ) : (
            <>
              {/* Course */}
              <div>
                <Label>Course</Label>
                <SearchableSelect
                  options={courseOptions}
                  value={courseId}
                  onChange={setCourseId}
                  placeholder="Select a course…"
                />
              </div>

              {/* Time Block */}
              <div>
                <Label>Time block</Label>
                <SearchableSelect
                  options={timeBlockOptions}
                  value={timeBlockId}
                  onChange={setTimeBlockId}
                  placeholder="Select a time block…"
                />
              </div>

              {/* Capacity + Section # */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label>{isEdit ? 'Capacity' : 'Capacity (optional)'}</Label>
                  <input
                    type="number"
                    min={1}
                    value={capacity}
                    onChange={(e) => setCapacity(e.target.value ? Number(e.target.value) : '')}
                    className="w-full text-sm border border-gray-200 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                    placeholder={isEdit ? 'e.g. 25' : 'Default 30 if empty'}
                  />
                </div>
                <div>
                  <Label>Section #</Label>
                  <input
                    type="number"
                    min={1}
                    value={sectionNumber}
                    onChange={(e) => setSectionNumber(e.target.value ? Number(e.target.value) : '')}
                    disabled={isEdit}
                    className="w-full text-sm border border-gray-200 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-500 disabled:bg-gray-50 disabled:text-gray-400"
                    placeholder="e.g. 1"
                  />
                </div>
              </div>
              {!isEdit && duplicateCourseSectionMessage && (
                <div className="p-3 bg-amber-50 border border-amber-200 rounded-lg text-sm text-amber-900">
                  {duplicateCourseSectionMessage}
                </div>
              )}

              {/* Room (edit only) */}
              {isEdit && (
                <div>
                  <Label>Room</Label>
                  <input
                    type="text"
                    value={room}
                    onChange={(e) => setRoom(e.target.value)}
                    className="w-full text-sm border border-gray-200 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                    placeholder="e.g. Ryder 101"
                  />
                </div>
              )}

              {isEdit && section && (
                <div>
                  <Label>Crosslisted section</Label>
                  <p className="text-xs text-gray-500 mb-2">
                    Choose another section in this schedule this offering is paired with (e.g. undergrad / graduate).
                  </p>
                  <SearchableSelect<number | null>
                    options={crosslistOptions}
                    value={crosslistedSectionId}
                    onChange={setCrosslistedSectionId}
                    placeholder="Not crosslisted"
                  />
                  {uncrosslistWarning && (
                    <div className="mt-2 p-3 bg-amber-50 border border-amber-200 rounded-lg text-sm text-amber-900">
                      {uncrosslistWarning}
                    </div>
                  )}
                  {changeCrosslistPartnerWarning && (
                    <div className="mt-2 p-3 bg-amber-50 border border-amber-200 rounded-lg text-sm text-amber-900">
                      {changeCrosslistPartnerWarning}
                    </div>
                  )}
                  {showNewCrosslistSyncNotice && (
                    <div className="mt-2 p-3 bg-amber-50 border border-amber-200 rounded-lg text-sm text-amber-900">
                      <p className="font-medium">Crosslisted sections stay in sync</p>
                      <p className="mt-1 text-amber-800">
                        When you save,{' '}
                        <span className="font-semibold">
                          {crosslistPartnerLabel ?? 'the selected section'}
                        </span>{' '}
                        will be updated to match this section&apos;s time block, instructors, capacity, and room. After that,
                        if you change any of those fields on either crosslisted section, the other section will be updated too.
                      </p>
                    </div>
                  )}
                </div>
              )}

              {/* Faculty */}
              <div>
                <Label>Instructors</Label>
                <p className="text-xs text-gray-500 mb-2">
                  {courseId != null
                    ? 'Ordered by teaching preference for this course (eager first) when preferences appear elsewhere on this schedule.'
                    : 'Select a course to order instructors by preference for that course.'}
                </p>
                <MultiSearchableSelect
                  options={facultyOptions}
                  value={selectedNuids}
                  onChange={setSelectedNuids}
                  placeholder="Add instructors…"
                />
                {doubleBookWarning && (
                  <div className="mt-2 p-3 bg-amber-50 border border-amber-200 rounded-lg text-sm text-amber-800">
                    {doubleBookWarning}
                  </div>
                )}
              </div>

              {isEdit && section && (
                <div className="pt-4 border-t border-gray-100">
                  <SectionComments sectionId={section.section_id} />
                </div>
              )}

              {error && (
                <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">
                  {error}
                </div>
              )}
            </>
          )}
        </div>

        {/* Footer */}
        <div className="border-t border-gray-100 px-6 py-4 flex items-center justify-between gap-3">
          {confirmingDelete ? (
            <>
              <span className="text-sm text-red-600">Delete this section?</span>
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
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.75} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
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
                  disabled={
                    saving ||
                    loadingData ||
                    (!isEdit && duplicateCourseSectionMessage != null)
                  }
                  className="px-4 py-2 text-sm font-medium bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50 transition-colors"
                >
                  {saving ? 'Saving…' : isEdit ? 'Save changes' : 'Add section'}
                </button>
              </div>
            </>
          )}
        </div>
      </div>
    </>
  );
}
