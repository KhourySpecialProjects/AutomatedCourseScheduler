import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import type { InstructorInfo, SectionRichResponse, TimeBlockInfo } from '../api/generated';
import { getAutomatedCourseSchedulerAPI } from '../api/generated';
import type { LockInfo } from '../hooks/useScheduleWebSocket';
import FacultyTooltip from './FacultyTooltip';
import MultiSearchableSelect from './MultiSearchableSelect';
import SectionDetailPanel from './SectionDetailPanel';
import SectionMutationDrawer from './SectionMutationDrawer';
import type { SelectOption } from './SearchableSelect';

type SortKey = 'course' | 'section' | 'time' | 'instructor' | 'capacity';
type SortDir = 'asc' | 'desc';
type DayFilter = 'all' | 'MWR' | 'MR' | 'WF';

interface Props {
  sections: SectionRichResponse[];
  scheduleId: number;
  locks: Map<number, LockInfo>;
  campusName: string | null;
  readOnly?: boolean;
  viewMode?: 'table' | 'calendar';
  onSelectedCourseCountChange?: (count: number) => void;
}

function hasConflict(section: SectionRichResponse): boolean {
  return section.instructors.some((inst) =>
    inst.course_preferences.some(
      (cp) => cp.course_id === section.course.course_id && cp.preference === 'Not my cup of tea',
    ),
  );
}

function primaryInstructor(section: SectionRichResponse): InstructorInfo | undefined {
  return section.instructors[0];
}

function getSortValue(section: SectionRichResponse, key: SortKey): string | number {
  switch (key) {
    case 'course':
      return section.course.name.toLowerCase();
    case 'section':
      return section.section_number;
    case 'time':
      return section.time_block.start_time;
    case 'instructor': {
      const inst = primaryInstructor(section);
      return inst ? inst.last_name.toLowerCase() : '';
    }
    case 'capacity':
      return section.capacity;
  }
}

function dayCategory(days: string): DayFilter {
  if (days === 'MWR') return 'MWR';
  if (days === 'MR') return 'MR';
  if (days === 'WF') return 'WF';
  return 'MWR';
}

function LockBadge({ lock }: { lock: LockInfo }) {
  return (
    <span
      title={`Locked by ${lock.display_name}`}
      className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-xs font-medium bg-amber-50 text-amber-700 border border-amber-200"
    >
      <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
      </svg>
      {lock.display_name}
    </span>
  );
}

function dayLabel(letter: string): string {
  return (
    {
      M: 'Mon',
      T: 'Tue',
      W: 'Wed',
      R: 'Thu',
      F: 'Fri',
    }[letter] ?? letter
  );
}

function expandDays(days: string): string[] {
  const result: string[] = [];
  for (const ch of days) {
    if ('MTWRF'.includes(ch)) result.push(ch);
  }
  return result;
}

function courseColor(): { card: string; accent: string } {
  return { card: 'bg-violet-50 border-violet-200', accent: 'bg-violet-500' };
}

function parseTimeToMinutes(raw: string): number {
  const s = raw.trim();
  // Supports: "09:00", "9:00", "09:00:00", "9:00 AM", "1:35 PM"
  const m = s.match(/^(\d{1,2}):(\d{2})(?::(\d{2}))?\s*(AM|PM|am|pm)?$/);
  if (!m) return Number.POSITIVE_INFINITY;
  let h = Number(m[1]);
  const mins = Number(m[2]);
  const ampm = m[4]?.toLowerCase();
  if (ampm) {
    if (h === 12) h = 0;
    if (ampm === 'pm') h += 12;
  }
  return h * 60 + mins;
}

