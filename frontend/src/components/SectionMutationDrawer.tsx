import { useEffect, useState } from 'react';
import {
  getAutomatedCourseSchedulerAPI,
  type CourseResponse,
  type FacultyResponse,
  type SectionRichResponse,
  type TimeBlockInfo,
} from '../api/generated';

interface BaseProps {
  scheduleId: number;
  timeBlocks: TimeBlockInfo[];
  onClose: () => void;
}

interface CreateProps extends BaseProps {
  mode: 'create';
}

interface EditProps extends BaseProps {
  mode: 'edit';
  section: SectionRichResponse;
  onDeleteSuccess: () => void;
}

type Props = CreateProps | EditProps;

function Label({ children }: { children: React.ReactNode }) {
  return (
    <label className="block text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1">
      {children}
    </label>
  );
}

function FieldError({ msg }: { msg: string | null }) {
  if (!msg) return null;
  return <p className="mt-1 text-xs text-red-600">{msg}</p>;
}

export default function SectionMutationDrawer(props: Props) {
  const { scheduleId, timeBlocks, onClose } = props;
  const isEdit = props.mode === 'edit';
  const section = isEdit ? props.section : null;

  // Form state
  const [courseId, setCourseId] = useState<number | ''>(section?.course.course_id ?? '');
  const [timeBlockId, setTimeBlockId] = useState<number | ''>(section?.time_block.time_block_id ?? '');
  const [capacity, setCapacity] = useState<number | ''>(section?.capacity ?? '');
  const [sectionNumber, setSectionNumber] = useState<number | ''>(section?.section_number ?? '');
  const [room, setRoom] = useState(section?.room ?? '');
  const [selectedNuids, setSelectedNuids] = useState<Set<number>>(
    new Set(section?.instructors.map((i) => i.nuid) ?? []),
  );
  const [facultySearch, setFacultySearch] = useState('');

  // Remote data
  const [courses, setCourses] = useState<CourseResponse[]>([]);
  const [faculty, setFaculty] = useState<FacultyResponse[]>([]);
  const [loadingData, setLoadingData] = useState(true);

  // Submission state
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [deleting, setDeleting] = useState(false);
  const [confirmDelete, setConfirmDelete] = useState(false);

  useEffect(() => {
    const api = getAutomatedCourseSchedulerAPI();
    Promise.all([
      api.getCoursesCoursesGet(),
      api.getFacultyFacultyGet(),
    ]).then(([c, f]) => {
      setCourses(c);
      setFaculty(f);
      setLoadingData(false);
    }).catch(() => setLoadingData(false));
  }, []);

  function toggleNuid(nuid: number) {
    setSelectedNuids((prev) => {
      const next = new Set(prev);
      if (next.has(nuid)) next.delete(nuid);
      else next.add(nuid);
      return next;
    });
  }

  const filteredFaculty = facultySearch.trim()
    ? faculty.filter((f) => {
        const q = facultySearch.toLowerCase();
        return (
          f.FirstName?.toLowerCase().includes(q) ||
          f.LastName?.toLowerCase().includes(q) ||
          f.Email?.toLowerCase().includes(q)
        );
      })
    : faculty;

  async function handleSave() {
    setError(null);
    if (courseId === '' || timeBlockId === '' || capacity === '') {
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
          course_id: courseId as number,
          time_block_id: timeBlockId as number,
          capacity: capacity as number,
          room: room || null,
          faculty_nuids: [...selectedNuids],
        });
      } else {
        await api.createSectionSectionsPost({
          schedule_id: scheduleId,
          course_id: courseId as number,
          time_block_id: timeBlockId as number,
          capacity: capacity as number,
          section_number: sectionNumber as number,
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

  async function handleDelete() {
    if (!section) return;
    setDeleting(true);
    const api = getAutomatedCourseSchedulerAPI();
    try {
      await api.deleteSectionSectionsSectionIdDelete(section.section_id);
      (props as EditProps).onDeleteSuccess();
      onClose();
    } catch {
      setError('Failed to delete section.');
      setDeleting(false);
      setConfirmDelete(false);
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
                <select
                  value={courseId}
                  onChange={(e) => setCourseId(e.target.value ? Number(e.target.value) : '')}
                  className="w-full text-sm border border-gray-200 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                >
                  <option value="">Select a course…</option>
                  {courses.map((c) => (
                    <option key={c.CourseID} value={c.CourseID}>
                      {c.CourseName ?? `Course ${c.CourseID}`}
                      {c.CourseSubject ? ` (${c.CourseSubject}${c.CourseNo ? ` ${c.CourseNo}` : ''})` : ''}
                    </option>
                  ))}
                </select>
              </div>

              {/* Time Block */}
              <div>
                <Label>Time Block</Label>
                <select
                  value={timeBlockId}
                  onChange={(e) => setTimeBlockId(e.target.value ? Number(e.target.value) : '')}
                  className="w-full text-sm border border-gray-200 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                >
                  <option value="">Select a time block…</option>
                  {timeBlocks.map((tb) => (
                    <option key={tb.time_block_id} value={tb.time_block_id}>
                      {tb.days} {tb.start_time} – {tb.end_time}
                    </option>
                  ))}
                </select>
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
                <Label>Faculty</Label>
                <input
                  type="text"
                  value={facultySearch}
                  onChange={(e) => setFacultySearch(e.target.value)}
                  placeholder="Search faculty…"
                  className="w-full text-sm border border-gray-200 rounded-lg px-3 py-2 mb-2 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                />
                <div className="border border-gray-200 rounded-lg max-h-48 overflow-y-auto divide-y divide-gray-50">
                  {filteredFaculty.length === 0 ? (
                    <p className="px-3 py-2 text-xs text-gray-400">No faculty found.</p>
                  ) : (
                    filteredFaculty.map((f) => {
                      const checked = selectedNuids.has(f.NUID);
                      return (
                        <label
                          key={f.NUID}
                          className="flex items-center gap-3 px-3 py-2 hover:bg-gray-50 cursor-pointer"
                        >
                          <input
                            type="checkbox"
                            checked={checked}
                            onChange={() => toggleNuid(f.NUID)}
                            className="accent-indigo-600"
                          />
                          <span className="text-sm text-gray-800">
                            {f.FirstName} {f.LastName}
                          </span>
                          {f.Title && (
                            <span className="text-xs text-gray-400 ml-auto shrink-0">{f.Title}</span>
                          )}
                        </label>
                      );
                    })
                  )}
                </div>
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
          {/* Delete (edit mode only) */}
          {isEdit && (
            confirmDelete ? (
              <div className="flex items-center gap-2">
                <span className="text-xs text-red-600">Delete this section?</span>
                <button
                  onClick={handleDelete}
                  disabled={deleting}
                  className="px-3 py-1.5 text-xs font-medium bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-50 transition-colors"
                >
                  {deleting ? 'Deleting…' : 'Confirm'}
                </button>
                <button
                  onClick={() => setConfirmDelete(false)}
                  className="px-3 py-1.5 text-xs font-medium text-gray-600 hover:text-gray-900 transition-colors"
                >
                  Cancel
                </button>
              </div>
            ) : (
              <button
                onClick={() => setConfirmDelete(true)}
                className="flex items-center gap-1.5 text-sm text-red-500 hover:text-red-700 transition-colors"
              >
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.75} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                </svg>
                Delete
              </button>
            )
          )}

          {!isEdit && <div />}

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
        </div>
      </div>
    </>
  );
}
