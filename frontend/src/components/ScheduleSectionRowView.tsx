import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import type { InstructorInfo, SectionRichResponse, TimeBlockInfo } from '../api/generated';
import { getAutomatedCourseSchedulerAPI } from '../api/generated';
import type { LockInfo } from '../hooks/useScheduleWebSocket';
import CrosslistSectionHint from './CrosslistSectionHint';
import FacultyTooltip from './FacultyTooltip';
import MultiSearchableSelect from './MultiSearchableSelect';
import SectionCalendarGrid, { LockBadge, parseTimeToMinutes } from './SectionCalendarGrid';
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
  onSelectedInstructorCountChange?: (count: number) => void;
  isAdmin: boolean;
  userRoleLoaded: boolean;
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

function SectionCommentIndicator({ count }: { count: number }) {
  if (count <= 0) return null;
  const label = `${count} comment${count === 1 ? '' : 's'}`;
  return (
    <span
      title={label}
      className="inline-flex items-center gap-0.5 text-slate-500 shrink-0"
      aria-label={label}
    >
      <svg className="w-3.5 h-3.5 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden>
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={1.75}
          d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"
        />
      </svg>
      <span className="text-[11px] font-medium tabular-nums leading-none">{count}</span>
    </span>
  );
}

export default function ScheduleSectionRowView({
  sections,
  scheduleId,
  locks,
  campusName,
  readOnly = false,
  viewMode = 'table',
  onSelectedCourseCountChange,
  onSelectedInstructorCountChange,
  isAdmin,
  userRoleLoaded,
}: Props) {
  const [sortKey, setSortKey] = useState<SortKey>('course');
  const [sortDir, setSortDir] = useState<SortDir>('asc');
  const [courseFilterIds, setCourseFilterIds] = useState<number[]>([]);
  const [courseQuery, setCourseQuery] = useState('');
  const [instructorFilterNuids, setInstructorFilterNuids] = useState<number[]>([]);
  const [instructorQuery, setInstructorQuery] = useState('');
  const [dayFilter, setDayFilter] = useState<DayFilter>('all');
  const [selectedSection, setSelectedSection] = useState<SectionRichResponse | null>(null);
  const [editingSection, setEditingSection] = useState<SectionRichResponse | null>(null);
  const [creating, setCreating] = useState(false);
  const [lockError, setLockError] = useState<{ sectionId: number; msg: string } | null>(null);
  const [hoveredInstructor, setHoveredInstructor] = useState<{
    instructor: InstructorInfo;
    rect: DOMRect;
  } | null>(null);
  const hoverTimeout = useRef<ReturnType<typeof setTimeout> | null>(null);

  const handleInstructorMouseEnter = useCallback((e: React.MouseEvent<HTMLElement>, instructor: InstructorInfo) => {
    const rect = e.currentTarget.getBoundingClientRect();
    if (hoverTimeout.current) clearTimeout(hoverTimeout.current);
    hoverTimeout.current = setTimeout(() => setHoveredInstructor({ instructor, rect }), 300);
  }, []);

  const handleInstructorMouseLeave = useCallback(() => {
    if (hoverTimeout.current) clearTimeout(hoverTimeout.current);
    hoverTimeout.current = setTimeout(() => setHoveredInstructor(null), 150);
  }, []);

  useEffect(
    () => () => {
      if (hoverTimeout.current) clearTimeout(hoverTimeout.current);
    },
    [],
  );

  const handleSort = (key: SortKey) => {
    if (sortKey === key) setSortDir((d) => (d === 'asc' ? 'desc' : 'asc'));
    else { setSortKey(key); setSortDir('asc'); }
  };

  useEffect(() => {
    onSelectedInstructorCountChange?.(instructorFilterNuids.length);
  }, [instructorFilterNuids.length, onSelectedInstructorCountChange]);

  useEffect(() => {
    onSelectedCourseCountChange?.(courseFilterIds.length);
  }, [courseFilterIds.length, onSelectedCourseCountChange]);

  useEffect(() => {
    if (isAdmin) return;
    setCreating(false);
    setEditingSection((current) => {
      if (!current) return null;
      const id = current.section_id;
      void getAutomatedCourseSchedulerAPI().releaseLockSectionsSectionIdUnlockPost(id).catch(() => {});
      return null;
    });
  }, [isAdmin]);

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

  function isLockedFor(section: SectionRichResponse): boolean {
    return Boolean(locks.get(section.section_id));
  }

  async function openAdminSectionEditor(section: SectionRichResponse) {
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

  function handleRowActivate(section: SectionRichResponse) {
    if (!userRoleLoaded || isLockedFor(section)) return;
    if (isAdmin) void openAdminSectionEditor(section);
    else setSelectedSection(section);
  }

  function handleEditClick(e: React.MouseEvent<HTMLButtonElement>, section: SectionRichResponse) {
    e.stopPropagation();
    if (!userRoleLoaded || !isAdmin || isLockedFor(section)) return;
    void openAdminSectionEditor(section);
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

        {isAdmin && (
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

      {lockError && (
        <p className="text-sm text-amber-700 mb-3" role="status">
          {lockError.msg}
        </p>
      )}

      {viewMode === 'calendar' ? (
        <SectionCalendarGrid
          sections={sections}
          displaySections={filtered}
          locks={locks}
          readOnly={readOnly || !isAdmin}
          onSectionClick={(section) => handleRowActivate(section)}
          onEditClick={handleEditClick}
          onInstructorMouseEnter={handleInstructorMouseEnter}
          onInstructorMouseLeave={handleInstructorMouseLeave}
        />
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
                        <svg className="w-3 h-3 text-indigo-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
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
              </tr>
            </thead>

            <tbody className="bg-white divide-y divide-gray-100">
              {sorted.length === 0 ? (
                <tr>
                  <td colSpan={5} className="px-4 py-8 text-center text-sm text-gray-400">
                    No sections match your filters.
                  </td>
                </tr>
              ) : (
                sorted.map((section) => {
                  const instructor = primaryInstructor(section);
                  const lock = locks.get(section.section_id);
                  const isLocked = Boolean(lock);
                  const rowInteractive = userRoleLoaded && !isLocked;

                  return (
                    <tr
                      key={section.section_id}
                      onClick={() => rowInteractive && handleRowActivate(section)}
                      className={`transition-colors ${
                        !userRoleLoaded
                          ? 'cursor-wait opacity-70'
                          : isLocked
                            ? 'bg-amber-50/40 cursor-default'
                            : 'hover:bg-indigo-50/40 cursor-pointer'
                      }`}
                    >
                      {/* Course */}
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-2 flex-wrap">
                          <span className="text-sm font-medium text-gray-900">{section.course.name}</span>
                          <SectionCommentIndicator count={section.comment_count ?? 0} />
                          {lock && <LockBadge lock={lock} />}
                        </div>
                        <div className="text-xs text-gray-400 mt-0.5">{section.course.credits} cr</div>
                      </td>

                      {/* Section # */}
                      <td className="px-4 py-3 text-sm text-gray-600 whitespace-nowrap">
                        <span className="inline-flex items-center gap-1">
                          §{section.section_number}
                          <CrosslistSectionHint section={section} allSections={sections} />
                        </span>
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
                            type="button"
                            className="cursor-default text-left text-sm text-indigo-700 underline decoration-dotted decoration-indigo-400 underline-offset-2 hover:text-indigo-900"
                            onClick={(e) => e.stopPropagation()}
                            onMouseEnter={(e) => handleInstructorMouseEnter(e, instructor)}
                            onMouseLeave={handleInstructorMouseLeave}
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
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      )}

      {hoveredInstructor && (
        <div
          onMouseEnter={() => {
            if (hoverTimeout.current) clearTimeout(hoverTimeout.current);
          }}
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
          allSections={sections}
          onClose={() => setSelectedSection(null)}
        />
      )}

      {/* Edit drawer */}
      {isAdmin && editingSection && (
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
      {isAdmin && creating && (
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
