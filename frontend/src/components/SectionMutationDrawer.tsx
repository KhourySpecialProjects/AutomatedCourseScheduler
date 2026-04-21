import { useCallback, useEffect, useMemo, useState } from 'react';
import {
  getAutomatedCourseSchedulerAPI,
  type CourseResponse,
  type FacultyResponse,
  type InstructorInfo,
  type SectionCreate,
  type SectionRichResponse,
  type TimeBlockInfo,
} from '../api/generated';
import { axiosInstance } from '../api/axiosInstance';
import SearchableSelect, { type SelectOption } from './SearchableSelect';
import MultiSearchableSelect from './MultiSearchableSelect';
import SectionComments from './SectionComments';
import { formatCourseLabel } from '../utils/courseFormat';

// ── Time block helpers ─────────────────────────────────────────────────────────

const DAY_LABELS: Record<string, string> = { M: 'Mon', T: 'Tue', W: 'Wed', R: 'Thu', F: 'Fri' };
const DAY_ORDER = ['M', 'T', 'W', 'R', 'F'];

/** TimeBlockInfo extended with the block_group field returned by GET /time-blocks. */
type TimeBlockFull = TimeBlockInfo & { block_group?: string | null };

/** Standard NEU semester course sequences, matched to DB time blocks by days+time. */
const STANDARD_SEQUENCES = [
  { name: 'Seq 1', days: 'MWR', start: '08:00', end: '09:05' },
  { name: 'Seq 2', days: 'MWR', start: '09:15', end: '10:20' },
  { name: 'Seq 3', days: 'MWR', start: '10:30', end: '11:35' },
  { name: 'Seq A', days: 'MR',  start: '11:45', end: '13:25' },
  { name: 'Seq 4', days: 'MWR', start: '13:35', end: '14:40' },
  { name: 'Seq B', days: 'MW',  start: '14:50', end: '16:30' },
  { name: 'Seq 5', days: 'MWR', start: '16:35', end: '17:40' },
  { name: 'Seq C', days: 'TF',  start: '08:00', end: '09:40' },
  { name: 'Seq D', days: 'TF',  start: '09:50', end: '11:30' },
  { name: 'Seq E', days: 'WF',  start: '11:45', end: '13:25' },
  { name: 'Seq F', days: 'TF',  start: '13:35', end: '15:15' },
  { name: 'Seq G', days: 'TF',  start: '15:25', end: '17:05' },
] as const;

/** Convert 24-hour "HH:MM" to "H:MM AM/PM". */
function to12Hour(time24: string): string {
  const [h, m] = time24.split(':').map(Number);
  const period = h < 12 ? 'AM' : 'PM';
  const hour = h % 12 || 12;
  return `${hour}:${String(m).padStart(2, '0')} ${period}`;
}

/** Convert hour/minute/period selection to 24-hour "HH:MM". */
function to24Hour(hour: string, minute: string, period: 'AM' | 'PM'): string {
  let h = Number(hour) % 12;
  if (period === 'PM') h += 12;
  return `${String(h).padStart(2, '0')}:${minute.padStart(2, '0')}`;
}

/** Return the day chars in canonical MTWRF order. */
function orderDays(selected: string[]): string {
  return DAY_ORDER.filter((d) => selected.includes(d)).join('');
}

/** Format a days string as "Mon/Wed/Thu". */
function formatDays(days: string): string {
  return days.split('').map((d) => DAY_LABELS[d] ?? d).join('/');
}

/** Find a standard sequence name for this days+time combination, or null. */
function findSequenceName(days: string, start: string, end: string): string | null {
  return (
    STANDARD_SEQUENCES.find((s) => s.days === days && s.start === start && s.end === end)?.name ??
    null
  );
}

/** Split block sequences — two blocks with different days/times that form one course meeting pattern. */
const SPLIT_SEQUENCES = [
  {
    name: 'Seq H',
    blocks: [
      { days: 'T', start: '11:45', end: '13:25' },
      { days: 'R', start: '14:50', end: '16:30' },
    ],
  },
] as const;

/** Find a named split sequence matching two blocks (order-independent), or null. */
function findSplitSequenceName(
  b1: { days: string; start_time: string; end_time: string },
  b2: { days: string; start_time: string; end_time: string },
): string | null {
  for (const seq of SPLIT_SEQUENCES) {
    const [s1, s2] = seq.blocks;
    const fwd =
      s1.days === b1.days && s1.start === b1.start_time && s1.end === b1.end_time &&
      s2.days === b2.days && s2.start === b2.start_time && s2.end === b2.end_time;
    const rev =
      s1.days === b2.days && s1.start === b2.start_time && s1.end === b2.end_time &&
      s2.days === b1.days && s2.start === b1.start_time && s2.end === b1.end_time;
    if (fwd || rev) return seq.name;
  }
  return null;
}

