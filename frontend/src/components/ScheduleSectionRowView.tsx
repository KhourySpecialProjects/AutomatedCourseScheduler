import { useCallback, useEffect, useRef, useState } from 'react';
import type { InstructorInfo, SectionRichResponse } from '../api/generated';
import FacultyTooltip from './FacultyTooltip';
import SectionDetailPanel from './SectionDetailPanel';

type SortKey = 'course' | 'section' | 'time' | 'instructor' | 'capacity';
type SortDir = 'asc' | 'desc';
type DayFilter = 'all' | 'MWF' | 'TTh' | 'Eve';

interface Props {
  sections: SectionRichResponse[];
  scheduleId: number;
}

function hasConflict(section: SectionRichResponse): boolean {
  return section.instructors.some((inst) =>
    inst.course_preferences.some(
      (cp) => cp.course_id === section.course.course_id && cp.preference === "Not my cup of tea",
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
  if (days === 'MWF') return 'MWF';
  if (days === 'TTh') return 'TTh';
  return 'Eve';
}

export default function ScheduleSectionRowView({ sections, scheduleId }: Props) {
  const [sortKey, setSortKey] = useState<SortKey>('course');
  const [sortDir, setSortDir] = useState<SortDir>('asc');
  const [filterText, setFilterText] = useState('');
  const [dayFilter, setDayFilter] = useState<DayFilter>('all');
  const [selectedSection, setSelectedSection] = useState<SectionRichResponse | null>(null);
  const [hoveredInstructor, setHoveredInstructor] = useState<{
    instructor: InstructorInfo;
    rect: DOMRect;
  } | null>(null);
  const hoverTimeout = useRef<ReturnType<typeof setTimeout> | null>(null);

  const handleSort = (key: SortKey) => {
    if (sortKey === key) {
      setSortDir((d) => (d === 'asc' ? 'desc' : 'asc'));
    } else {
      setSortKey(key);
      setSortDir('asc');
    }
  };

  const handleInstructorMouseEnter = useCallback(
    (e: React.MouseEvent<HTMLButtonElement>, instructor: InstructorInfo) => {
      const rect = e.currentTarget.getBoundingClientRect();
      if (hoverTimeout.current) clearTimeout(hoverTimeout.current);
      hoverTimeout.current = setTimeout(() => {
        setHoveredInstructor({ instructor, rect });
      }, 300);
    },
    [],
  );

  const handleInstructorMouseLeave = useCallback(() => {
    if (hoverTimeout.current) clearTimeout(hoverTimeout.current);
    hoverTimeout.current = setTimeout(() => setHoveredInstructor(null), 150);
  }, []);

  useEffect(() => {
    return () => {
      if (hoverTimeout.current) clearTimeout(hoverTimeout.current);
    };
  }, []);

  const filtered = sections.filter((s) => {
    const q = filterText.toLowerCase();
    const textMatch =
      !q ||
      s.course.name.toLowerCase().includes(q) ||
      s.instructors.some(
        (i) =>
          i.first_name.toLowerCase().includes(q) || i.last_name.toLowerCase().includes(q),
      );
    const dayMatch = dayFilter === 'all' || dayCategory(s.time_block.days) === dayFilter;
    return textMatch && dayMatch;
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
        <div className="relative flex-1 min-w-48">
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
            placeholder="Filter by course or professor…"
            value={filterText}
            onChange={(e) => setFilterText(e.target.value)}
            className="w-full pl-9 pr-3 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
          />
        </div>

        <div className="flex gap-1">
          {(['all', 'MWF', 'TTh', 'Eve'] as DayFilter[]).map((f) => (
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
      </div>

      {/* Table */}
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
                      <svg
                        className="w-3 h-3 text-indigo-500"
                        fill="none"
                        viewBox="0 0 24 24"
                        stroke="currentColor"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2}
                          d={
                            sortDir === 'asc'
                              ? 'M5 15l7-7 7 7'
                              : 'M19 9l-7 7-7-7'
                          }
                        />
                      </svg>
                    ) : (
                      <svg
                        className="w-3 h-3 text-gray-300"
                        fill="none"
                        viewBox="0 0 24 24"
                        stroke="currentColor"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2}
                          d="M7 16V4m0 0L3 8m4-4l4 4M17 8v12m0 0l4-4m-4 4l-4-4"
                        />
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
                const conflict = hasConflict(section);
                const instructor = primaryInstructor(section);

                return (
                  <tr
                    key={section.section_id}
                    onClick={() => setSelectedSection(section)}
                    className="hover:bg-indigo-50/40 cursor-pointer transition-colors"
                  >
                    {/* Course */}
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-2">
                        {conflict && (
                          <span
                            title="Instructor preference conflict"
                            className="inline-block w-1.5 h-1.5 rounded-full bg-amber-400 shrink-0"
                          />
                        )}
                        <span className="text-sm font-medium text-gray-900">
                          {section.course.name}
                        </span>
                      </div>
                      <div className="text-xs text-gray-400 mt-0.5">
                        {section.course.credits} cr
                      </div>
                    </td>

                    {/* Section # */}
                    <td className="px-4 py-3 text-sm text-gray-600 whitespace-nowrap">
                      §{section.section_number}
                    </td>

                    {/* Time */}
                    <td className="px-4 py-3 whitespace-nowrap">
                      <span className="text-sm font-medium text-gray-900">
                        {section.time_block.days}
                      </span>
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
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>

      {/* Tooltip */}
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

      {/* Detail panel */}
      {selectedSection && (
        <SectionDetailPanel
          section={selectedSection}
          onClose={() => setSelectedSection(null)}
        />
      )}
    </div>
  );
}
