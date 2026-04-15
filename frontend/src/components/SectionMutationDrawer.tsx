import { useEffect, useMemo, useState } from 'react';
import {
  getAutomatedCourseSchedulerAPI,
  type CourseResponse,
  type FacultyResponse,
  type SectionRichResponse,
  type TimeBlockInfo,
} from '../api/generated';
import SearchableSelect, { type SelectOption } from './SearchableSelect';
import MultiSearchableSelect from './MultiSearchableSelect';

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

  // Form state
  const [courseId, setCourseId] = useState<number | null>(section?.course.course_id ?? null);
  const [timeBlockId, setTimeBlockId] = useState<number | null>(section?.time_block.time_block_id ?? null);
  const [capacity, setCapacity] = useState<number | ''>(section?.capacity ?? '');
  const [sectionNumber, setSectionNumber] = useState<number | ''>(section?.section_number ?? '');
  const [room, setRoom] = useState(section?.room ?? '');
  const [selectedNuids, setSelectedNuids] = useState<number[]>(
    section?.instructors.map((i) => i.nuid) ?? [],
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

  const warning = useMemo<string | null>(() => {
    if (timeBlockId === null || selectedNuids.length === 0) return null;

    const selected = new Set(selectedNuids);
    const conflicts = scheduleSections
      .filter((s) => (section ? s.section_id !== section.section_id : true))
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
      .map((c) => `${c.name || `NUID ${c.nuid}`} is already assigned to ${c.course} §${c.sectionNo}`)
      .slice(0, 4);
    const more = conflicts.length > 4 ? ` (+${conflicts.length - 4} more)` : '';
    return `Professor double-booked: ${lines.join('; ')}${more}`;
  }, [scheduleSections, section, selectedNuids, timeBlockId]);

  // Build typed SelectOption arrays once data is loaded
  const courseOptions: SelectOption<number>[] = courses.map((c) => ({
    value: c.course_id,
    label: c.name ?? `Course ${c.course_id}`,
    sublabel: [c.subject, c.code].filter(Boolean).join(' ') || undefined,
  }));

  const timeBlockOptions: SelectOption<number>[] = timeBlocks.map((tb) => ({
    value: tb.time_block_id,
    label: `${tb.days}  ${tb.start_time} – ${tb.end_time}`,
  }));

  const facultyOptions: SelectOption<number>[] = faculty.map((f) => ({
    value: f.nuid,
    label: `${f.first_name ?? ''} ${f.last_name ?? ''}`.trim(),
    // sublabel: f.nuid ?? undefined,
  }));

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
    if (courseId === null || timeBlockId === null || capacity === '') {
      setError('Course, time block, and capacity are required.');
      return;
    }
    if (!isEdit && sectionNumber === '') {
      setError('Section number is required.');
      return;
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
          faculty_nuids: selectedNuids,
        });
      } else {
        await api.createSectionSectionsPost({
          schedule_id: scheduleId,
          course_id: courseId,
          time_block_id: timeBlockId,
          capacity: capacity as number,
          section_number: sectionNumber as number,
          faculty_nuids: selectedNuids,
        });
      }
      onClose();
    } catch (err: unknown) {
      const status = (err as { response?: { status?: number } })?.response?.status;
      if (status === 423) {
        setError('This section is locked by another user. Please try again later.');
      } else {
        setError('Failed to save. Please try again.');
      }
      setSaving(false);
    }
  }

  const title = isEdit
    ? `Edit ${section!.course.name} §${section!.section_number}`
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
                <Label>Time Block</Label>
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
                  <Label>Capacity</Label>
                  <input
                    type="number"
                    min={1}
                    value={capacity}
                    onChange={(e) => setCapacity(e.target.value ? Number(e.target.value) : '')}
                    className="w-full text-sm border border-gray-200 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                    placeholder="e.g. 25"
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

              {/* Faculty */}
              <div>
                <Label>Instructors</Label>
                <MultiSearchableSelect
                  options={facultyOptions}
                  value={selectedNuids}
                  onChange={setSelectedNuids}
                  placeholder="Add instructors…"
                />
                {warning && (
                  <div className="mt-2 p-3 bg-amber-50 border border-amber-200 rounded-lg text-sm text-amber-800">
                    {warning}
                  </div>
                )}
              </div>

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
                  disabled={saving || loadingData}
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
