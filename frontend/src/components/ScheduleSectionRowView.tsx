import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import type { CourseResponse, InstructorInfo, SectionRichResponse, TimeBlockInfo, WarningResponse } from '../api/generated';
import { getAutomatedCourseSchedulerAPI, Severity } from '../api/generated';
import { axiosInstance } from '../api/axiosInstance';
import type { LockInfo } from '../stores/scheduleDataStore';
import CrosslistSectionHint from './CrosslistSectionHint';
import FacultyTooltip from './FacultyTooltip';
import MultiSearchableSelect from './MultiSearchableSelect';
import SectionCalendarGrid, { LockBadge } from './SectionCalendarGrid';
import { parseTimeToMinutes } from '../utils/scheduleCalendar';
import SectionDetailPanel from './SectionDetailPanel';
import SectionMutationDrawer from './SectionMutationDrawer';
import type { SelectOption } from './SearchableSelect';
import { formatCourseLabel } from '../utils/courseFormat';

type SortKey = 'course' | 'section' | 'time' | 'instructor' | 'capacity';
type SortDir = 'asc' | 'desc';

interface Props {
  sections: SectionRichResponse[];
  scheduleId: number;
  locks: Map<number, LockInfo>;
  warnings: WarningResponse[];
  campusName: string | null;
  campusId: number | null;
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
      return section.time_block?.start_time ?? '';
    case 'instructor': {
      const inst = primaryInstructor(section);
      return inst ? inst.last_name.toLowerCase() : '';
    }
    case 'capacity':
      return section.capacity;
  }
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
  warnings,
  campusName,
  campusId,
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
  const [timeBlockFilterIds, setTimeBlockFilterIds] = useState<number[]>([]);
  const [selectedSection, setSelectedSection] = useState<SectionRichResponse | null>(null);
  const [editingSection, setEditingSection] = useState<SectionRichResponse | null>(null);
  const editingSectionRef = useRef<SectionRichResponse | null>(null);
  const [creating, setCreating] = useState(false);
  const [lockError, setLockError] = useState<{ sectionId: number; msg: string } | null>(null);

  useEffect(() => {
    editingSectionRef.current = editingSection;
  }, [editingSection]);

  // Release any held lock on unmount so navigating away with the editor open
  // does not leave a dangling lock (the shared WebSocket no longer closes on
  // page navigation, so the server's disconnect-release failsafe won't fire).
  useEffect(() => {
    return () => {
      const active = editingSectionRef.current;
      if (active) {
        void getAutomatedCourseSchedulerAPI()
          .releaseLockSectionsSectionIdUnlockPost(active.section_id)
          .catch(() => {});
      }
    };
  }, []);
  const [hoveredInstructor, setHoveredInstructor] = useState<{
    instructor: InstructorInfo;
    rect: DOMRect;
  } | null>(null);
  const [catalogCourses, setCatalogCourses] = useState<CourseResponse[]>([]);
  const hoverTimeout = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    const api = getAutomatedCourseSchedulerAPI();
    api.getCoursesCoursesGet().then((cs) => setCatalogCourses(cs)).catch(() => {});
  }, []);

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

  const courseMetaForUi = useCallback(
    (section: SectionRichResponse): { code: string | null; name: string } => {
      const { subject, code: codeNo, name } = section.course;
      const code = subject.trim() && codeNo != null ? `${subject}${codeNo}` : null;
      return { code, name };
    },
    [],
  );

  const courseLabelForUi = useCallback(
    (section: SectionRichResponse) =>
      formatCourseLabel({
        name: section.course.name,
        subject: section.course.subject,
        code: section.course.code,
      }),
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
    queueMicrotask(() => {
      setCreating(false);
      setEditingSection((current) => {
        if (!current) return null;
        const id = current.section_id;
        void getAutomatedCourseSchedulerAPI().releaseLockSectionsSectionIdUnlockPost(id).catch(() => {});
        return null;
      });
    });
  }, [isAdmin]);

  // Load all time blocks for this campus from the API.
  // Previously these were derived from existing sections, which meant the
  // dropdown was empty on a fresh (un-generated) schedule.  Loading directly
  // from the DB ensures all available blocks are always present.
  type TimeBlockFull = TimeBlockInfo & { block_group?: string | null };
  const [timeBlocks, setTimeBlocks] = useState<TimeBlockFull[]>([]);

  useEffect(() => {
    if (campusId == null) return;
    axiosInstance<{ time_block_id: number; meeting_days: string; start_time: string; end_time: string; block_group: string | null }[]>({
      method: 'GET',
      url: '/time-blocks',
      params: { campus_id: campusId },
    })
      .then((data) => {
        // Map the API response to TimeBlockFull — includes block_group so the
        // section drawer can collapse split-block pairs into one dropdown entry.
        const mapped: TimeBlockFull[] = data
          .map((tb) => ({
            time_block_id: tb.time_block_id,
            days: tb.meeting_days,
            start_time: tb.start_time,
            end_time: tb.end_time,
            block_group: tb.block_group,
          }))
          .sort((a, b) => {
            const ta = parseTimeToMinutes(a.start_time);
            const tb = parseTimeToMinutes(b.start_time);
            if (ta !== tb) return ta - tb;
            const da = a.days.localeCompare(b.days);
            if (da !== 0) return da;
            return a.end_time.localeCompare(b.end_time);
          });
        setTimeBlocks(mapped);
      })
      .catch(() => {
        // Fall back to deriving blocks from existing sections if the fetch fails
        const byKey = new Map<string, TimeBlockInfo>();
        for (const s of sections) {
          const tb = s.time_block;
          if (!tb) continue;
          const key = `${tb.days}|${tb.start_time}|${tb.end_time}`;
          if (!byKey.has(key)) byKey.set(key, tb);
        }
        setTimeBlocks([...byKey.values()]);
      });
  }, [campusId]); // eslint-disable-line react-hooks/exhaustive-deps


  const courseOptions = useMemo<SelectOption<number>[]>(() => {
    const byId = new Map<number, SelectOption<number>>();
    for (const s of sections) {
      if (!byId.has(s.course.course_id)) {
        byId.set(s.course.course_id, {
          value: s.course.course_id,
          label: courseLabelForUi(s),
        });
      }
    }
    return [...byId.values()].sort((a, b) => a.label.localeCompare(b.label));
  }, [sections, courseLabelForUi]);

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

  const timeBlockOptions = useMemo<SelectOption<number>[]>(() => {
    const byId = new Map<number, { days: string; start: string; end: string; opt: SelectOption<number> }>();
    for (const s of sections) {
      const tb = s.time_block;
      if (!tb || byId.has(tb.time_block_id)) continue;
      byId.set(tb.time_block_id, {
        days: tb.days,
        start: tb.start_time,
        end: tb.end_time,
        opt: { value: tb.time_block_id, label: `${tb.days} ${tb.start_time} – ${tb.end_time}` },
      });
    }
    const rows = [...byId.values()];
    rows.sort((a, b) => {
      const ta = parseTimeToMinutes(a.start);
      const tb = parseTimeToMinutes(b.start);
      if (ta !== tb) return ta - tb;
      const da = a.days.localeCompare(b.days);
      if (da !== 0) return da;
      return a.end.localeCompare(b.end);
    });
    return rows.map((r) => r.opt);
  }, [sections]);

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
    if (!userRoleLoaded) return;
    if (isAdmin) {
      if (isLockedFor(section)) return;
      void openAdminSectionEditor(section);
    } else {
      setSelectedSection(section);
    }
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
    const timeBlockMatch = timeBlockFilterIds.length === 0 || (s.time_block != null && timeBlockFilterIds.includes(s.time_block.time_block_id));
    return courseMatch && instructorMatch && timeBlockMatch;
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
                  className="w-full text-left px-3 py-2 text-sm hover:bg-burgundy-50 transition-colors"
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
                  className="w-full text-left px-3 py-2 text-sm hover:bg-burgundy-50 transition-colors"
                >
                  {opt.label}
                </button>
              ))}
            </div>
          )}
        </div>

        <div className="relative flex-1 min-w-56 max-w-[22rem]">
          <div className="mb-1">
            <MultiSearchableSelect
              options={timeBlockOptions}
              value={timeBlockFilterIds}
              onChange={setTimeBlockFilterIds}
              placeholder="Selected time blocks…"
            />
          </div>
        </div>

        <span className="text-xs text-gray-400 whitespace-nowrap">
          {sorted.length} of {sections.length} section{sections.length !== 1 ? 's' : ''}
        </span>

        {isAdmin && (
          <button
            onClick={() => setCreating(true)}
            className="ml-auto flex items-center gap-1.5 px-3 py-1.5 text-sm font-medium bg-burgundy-600 text-white rounded-lg hover:bg-burgundy-700 transition-colors"
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
          getCourseMetaForUi={courseMetaForUi}
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
                    { key: 'section', label: 'Section' },
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
                        <svg className="w-3 h-3 text-burgundy-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
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
                  const rowClass =
                    !userRoleLoaded
                      ? 'cursor-wait opacity-70'
                      : isLocked && isAdmin
                        ? 'bg-amber-50/40 cursor-default'
                        : isLocked && !isAdmin
                          ? 'bg-amber-50/40 cursor-pointer hover:bg-burgundy-50/40'
                          : 'hover:bg-burgundy-50/40 cursor-pointer';

                  return (
                    <tr
                      key={section.section_id}
                      onClick={() => userRoleLoaded && handleRowActivate(section)}
                      className={`transition-colors ${rowClass}`}
                    >
                      {/* Course */}
                      <td className="px-4 py-3">
                        {(() => {
                          const m = courseMetaForUi(section);
                          const sw = isAdmin
                            ? warnings.filter((w) => w.section_id === section.section_id && !w.dismissed)
                            : [];
                          const maxSev = sw.reduce((acc, w) => Math.max(acc, w.SeverityRank), 0);
                          const dotColor = maxSev === Severity.NUMBER_3 ? 'bg-red-500' : maxSev === Severity.NUMBER_2 ? 'bg-amber-500' : 'bg-yellow-400';
                          return (
                            <>
                              <div className="flex items-center gap-2 flex-wrap">
                                <span className="text-sm font-semibold text-gray-900">
                                  {m.code ?? m.name}
                                </span>
                                {maxSev > 0 && (
                                  <span
                                    title={sw.map((w) => w.Message).join('\n')}
                                    className={`inline-block w-2 h-2 rounded-full shrink-0 ${dotColor}`}
                                  />
                                )}
                                <SectionCommentIndicator count={section.comment_count ?? 0} />
                                {lock && <LockBadge lock={lock} />}
                              </div>
                              <div className="text-xs text-gray-500 mt-0.5 truncate max-w-[22rem]">
                                {m.code ? m.name : `${section.course.credits} cr`}
                              </div>
                            </>
                          );
                        })()}
                      </td>

                      {/* Section # */}
                      <td className="px-4 py-3 text-sm text-gray-600 whitespace-nowrap">
                        <span className="inline-flex items-center gap-1 ml-1">
                          {section.section_number}
                          <CrosslistSectionHint section={section} allSections={sections} />
                        </span>
                      </td>

                      {/* Time */}
                      <td className="px-4 py-3 whitespace-nowrap">
                        <span className="text-sm font-medium text-gray-900">{section.time_block?.days ?? '—'}</span>
                        <span className="text-sm text-gray-500 ml-1.5">
                          {section.time_block ? `${section.time_block.start_time} – ${section.time_block.end_time}` : 'Unassigned'}
                        </span>
                      </td>

                      {/* Instructor */}
                      <td className="px-4 py-3 whitespace-nowrap">
                        {instructor ? (
                          <button
                            type="button"
                            className="cursor-default text-left text-sm text-burgundy-700 underline decoration-dotted decoration-burgundy-400 underline-offset-2 hover:text-burgundy-900"
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
          key={editingSection.section_id}
          mode="edit"
          scheduleId={scheduleId}
          section={editingSection}
          warnings={warnings.filter((w) => w.section_id === editingSection.section_id && !w.dismissed)}
          timeBlocks={timeBlocks}
          campusId={campusId}
          campusName={campusName}
          courses={catalogCourses}
          scheduleSections={sections}
          onClose={handleEditClose}
          onTimeBlockCreated={(tb: TimeBlockFull) => setTimeBlocks((prev) => [...prev, tb].sort((a, b) => {
            const ta = parseTimeToMinutes(a.start_time);
            const tb2 = parseTimeToMinutes(b.start_time);
            if (ta !== tb2) return ta - tb2;
            return a.days.localeCompare(b.days);
          }))}
        />
      )}

      {/* Create drawer */}
      {isAdmin && creating && (
        <SectionMutationDrawer
          mode="create"
          scheduleId={scheduleId}
          timeBlocks={timeBlocks}
          campusId={campusId}
          campusName={campusName}
          courses={catalogCourses}
          scheduleSections={sections}
          onClose={() => setCreating(false)}
          onTimeBlockCreated={(tb: TimeBlockFull) => setTimeBlocks((prev) => [...prev, tb].sort((a, b) => {
            const ta = parseTimeToMinutes(a.start_time);
            const tb2 = parseTimeToMinutes(b.start_time);
            if (ta !== tb2) return ta - tb2;
            return a.days.localeCompare(b.days);
          }))}
        />
      )}
    </div>
  );
}