/** Build a human-readable label: "Seq 1  ·  Mon/Wed/Thu  8:00 AM – 9:05 AM". */
function timeBlockLabel(days: string, start: string, end: string): string {
  const seqName = findSequenceName(days, start, end);
  const timeRange = `${to12Hour(start)} – ${to12Hour(end)}`;
  const daysStr = formatDays(days);
  return seqName ? `${seqName}  ·  ${daysStr}  ${timeRange}` : `${daysStr}  ${timeRange}`;
}

/** Pick a random uppercase letter to use as a split-block group identifier. */
function generateBlockGroup(): string {
  return 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'[Math.floor(Math.random() * 26)];
}

// ── Sub-components ─────────────────────────────────────────────────────────────

/**
 * Compound AM/PM time selector — three linked selects for hour, minute, period.
 * Reports the chosen time as a "HH:MM" 24-hour string via `onChange`.
 */
function TimeSelect({ value, onChange }: { value: string; onChange: (v: string) => void }) {
  const [h24, m] = value ? value.split(':') : ['', ''];
  const hNum = h24 ? Number(h24) : null;
  const hour = hNum !== null ? String(hNum % 12 || 12) : '';
  const minute = m ?? '';
  const period: 'AM' | 'PM' = hNum !== null && hNum >= 12 ? 'PM' : 'AM';

  function emit(newHour: string, newMinute: string, newPeriod: 'AM' | 'PM') {
    if (newHour && newMinute) onChange(to24Hour(newHour, newMinute, newPeriod));
  }

  const sel = 'text-xs border border-gray-200 rounded px-1.5 py-1 focus:outline-none focus:ring-1 focus:ring-burgundy-500 bg-white';

  return (
    <div className="flex items-center gap-1">
      <select className={sel} value={hour} onChange={(e) => emit(e.target.value, minute, period)}>
        <option value="">hr</option>
        {[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12].map((n) => (
          <option key={n} value={String(n)}>{n}</option>
        ))}
      </select>
      <span className="text-xs text-gray-400">:</span>
      <select className={sel} value={minute} onChange={(e) => emit(hour, e.target.value, period)}>
        <option value="">min</option>
        {['00', '05', '10', '15', '20', '25', '30', '35', '40', '45', '50', '55'].map((mm) => (
          <option key={mm} value={mm}>{mm}</option>
        ))}
      </select>
      <select className={sel} value={period} onChange={(e) => emit(hour, minute, e.target.value as 'AM' | 'PM')}>
        <option value="AM">AM</option>
        <option value="PM">PM</option>
      </select>
    </div>
  );
}

/** Day toggle buttons + start/end time selects for one meeting pattern. */
function MeetingPatternInput({
  days,
  startTime,
  endTime,
  onDaysChange,
  onStartChange,
  onEndChange,
}: {
  days: string[];
  startTime: string;
  endTime: string;
  onDaysChange: (d: string[]) => void;
  onStartChange: (v: string) => void;
  onEndChange: (v: string) => void;
}) {
  function toggleDay(d: string) {
    onDaysChange(days.includes(d) ? days.filter((x) => x !== d) : [...days, d]);
  }

  return (
    <div className="space-y-2">
      <div className="flex gap-1">
        {DAY_ORDER.map((d) => (
          <button
            key={d}
            type="button"
            onClick={() => toggleDay(d)}
            className={`px-2 py-1 text-xs font-medium rounded transition-colors ${
              days.includes(d)
                ? 'bg-burgundy-600 text-white'
                : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
            }`}
          >
            {DAY_LABELS[d]}
          </button>
        ))}
      </div>
      <div className="flex items-center gap-2">
        <TimeSelect value={startTime} onChange={onStartChange} />
        <span className="text-xs text-gray-400">–</span>
        <TimeSelect value={endTime} onChange={onEndChange} />
      </div>
    </div>
  );
}

/**
 * Inline form that lets admins create a new time block (or split block pair)
 * without leaving the section drawer.  On success it calls `onCreated` with
 * one or two `TimeBlockInfo` objects — two when "split block" is checked.
 */