export default function ScheduleSectionRowView({
  sections,
  scheduleId,
  locks,
  campusName,
  readOnly,
  viewMode = 'table',
  onSelectedCourseCountChange,
}: Props) {
  const [sortKey, setSortKey] = useState<SortKey>('course');
  const [sortDir, setSortDir] = useState<SortDir>('asc');
  const [courseFilterIds, setCourseFilterIds] = useState<number[]>([]);
  const [courseQuery, setCourseQuery] = useState('');
  const [instructorFilterNuids, setInstructorFilterNuids] = useState<number[]>([]);
  const [instructorQuery, setInstructorQuery] = useState('');
  const [dayFilter, setDayFilter] = useState<DayFilter>('all');
  const [selectedSection, setSelectedSection] = useState<SectionRichResponse | null>(null);
  const [hoveredInstructor, setHoveredInstructor] = useState<{
    instructor: InstructorInfo;
    rect: DOMRect;
  } | null>(null);
  const [editingSection, setEditingSection] = useState<SectionRichResponse | null>(null);
  const [creating, setCreating] = useState(false);
  const [lockError, setLockError] = useState<{ sectionId: number; msg: string } | null>(null);
  const hoverTimeout = useRef<ReturnType<typeof setTimeout> | null>(null);

  const handleSort = (key: SortKey) => {
    if (sortKey === key) setSortDir((d) => (d === 'asc' ? 'desc' : 'asc'));
    else { setSortKey(key); setSortDir('asc'); }
  };

  const handleInstructorMouseEnter = useCallback(
    (e: React.MouseEvent<HTMLButtonElement>, instructor: InstructorInfo) => {
      const rect = e.currentTarget.getBoundingClientRect();
      if (hoverTimeout.current) clearTimeout(hoverTimeout.current);
      hoverTimeout.current = setTimeout(() => setHoveredInstructor({ instructor, rect }), 300);
    },
    [],
  );

  const handleInstructorMouseLeave = useCallback(() => {
    if (hoverTimeout.current) clearTimeout(hoverTimeout.current);
    hoverTimeout.current = setTimeout(() => setHoveredInstructor(null), 150);
  }, []);

  useEffect(() => () => { if (hoverTimeout.current) clearTimeout(hoverTimeout.current); }, []);

  useEffect(() => {
    onSelectedCourseCountChange?.(courseFilterIds.length);
  }, [courseFilterIds.length, onSelectedCourseCountChange]);

  // Derive unique time blocks from loaded sections for use in the mutation drawer
  const timeBlocks = useMemo<TimeBlockInfo[]>(() => {
    // De-dupe by displayed block (days + start/end) to avoid duplicate rows.
    const byKey = new Map<string, TimeBlockInfo>();
    for (const s of sections) {
      const tb = s.time_block;
      const key = `${tb.days}|${tb.start_time}|${tb.end_time}`;
      if (!byKey.has(key)) byKey.set(key, tb);
    }
    const result = [...byKey.values()];
    // Chronological ordering: 9:00 AM first, then onward.
    return result.sort((a, b) => {
      const ta = parseTimeToMinutes(a.start_time);
      const tb = parseTimeToMinutes(b.start_time);
      if (ta !== tb) return ta - tb;
      const da = a.days.localeCompare(b.days);
      if (da !== 0) return da;
      return a.end_time.localeCompare(b.end_time);
    });
  }, [sections]);

  // Calendar rows should group by time range, regardless of day pattern.
  const calendarTimeRows = useMemo(() => {
    const byRange = new Map<string, { start_time: string; end_time: string }>();
    for (const s of sections) {
      const tb = s.time_block;
      const key = `${tb.start_time}|${tb.end_time}`;
      if (!byRange.has(key)) byRange.set(key, { start_time: tb.start_time, end_time: tb.end_time });
    }
    const rows = [...byRange.values()];
    return rows.sort((a, b) => {
      const ta = parseTimeToMinutes(a.start_time);
      const tb = parseTimeToMinutes(b.start_time);
      if (ta !== tb) return ta - tb;
      return a.end_time.localeCompare(b.end_time);
    });
  }, [sections]);

  const courseOptions = useMemo<SelectOption<number>[]>(() => {
    const byId = new Map<number, SelectOption<number>>();
    for (const s of sections) {
      if (!byId.has(s.course.course_id)) {
        byId.set(s.course.course_id, {
          value: s.course.course_id,
          label: s.course.name,
        });
      }
    }
    return [...byId.values()].sort((a, b) => a.label.localeCompare(b.label));
  }, [sections]);

  const instructorOptions = useMemo<SelectOption<number>[]>(() => {
    const byNuid = new Map<number, SelectOption<number>>();
    for (const s of sections) {
      for (const i of s.instructors) {
        if (!byNuid.has(i.nuid)) {
          byNuid.set(i.nuid, {
            value: i.nuid,
            label: `${i.first_name} ${i.last_name}`.trim(),
          });
        }
      }
    }
    return [...byNuid.values()].sort((a, b) => a.label.localeCompare(b.label));
  }, [sections]);

  const courseSuggestions = useMemo(() => {
    const q = courseQuery.trim().toLowerCase();
    if (!q) return [];
    const selected = new Set(courseFilterIds);
    return courseOptions
      .filter((o) => !selected.has(o.value))
      .filter((o) => o.label.toLowerCase().includes(q))
      .slice(0, 8);
  }, [courseOptions, courseFilterIds, courseQuery]);

  const instructorSuggestions = useMemo(() => {
    const q = instructorQuery.trim().toLowerCase();
    if (!q) return [];
    const selected = new Set(instructorFilterNuids);
    return instructorOptions
      .filter((o) => !selected.has(o.value))
      .filter((o) => o.label.toLowerCase().includes(q))
      .slice(0, 8);
  }, [instructorOptions, instructorFilterNuids, instructorQuery]);

  async function handleEditClick(e: React.MouseEvent, section: SectionRichResponse) {
    e.stopPropagation();
    if (readOnly) return;
    setLockError(null);
    try {
      await getAutomatedCourseSchedulerAPI().acquireLockSectionsSectionIdLockPost(section.section_id);
      setEditingSection(section);
    } catch (err: unknown) {
      const status = (err as { response?: { status?: number } })?.response?.status;
      const lockMeta = (err as { response?: { data?: { locked_by?: number } } })?.response?.data;
      const lockedBy = locks.get(section.section_id)?.display_name ?? lockMeta?.locked_by ?? 'another user';
      if (status === 423) {
        setLockError({ sectionId: section.section_id, msg: `Locked by ${lockedBy}` });
        setTimeout(() => setLockError(null), 3000);
      }
    }
  }

  async function handleEditClose() {
    if (editingSection) {
      try {
        await getAutomatedCourseSchedulerAPI().releaseLockSectionsSectionIdUnlockPost(editingSection.section_id);
      } catch { /* best-effort */ }
    }
    setEditingSection(null);
  }

  const filtered = sections.filter((s) => {
    const courseMatch = courseFilterIds.length === 0 || courseFilterIds.includes(s.course.course_id);
    const instructorMatch =
      instructorFilterNuids.length === 0 || s.instructors.some((i) => instructorFilterNuids.includes(i.nuid));
    const dayMatch = dayFilter === 'all' || dayCategory(s.time_block.days) === dayFilter;
    return courseMatch && instructorMatch && dayMatch;
  });

  const daysInView = useMemo(() => ['M', 'T', 'W', 'R', 'F'], []);

  const calendarMap = useMemo(() => {
    const map = new Map<string, Map<string, SectionRichResponse[]>>();
    for (const s of filtered) {
      const key = `${s.time_block.start_time}|${s.time_block.end_time}`;
      if (!map.has(key)) map.set(key, new Map());
      const row = map.get(key)!;
      for (const d of expandDays(s.time_block.days)) {
        const arr = row.get(d) ?? [];
        arr.push(s);
        row.set(d, arr);
      }
    }
    // stable order inside a cell
    for (const row of map.values()) {
      for (const [d, arr] of row.entries()) {
        row.set(
          d,
          [...arr].sort((a, b) => a.course.name.localeCompare(b.course.name) || a.section_number - b.section_number),
        );
      }
    }
    return map;
  }, [filtered]);

  const sorted = [...filtered].sort((a, b) => {
    const av = getSortValue(a, sortKey);
    const bv = getSortValue(b, sortKey);
    const cmp = av < bv ? -1 : av > bv ? 1 : 0;
    return sortDir === 'asc' ? cmp : -cmp;
  });

  return (
    <div>
      {/* Filter bar */}
      <div className="flex flex-wrap items-center gap-3 mb-4">
        <div className="relative flex-1 min-w-64 max-w-[32rem]">
          <div className="mb-1">
            <MultiSearchableSelect
              options={courseOptions}
              value={courseFilterIds}
              onChange={setCourseFilterIds}
              placeholder="Selected courses…"
            />
          </div>

          <div className="relative">
            <svg
              className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
              />
            </svg>
            <input
              type="text"
              placeholder="Type a course name"
              value={courseQuery}
              onChange={(e) => setCourseQuery(e.target.value)}
              className="w-full pl-9 pr-3 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
            />
          </div>

          {courseSuggestions.length > 0 && (
            <div className="absolute left-0 right-0 mt-1 bg-white border border-gray-200 rounded-lg shadow-sm overflow-hidden z-10">
              {courseSuggestions.map((opt) => (
                <button
                  key={opt.value}
                  type="button"
                  onClick={() => {
                    setCourseFilterIds((prev) => [...prev, opt.value]);
                    setCourseQuery('');
                  }}
                  className="w-full text-left px-3 py-2 text-sm hover:bg-indigo-50 transition-colors"
                >
                  {opt.label}
                </button>
              ))}
            </div>
          )}
        </div>

        <div className="relative flex-1 min-w-64 max-w-[28rem]">
          <div className="mb-1">
            <MultiSearchableSelect
              options={instructorOptions}
              value={instructorFilterNuids}
              onChange={setInstructorFilterNuids}
              placeholder="Selected professors…"
            />
          </div>

          <div className="relative">
            <svg
              className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
              />
            </svg>
            <input
              type="text"
              placeholder="Type a professor name"
              value={instructorQuery}
              onChange={(e) => setInstructorQuery(e.target.value)}
              className="w-full pl-9 pr-3 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
            />
          </div>

          {instructorSuggestions.length > 0 && (
            <div className="absolute left-0 right-0 mt-1 bg-white border border-gray-200 rounded-lg shadow-sm overflow-hidden z-10">
              {instructorSuggestions.map((opt) => (
                <button
                  key={opt.value}
                  type="button"
                  onClick={() => {
                    setInstructorFilterNuids((prev) => [...prev, opt.value]);
                    setInstructorQuery('');
                  }}
                  className="w-full text-left px-3 py-2 text-sm hover:bg-indigo-50 transition-colors"
                >
                  {opt.label}
                </button>
              ))}
            </div>
          )}
        </div>

        <div className="flex gap-1">
          {(['all', 'MWR', 'MR', 'WF'] as DayFilter[]).map((f) => (
            <button
              key={f}
              onClick={() => setDayFilter(f)}
              className={`px-3 py-1.5 text-xs font-medium rounded-md transition-colors ${
                dayFilter === f
                  ? 'bg-indigo-600 text-white'
                  : 'bg-white text-gray-600 border border-gray-200 hover:bg-gray-50'
              }`}
            >
              {f === 'all' ? 'All days' : f}
            </button>
          ))}
        </div>

        <span className="text-xs text-gray-400 whitespace-nowrap">
          {sorted.length} of {sections.length} section{sections.length !== 1 ? 's' : ''}
        </span>

        {!readOnly && (
          <button
            onClick={() => setCreating(true)}
            className="ml-auto flex items-center gap-1.5 px-3 py-1.5 text-sm font-medium bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors"
          >
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
            </svg>
            Add section
          </button>
        )}
      </div>

      {viewMode === 'calendar' ? (
        <div className="rounded-lg border border-gray-200 bg-white overflow-auto max-h-[72vh]">
          {sorted.length === 0 ? (
            <div className="px-4 py-10 text-center text-sm text-gray-400">No sections match your filters.</div>
          ) : (
            <div className="min-w-[64rem]">
              {/* Header row */}
              <div className="sticky top-0 z-30 bg-white">
                <div
                  className="grid border-b border-gray-200 bg-gray-50"
                  style={{
                    gridTemplateColumns: `clamp(10rem, 16vw, 14rem) repeat(${daysInView.length || 1}, minmax(10.5rem, 1fr))`,
                  }}
                >
                  <div className="px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wider sticky left-0 z-40 bg-gray-50 border-r border-gray-200">
                    Time
                  </div>
                  {(daysInView.length ? daysInView : ['M']).map((d) => (
                    <div
                      key={d}
                      className="px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wider border-r border-gray-200 last:border-r-0"
                    >
                      {dayLabel(d)}
                    </div>
                  ))}
                </div>
              </div>

              {/* Body */}
              <div>
                {calendarTimeRows.map((tb) => (
                  <div
                    key={`${tb.start_time}|${tb.end_time}`}
                    className="grid border-b border-gray-100"
                    style={{
                      gridTemplateColumns: `clamp(10rem, 16vw, 14rem) repeat(${daysInView.length || 1}, minmax(10.5rem, 1fr))`,
                    }}
                  >
                    <div className="px-4 py-5 text-sm text-gray-700 bg-white sticky left-0 z-20 border-r border-gray-100 min-h-[clamp(10.5rem,12vw,14rem)] flex flex-col justify-center">
                      <div className="text-sm font-semibold text-gray-900">{tb.start_time}</div>
                      <div className="text-xs text-gray-400 mt-0.5">{tb.end_time}</div>
                    </div>

                    {daysInView.map((d) => {
                      const items = calendarMap.get(`${tb.start_time}|${tb.end_time}`)?.get(d) ?? [];
                      return (
                        <div
                          key={d}
                          className="px-3 py-3 min-h-[clamp(10.5rem,12vw,14rem)] bg-white border-r border-gray-100 last:border-r-0"
                        >
                          <div className="grid grid-cols-1 gap-2">
                            {items.map((section) => {
                              const lock = locks.get(section.section_id);
                              const isLocked = Boolean(lock);
                              const instructor = primaryInstructor(section);
                              const conflict = hasConflict(section);
                              const colors = courseColor();
                              return (
                                <button
                                  key={section.section_id}
                                  type="button"
                                  disabled={isLocked}
                                  onClick={() => !isLocked && setSelectedSection(section)}
                                  onMouseEnter={(e) => {
                                    if (!instructor) return;
                                    const rect = e.currentTarget.getBoundingClientRect();
                                    if (hoverTimeout.current) clearTimeout(hoverTimeout.current);
                                    hoverTimeout.current = setTimeout(() => setHoveredInstructor({ instructor, rect }), 250);
                                  }}
                                  onMouseLeave={handleInstructorMouseLeave}
                                  title={isLocked ? `Locked by ${lock!.display_name}` : `${section.course.name} §${section.section_number}`}
                                  className={`relative w-full aspect-square text-left rounded-xl border p-3 transition-colors shadow-sm overflow-hidden ${
                                    isLocked
                                      ? 'bg-amber-50/40 border-amber-200 text-amber-800 cursor-not-allowed opacity-70'
                                      : `${colors.card} hover:bg-white`
                                  }`}
                                >
                                  {!readOnly && (
                                    <button
                                      type="button"
                                      onClick={(e) => handleEditClick(e, section)}
                                      disabled={isLocked}
                                      title={isLocked ? `Locked by ${lock!.display_name}` : 'Edit section'}
                                      className="absolute bottom-2 right-2 p-1.5 rounded-md text-gray-400 hover:text-violet-700 hover:bg-white/70 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
                                    >
                                      <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                        <path
                                          strokeLinecap="round"
                                          strokeLinejoin="round"
                                          strokeWidth={1.75}
                                          d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"
                                        />
                                      </svg>
                                    </button>
                                  )}
                                  <div className="h-full flex flex-col">
                                    <div className="min-w-0">
                                      <div className="flex items-center gap-2">
                                        {conflict && (
                                          <span
                                            title="Instructor preference conflict"
                                            className="inline-block w-1.5 h-1.5 rounded-full bg-amber-400 shrink-0"
                                          />
                                        )}
                                        {!isLocked && <span className={`w-1 h-4 rounded-full ${colors.accent}`} />}
                                        <div className="text-sm font-semibold text-gray-900 truncate">{section.course.name}</div>
                                      </div>
                                      <div className="mt-1 text-[11px] text-gray-500">
                                        <span className="font-medium">§{section.section_number}</span>
                                      </div>
                                    </div>
                                    <div className="mt-auto flex items-end justify-between gap-2">
                                      <div className="text-[11px] text-gray-500">
                                        Cap {section.capacity}
                                      </div>
                                      {lock ? <LockBadge lock={lock} /> : null}
                                    </div>
                                  </div>
                                </button>
                              );
                            })}
                          </div>
                        </div>
                      );
                    })}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      ) : (
        /* Table */
        <div className="overflow-x-auto rounded-lg border border-gray-200">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                {(
                  [
                    { key: 'course', label: 'Course' },
                    { key: 'section', label: '§' },
                    { key: 'time', label: 'Time' },
                    { key: 'instructor', label: 'Instructor' },
                    { key: 'capacity', label: 'Capacity' },
                  ] as { key: SortKey; label: string }[]
                ).map(({ key, label }) => (
                  <th
                    key={key}
                    onClick={() => handleSort(key)}
                    className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer select-none hover:bg-gray-100 transition-colors"
                  >
                    <span className="flex items-center gap-1">
                      {label}
                      {sortKey === key ? (
                        <svg className="w-3 h-3 text-indigo-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d={sortDir === 'asc' ? 'M5 15l7-7 7 7' : 'M19 9l-7 7-7-7'} />
                        </svg>
                      ) : (
                        <svg className="w-3 h-3 text-gray-300" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16V4m0 0L3 8m4-4l4 4M17 8v12m0 0l4-4m-4 4l-4-4" />
                        </svg>
                      )}
                    </span>
                  </th>
                ))}
                {/* Actions column */}
                {!readOnly && <th className="px-4 py-3 w-24" />}
              </tr>
            </thead>

            <tbody className="bg-white divide-y divide-gray-100">
              {sorted.length === 0 ? (
                <tr>
                  <td colSpan={6} className="px-4 py-8 text-center text-sm text-gray-400">
                    No sections match your filters.
                  </td>
                </tr>
              ) : (
                sorted.map((section) => {
                  const conflict = hasConflict(section);
                  const instructor = primaryInstructor(section);
                  const lock = locks.get(section.section_id);
                  const isLocked = Boolean(lock);

                  return (
                    <tr
                      key={section.section_id}
                      onClick={() => !isLocked && setSelectedSection(section)}
                      className={`transition-colors ${isLocked ? 'bg-amber-50/40 cursor-default' : 'hover:bg-indigo-50/40 cursor-pointer'}`}
                    >
                      {/* Course */}
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-2 flex-wrap">
                          {conflict && (
                            <span title="Instructor preference conflict" className="inline-block w-1.5 h-1.5 rounded-full bg-amber-400 shrink-0" />
                          )}
                          <span className="text-sm font-medium text-gray-900">{section.course.name}</span>
                          {lock && <LockBadge lock={lock} />}
                        </div>
                        <div className="text-xs text-gray-400 mt-0.5">{section.course.credits} cr</div>
                      </td>

                      {/* Section # */}
                      <td className="px-4 py-3 text-sm text-gray-600 whitespace-nowrap">
                        §{section.section_number}
                      </td>

                      {/* Time */}
                      <td className="px-4 py-3 whitespace-nowrap">
                        <span className="text-sm font-medium text-gray-900">{section.time_block.days}</span>
                        <span className="text-sm text-gray-500 ml-1.5">
                          {section.time_block.start_time} – {section.time_block.end_time}
                        </span>
                      </td>

                      {/* Instructor */}
                      <td className="px-4 py-3 whitespace-nowrap">
                        {instructor ? (
                          <button
                            onClick={(e) => e.stopPropagation()}
                            onMouseEnter={(e) => handleInstructorMouseEnter(e, instructor)}
                            onMouseLeave={handleInstructorMouseLeave}
                            className="text-sm text-indigo-700 hover:text-indigo-900 underline decoration-dotted underline-offset-2 cursor-default"
                          >
                            {instructor.first_name} {instructor.last_name}
                          </button>
                        ) : (
                          <span className="text-sm text-gray-400 italic">Unassigned</span>
                        )}
                        {section.instructors.length > 1 && (
                          <span className="ml-1.5 text-xs text-gray-400">
                            +{section.instructors.length - 1} more
                          </span>
                        )}
                      </td>

                      {/* Capacity */}
                      <td className="px-4 py-3 text-sm text-gray-600 whitespace-nowrap">
                        {section.capacity}
                      </td>

                      {/* Actions */}
                      {!readOnly && (
                        <td className="px-4 py-3 whitespace-nowrap">
                          <div className="flex items-center gap-1 justify-end">
                            {lockError?.sectionId === section.section_id && (
                              <span className="text-xs text-amber-600 mr-1">{lockError.msg}</span>
                            )}
                            <button
                              onClick={(e) => handleEditClick(e, section)}
                              disabled={isLocked}
                              title={isLocked ? `Locked by ${lock!.display_name}` : 'Edit section'}
                              className="p-1.5 rounded-md text-gray-400 hover:text-indigo-600 hover:bg-indigo-50 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
                            >
                              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.75} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                              </svg>
                            </button>
                          </div>
                        </td>
                      )}
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      )}

      {/* Tooltip */}
      {hoveredInstructor && (
        <div
          onMouseEnter={() => { if (hoverTimeout.current) clearTimeout(hoverTimeout.current); }}
          onMouseLeave={handleInstructorMouseLeave}
        >
          <FacultyTooltip
            instructor={hoveredInstructor.instructor}
            allSections={sections}
            scheduleId={scheduleId}
            anchorRect={hoveredInstructor.rect}
          />
        </div>
      )}

      {/* Detail panel (view only, not available when locked) */}
      {selectedSection && (
        <SectionDetailPanel
          section={selectedSection}
          onClose={() => setSelectedSection(null)}
        />
      )}

      {/* Edit drawer */}
      {!readOnly && editingSection && (
        <SectionMutationDrawer
          mode="edit"
          scheduleId={scheduleId}
          section={editingSection}
          timeBlocks={timeBlocks}
          campusName={campusName}
          onClose={handleEditClose}
        />
      )}

      {/* Create drawer */}
      {!readOnly && creating && (
        <SectionMutationDrawer
          mode="create"
          scheduleId={scheduleId}
          timeBlocks={timeBlocks}
          campusName={campusName}
          onClose={() => setCreating(false)}
        />
      )}
    </div>
  );
}
