import { useMemo } from 'react';
import type { InstructorInfo, SectionRichResponse } from '../api/generated';
import type { LockInfo } from '../hooks/useScheduleWebSocket';

// Exported so ScheduleSectionRowView can reuse it for time block sorting.
export function parseTimeToMinutes(raw: string): number {
  const s = raw.trim();
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

export function expandDays(days: string): string[] {
  const result: string[] = [];
  for (const ch of days) {
    if ('MTWRF'.includes(ch)) result.push(ch);
  }
  return result;
}

function dayLabel(letter: string): string {
  return (
    ({ M: 'Mon', T: 'Tue', W: 'Wed', R: 'Thu', F: 'Fri' } as Record<string, string>)[letter] ??
    letter
  );
}

export function LockBadge({ lock }: { lock: LockInfo }) {
  return (
    <span
      title={`Locked by ${lock.display_name}`}
      className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-xs font-medium bg-amber-50 text-amber-700 border border-amber-200"
    >
      <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={2}
          d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"
        />
      </svg>
      {lock.display_name}
    </span>
  );
}

const DAYS = ['M', 'T', 'W', 'R', 'F'];
const CARD_COLORS = { card: 'bg-violet-50 border-violet-200', accent: 'bg-violet-500' };

interface Props {
  /** Used to derive the set of time-row labels (all available time slots). */
  sections: SectionRichResponse[];
  /** Which sections actually appear in calendar cells. Defaults to `sections`. */
  displaySections?: SectionRichResponse[];
  locks?: Map<number, LockInfo>;
  readOnly?: boolean;
  onSectionClick?: (section: SectionRichResponse) => void;
  onEditClick?: (e: React.MouseEvent<HTMLButtonElement>, section: SectionRichResponse) => void;
  onInstructorMouseEnter?: (
    e: React.MouseEvent<HTMLButtonElement>,
    instructor: InstructorInfo,
  ) => void;
  onInstructorMouseLeave?: () => void;
  emptyMessage?: string;
}

export default function SectionCalendarGrid({
  sections,
  displaySections,
  locks = new Map(),
  readOnly = true,
  onSectionClick,
  onEditClick,
  onInstructorMouseEnter,
  onInstructorMouseLeave,
  emptyMessage = 'No sections match your filters.',
}: Props) {
  const visible = displaySections ?? sections;

  // Time rows derived from ALL sections (not just visible) so the grid always shows
  // the full set of possible slots even when filtered.
  const calendarTimeRows = useMemo(() => {
    const byRange = new Map<string, { start_time: string; end_time: string }>();
    for (const s of sections) {
      const key = `${s.time_block.start_time}|${s.time_block.end_time}`;
      if (!byRange.has(key))
        byRange.set(key, { start_time: s.time_block.start_time, end_time: s.time_block.end_time });
    }
    return [...byRange.values()].sort((a, b) => {
      const ta = parseTimeToMinutes(a.start_time);
      const tb = parseTimeToMinutes(b.start_time);
      if (ta !== tb) return ta - tb;
      return a.end_time.localeCompare(b.end_time);
    });
  }, [sections]);

  // Calendar map derived from the *visible* (filtered) sections.
  const calendarMap = useMemo(() => {
    const map = new Map<string, Map<string, SectionRichResponse[]>>();
    for (const s of visible) {
      const key = `${s.time_block.start_time}|${s.time_block.end_time}`;
      if (!map.has(key)) map.set(key, new Map());
      const row = map.get(key)!;
      for (const d of expandDays(s.time_block.days)) {
        const arr = row.get(d) ?? [];
        arr.push(s);
        row.set(d, arr);
      }
    }
    for (const row of map.values()) {
      for (const [d, arr] of row.entries()) {
        row.set(
          d,
          [...arr].sort(
            (a, b) =>
              a.course.name.localeCompare(b.course.name) || a.section_number - b.section_number,
          ),
        );
      }
    }
    return map;
  }, [visible]);

  return (
    <div className="rounded-lg border border-gray-200 bg-white overflow-auto max-h-[72vh]">
      {visible.length === 0 ? (
        <div className="px-4 py-10 text-center text-sm text-gray-400">{emptyMessage}</div>
      ) : (
        <div className="min-w-[64rem]">
          {/* Sticky header */}
          <div className="sticky top-0 z-30 bg-white">
            <div
              className="grid border-b border-gray-200 bg-gray-50"
              style={{
                gridTemplateColumns: `clamp(10rem, 16vw, 14rem) repeat(${DAYS.length}, minmax(10.5rem, 1fr))`,
              }}
            >
              <div className="px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wider sticky left-0 z-40 bg-gray-50 border-r border-gray-200">
                Time
              </div>
              {DAYS.map((d) => (
                <div
                  key={d}
                  className="px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wider border-r border-gray-200 last:border-r-0"
                >
                  {dayLabel(d)}
                </div>
              ))}
            </div>
          </div>

          {/* Body rows */}
          <div>
            {calendarTimeRows.map((tb) => (
              <div
                key={`${tb.start_time}|${tb.end_time}`}
                className="grid border-b border-gray-100"
                style={{
                  gridTemplateColumns: `clamp(10rem, 16vw, 14rem) repeat(${DAYS.length}, minmax(10.5rem, 1fr))`,
                }}
              >
                {/* Time label */}
                <div className="px-4 py-5 text-sm text-gray-700 bg-white sticky left-0 z-20 border-r border-gray-100 min-h-[clamp(10.5rem,12vw,14rem)] flex flex-col justify-center">
                  <div className="text-sm font-semibold text-gray-900">{tb.start_time}</div>
                  <div className="text-xs text-gray-400 mt-0.5">{tb.end_time}</div>
                </div>

                {/* Day cells */}
                {DAYS.map((d) => {
                  const items =
                    calendarMap.get(`${tb.start_time}|${tb.end_time}`)?.get(d) ?? [];
                  return (
                    <div
                      key={d}
                      className="px-3 py-3 min-h-[clamp(10.5rem,12vw,14rem)] bg-white border-r border-gray-100 last:border-r-0"
                    >
                      <div className="grid grid-cols-1 gap-2">
                        {items.map((section) => {
                          const lock = locks.get(section.section_id);
                          const isLocked = Boolean(lock);
                          const instructor = section.instructors[0];
                          const conflict = section.instructors.some((inst) =>
                            inst.course_preferences.some(
                              (cp) =>
                                cp.course_id === section.course.course_id &&
                                cp.preference === 'Not my cup of tea',
                            ),
                          );

                          return (
                            <button
                              key={section.section_id}
                              type="button"
                              disabled={isLocked || !onSectionClick}
                              onClick={() => !isLocked && onSectionClick?.(section)}
                              onMouseEnter={
                                instructor && onInstructorMouseEnter
                                  ? (e) => onInstructorMouseEnter(e, instructor)
                                  : undefined
                              }
                              onMouseLeave={onInstructorMouseLeave}
                              title={
                                isLocked
                                  ? `Locked by ${lock!.display_name}`
                                  : `${section.course.name} §${section.section_number}`
                              }
                              className={`relative w-full aspect-square text-left rounded-xl border p-3 transition-colors shadow-sm overflow-hidden ${
                                isLocked
                                  ? 'bg-amber-50/40 border-amber-200 text-amber-800 cursor-not-allowed opacity-70'
                                  : onSectionClick
                                    ? `${CARD_COLORS.card} hover:bg-white cursor-pointer`
                                    : `${CARD_COLORS.card} cursor-default`
                              }`}
                            >
                              {!readOnly && onEditClick && (
                                <button
                                  type="button"
                                  onClick={(e) => onEditClick(e, section)}
                                  disabled={isLocked}
                                  title={
                                    isLocked ? `Locked by ${lock!.display_name}` : 'Edit section'
                                  }
                                  className="absolute bottom-2 right-2 p-1.5 rounded-md text-gray-400 hover:text-violet-700 hover:bg-white/70 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
                                >
                                  <svg
                                    className="w-4 h-4"
                                    fill="none"
                                    viewBox="0 0 24 24"
                                    stroke="currentColor"
                                  >
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
                                    {!isLocked && (
                                      <span
                                        className={`w-1 h-4 rounded-full ${CARD_COLORS.accent}`}
                                      />
                                    )}
                                    <div className="text-sm font-semibold text-gray-900 truncate">
                                      {section.course.name}
                                    </div>
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
  );
}