function InlineTimeBlockForm({
  campusId,
  onCreated,
  onCancel,
}: {
  campusId: number;
  onCreated: (tb: TimeBlockFull | TimeBlockFull[]) => void;
  onCancel: () => void;
}) {
  const [days1, setDays1] = useState<string[]>([]);
  const [start1, setStart1] = useState('');
  const [end1, setEnd1] = useState('');

  // Second meeting pattern for split blocks
  const [isSplit, setIsSplit] = useState(false);
  const [days2, setDays2] = useState<string[]>([]);
  const [start2, setStart2] = useState('');
  const [end2, setEnd2] = useState('');

  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function postBlock(
    meetingDays: string,
    startTime: string,
    endTime: string,
    blockGroup: string | null,
  ): Promise<TimeBlockFull> {
    const created = await axiosInstance<{
      time_block_id: number;
      meeting_days: string;
      start_time: string;
      end_time: string;
      block_group: string | null;
    }>({
      method: 'POST',
      url: '/time-blocks',
      data: { meeting_days: meetingDays, start_time: startTime, end_time: endTime, campus_id: campusId, block_group: blockGroup },
    });
    return {
      time_block_id: created.time_block_id,
      days: created.meeting_days,
      start_time: created.start_time,
      end_time: created.end_time,
      block_group: created.block_group,
    };
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const daysStr1 = orderDays(days1);
    if (!daysStr1 || !start1 || !end1) {
      setError('Please select at least one day and set start and end times.');
      return;
    }
    if (isSplit && (!orderDays(days2) || !start2 || !end2)) {
      setError('Please complete the second meeting pattern.');
      return;
    }
    setSaving(true);
    setError(null);
    try {
      if (isSplit) {
        const group = generateBlockGroup();
        const [tb1, tb2] = await Promise.all([
          postBlock(daysStr1, start1, end1, group),
          postBlock(orderDays(days2), start2, end2, group),
        ]);
        onCreated([tb1, tb2]);
      } else {
        onCreated(await postBlock(daysStr1, start1, end1, null));
      }
    } catch (err: unknown) {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setError(typeof detail === 'string' ? detail : 'Failed to create time block.');
    } finally {
      setSaving(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="mt-3 p-3 bg-gray-50 border border-gray-200 rounded-lg space-y-3">
      {error && <p className="text-xs text-red-600">{error}</p>}

      <p className="text-xs font-medium text-gray-600">Meeting days &amp; times</p>
      <MeetingPatternInput
        days={days1}
        startTime={start1}
        endTime={end1}
        onDaysChange={setDays1}
        onStartChange={setStart1}
        onEndChange={setEnd1}
      />

      <label className="flex items-center gap-2 text-xs text-gray-600 cursor-pointer select-none">
        <input
          type="checkbox"
          checked={isSplit}
          onChange={(e) => setIsSplit(e.target.checked)}
          className="rounded border-gray-300 text-burgundy-600 focus:ring-burgundy-500"
        />
        Split block (two different meeting times)
      </label>

      {isSplit && (
        <div className="pl-3 border-l-2 border-gray-200 space-y-2">
          <p className="text-xs font-medium text-gray-600">Second meeting pattern</p>
          <MeetingPatternInput
            days={days2}
            startTime={start2}
            endTime={end2}
            onDaysChange={setDays2}
            onStartChange={setStart2}
            onEndChange={setEnd2}
          />
        </div>
      )}

      <div className="flex items-center gap-2 justify-end pt-1">
        <button
          type="button"
          onClick={onCancel}
          className="text-xs text-gray-500 hover:text-gray-700 transition-colors"
        >
          Cancel
        </button>
        <button
          type="submit"
          disabled={saving}
          className="px-3 py-1.5 text-xs font-medium text-white bg-burgundy-600 rounded hover:bg-burgundy-700 disabled:opacity-50 transition-colors"
        >
          {saving ? 'Creating…' : isSplit ? 'Create split block' : 'Create time block'}
        </button>
      </div>
    </form>
  );
}

function courseOptionFromApi(c: CourseResponse): SelectOption<number> {
  const r = c as unknown as Record<string, unknown>;
  const id = Number(r.CourseID ?? r.course_id ?? 0);
  const name = String(r.CourseName ?? r.name ?? `Course ${id}`);
  const subj = r.CourseSubject ?? r.subject;
  const no = r.CourseNo ?? r.code;
  const subject = typeof subj === 'string' ? subj : undefined;
  const code = typeof no === 'number' ? no : Number(no);
  const label = formatCourseLabel({ name, subject, code });
  const credits = Number(r.Credits ?? r.credits);
  const sublabel = Number.isFinite(credits) ? `${credits} cr` : undefined;
  return { value: id, label, sublabel };
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
  timeBlocks: TimeBlockFull[];
  campusId: number | null;
  campusName: string | null;
  onClose: () => void;
  /** Called when admin creates a new time block inline — parent should add it to its list. */
  onTimeBlockCreated?: (tb: TimeBlockFull) => void;
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
  const { scheduleId, timeBlocks, campusId, campusName, onClose, onTimeBlockCreated } = props;
  const isEdit = props.mode === 'edit';
  const section = isEdit ? props.section : null;
  const [originalCrosslistedId, setOriginalCrosslistedId] = useState<number | null>(
    section?.crosslisted_section_id ?? null,
  );

  // Form state
  const [courseId, setCourseId] = useState<number | null>(section?.course.course_id ?? null);
  const [timeBlockId, setTimeBlockId] = useState<number | null>(section?.time_block.time_block_id ?? null);
  const [capacity, setCapacity] = useState<number | ''>(section?.capacity ?? '');
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

  const catalogById = useMemo(() => {
    const m = new Map<number, CourseResponse>();
    for (const c of courses) m.set(c.course_id, c);
    return m;
  }, [courses]);

  const sectionLabelForUi = useCallback(
    (s: SectionRichResponse): string => {
      const cat = catalogById.get(s.course.course_id);
      const courseLabel = formatCourseLabel({
        name: cat?.name ?? s.course.name,
        subject: cat?.subject,
        code: cat?.code,
      });
      return `${courseLabel} Section ${s.section_number}`;
    },
    [catalogById],
  );

  // Controls visibility of the inline "create time block" form
  const [showAddBlock, setShowAddBlock] = useState(false);

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
        label: sectionLabelForUi(s),
        sublabel: `${s.time_block.days} ${s.time_block.start_time} – ${s.time_block.end_time}`,
      }))
      .sort((a, b) => a.label.localeCompare(b.label));
    return [none, ...partners];
  }, [scheduleSections, section, crosslistedSectionId, sectionLabelForUi]);

  const crosslistPartnerLabel = useMemo(() => {
    if (crosslistedSectionId == null) return null;
    const p = scheduleSections.find((s) => s.section_id === crosslistedSectionId);
    if (!p) return null;
    return sectionLabelForUi(p);
  }, [scheduleSections, crosslistedSectionId, sectionLabelForUi]);

  const uncrosslistWarning = useMemo(() => {
    if (!isEdit) return null;
    if (originalCrosslistedId == null) return null;
    if (crosslistedSectionId != null) return null;
    const p = scheduleSections.find((s) => s.section_id === originalCrosslistedId);
    const label = p ? sectionLabelForUi(p) : `section #${originalCrosslistedId}`;
    return `You are uncrosslisting from ${label}. Both sections will keep their current time block and instructors; review both rows after saving.`;
  }, [isEdit, originalCrosslistedId, crosslistedSectionId, scheduleSections, sectionLabelForUi]);

  const changeCrosslistPartnerWarning = useMemo(() => {
    if (!isEdit) return null;
    if (originalCrosslistedId == null) return null;
    if (crosslistedSectionId == null) return null;
    if (crosslistedSectionId === originalCrosslistedId) return null;
    const prev = scheduleSections.find((s) => s.section_id === originalCrosslistedId);
    const next = scheduleSections.find((s) => s.section_id === crosslistedSectionId);
    const prevLabel = prev ? sectionLabelForUi(prev) : `section #${originalCrosslistedId}`;
    const nextLabel = next ? sectionLabelForUi(next) : `section #${crosslistedSectionId}`;
    return `This section will be uncrosslisted with ${prevLabel} and crosslisted with ${nextLabel} when you save.`;
  }, [isEdit, originalCrosslistedId, crosslistedSectionId, scheduleSections, sectionLabelForUi]);

  const showNewCrosslistSyncNotice = useMemo(() => {
    if (!isEdit) return false;
    return originalCrosslistedId == null && crosslistedSectionId != null;
  }, [isEdit, originalCrosslistedId, crosslistedSectionId]);

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

  const timeBlockOptions: SelectOption<number>[] = useMemo(() => {
    // Only show multi-day blocks (the standard named sequences) and split block halves.
    // Exclude single-day blocks (days.length === 1 and no block_group) — those are legacy
    // seed blocks that aren't useful for manual section assignment.
    const eligible = timeBlocks.filter((tb) => {
      // Always keep split-block halves
      if (tb.block_group != null) return true;
      // Only show blocks that exactly match a known standard sequence —
      // this filters out legacy seed blocks that don't correspond to any
      // official NEU meeting pattern.
      return STANDARD_SEQUENCES.some(
        (s) => s.days === tb.days && s.start === tb.start_time && s.end === tb.end_time,
      );
    });

    // Sort by start time so the earlier block of a pair is always processed first
    const sorted = [...eligible].sort((a, b) => a.start_time.localeCompare(b.start_time));
    const seen = new Set<number>();
    const opts: SelectOption<number>[] = [];

    for (const tb of sorted) {
      if (seen.has(tb.time_block_id)) continue;
      seen.add(tb.time_block_id);

      if (tb.block_group) {
        // Find the partner block sharing the same group
        const pair = sorted.find(
          (other) => other.block_group === tb.block_group && other.time_block_id !== tb.time_block_id,
        );
        if (pair) {
          seen.add(pair.time_block_id);
          const seqName = findSplitSequenceName(tb, pair);
          const part1 = `${formatDays(tb.days)}  ${to12Hour(tb.start_time)} – ${to12Hour(tb.end_time)}`;
          const part2 = `${formatDays(pair.days)}  ${to12Hour(pair.start_time)} – ${to12Hour(pair.end_time)}`;
          const label = seqName ? `${seqName}  ·  ${part1}  +  ${part2}` : `${part1}  +  ${part2}`;
          opts.push({ value: tb.time_block_id, label });
          continue;
        }
      }
      opts.push({ value: tb.time_block_id, label: timeBlockLabel(tb.days, tb.start_time, tb.end_time) });
    }

    return opts.sort((a, b) => a.label.localeCompare(b.label));
  }, [timeBlocks]);

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
      if (timeBlockId === null) {
        setError('Time block is required.');
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
                <div className="flex items-center justify-between mb-1.5">
                  <Label>Time block</Label>
                  {/* Only show "Add new" when a campus is known — we need it to create the block */}
                  {campusId != null && !showAddBlock && (
                    <button
                      type="button"
                      onClick={() => setShowAddBlock(true)}
                      className="text-xs text-burgundy-600 hover:text-burgundy-800 transition-colors"
                    >
                      + Add new
                    </button>
                  )}
                </div>
                <SearchableSelect
                  options={timeBlockOptions}
                  value={timeBlockId}
                  onChange={setTimeBlockId}
                  placeholder="Select a time block…"
                />
                {/* Inline form to create a new time block without leaving the drawer */}
                {showAddBlock && campusId != null && (
                  <InlineTimeBlockForm
                    campusId={campusId}
                    onCreated={(result) => {
                      const blocks = Array.isArray(result) ? result : [result];
                      // Auto-select the first block of the pair
                      if (blocks.length > 0) setTimeBlockId(blocks[0].time_block_id);
                      // Notify parent so its dropdown list stays in sync
                      for (const tb of blocks) onTimeBlockCreated?.(tb);
                      setShowAddBlock(false);
                    }}
                    onCancel={() => setShowAddBlock(false)}
                  />
                )}
              </div>

              {/* Capacity + section number (edit: fixed; create: auto-assigned server-side) */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label>{isEdit ? 'Capacity' : 'Capacity (optional)'}</Label>
                  <input
                    type="number"
                    min={1}
                    value={capacity}
                    onChange={(e) => setCapacity(e.target.value ? Number(e.target.value) : '')}
                    className="w-full text-sm border border-gray-200 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-burgundy-500"
                    placeholder={isEdit ? 'e.g. 25' : 'Default 30 if empty'}
                  />
                </div>
                <div>
                  <Label>Section #</Label>
                  {isEdit && section ? (
                    <input
                      type="number"
                      min={1}
                      value={section.section_number}
                      disabled
                      readOnly
                      className="w-full text-sm border border-gray-200 rounded-lg px-3 py-2 bg-gray-50 text-gray-500"
                    />
                  ) : (
                    <p className="text-sm text-gray-600 leading-relaxed pt-1">
                      Assigned automatically (next number for this course on this schedule).
                    </p>
                  )}
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
                    className="w-full text-sm border border-gray-200 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-burgundy-500"
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
                  disabled={saving || loadingData}
                  className="px-4 py-2 text-sm font-medium bg-burgundy-600 text-white rounded-lg hover:bg-burgundy-700 disabled:opacity-50 transition-colors"
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
