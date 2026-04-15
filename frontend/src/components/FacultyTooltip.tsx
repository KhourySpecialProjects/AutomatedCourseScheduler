import { createPortal } from 'react-dom';
import type { InstructorInfo, MeetingPreferenceInfo, SectionRichResponse } from '../api/generated';

function meetingPreferenceLabel(
  mp: MeetingPreferenceInfo,
  timeBlockLabelById: Map<number, string>,
): string {
  const r = mp as unknown as Record<string, unknown>;
  const mt = r.meeting_time ?? r.meetingTime;
  if (typeof mt === 'string' && mt.trim()) return mt;
  const id = r.time_block_id ?? r.timeBlockId;
  if (typeof id === 'number') return timeBlockLabelById.get(id) ?? `Time block #${id}`;
  return '—';
}

const PREFERENCE_STYLES: Record<string, string> = {
  'Eager to teach': 'bg-green-100 text-green-800',
  'Willing to teach': 'bg-amber-100 text-amber-800',
  'Not my cup of tea': 'bg-red-100 text-red-800',
};

interface Props {
  instructor: InstructorInfo;
  allSections: SectionRichResponse[];
  scheduleId: number;
  anchorRect: DOMRect;
}

function PreferenceBadge({ preference }: { preference: string }) {
  const style = PREFERENCE_STYLES[preference] ?? 'bg-gray-100 text-gray-700';
  const short =
    preference === 'Eager to teach'
      ? 'Eager'
      : preference === 'Willing to teach'
        ? 'Willing'
        : 'Not interested';
  return (
    <span className={`inline-block px-1.5 py-0.5 rounded text-xs font-medium ${style}`}>
      {short}
    </span>
  );
}

export default function FacultyTooltip({ instructor, allSections, scheduleId, anchorRect }: Props) {
  const sectionsTeaching = allSections.filter(
    (s) =>
      s.schedule_id === scheduleId && s.instructors.some((i) => i.nuid === instructor.nuid),
  );
  const timeBlockLabelById = new Map<number, string>();
  for (const s of allSections) {
    if (s.schedule_id !== scheduleId) continue;
    const tb = s.time_block;
    if (!timeBlockLabelById.has(tb.time_block_id)) {
      timeBlockLabelById.set(tb.time_block_id, `${tb.days} ${tb.start_time}–${tb.end_time}`);
    }
  }

  const pad = 8;
  const width = 288;
  const top = anchorRect.bottom + pad;
  let left = anchorRect.left + anchorRect.width / 2 - width / 2;
  left = Math.max(pad, Math.min(left, window.innerWidth - width - pad));

  return createPortal(
    <div
      className="pointer-events-auto fixed z-[10000] w-72 rounded-lg border border-gray-200 bg-white p-4 text-sm shadow-lg"
      style={{ top, left, width }}
    >
      <div className="mb-3">
        <div className="font-semibold text-gray-900">
          {instructor.first_name} {instructor.last_name}
        </div>
        <div className="text-xs text-indigo-600">{instructor.email}</div>
      </div>

      <div className="mb-3">
        <div className="mb-1 text-xs font-medium uppercase tracking-wide text-gray-500">
          This schedule ({sectionsTeaching.length} section{sectionsTeaching.length !== 1 ? 's' : ''})
        </div>
        {sectionsTeaching.length === 0 ? (
          <div className="text-xs text-gray-400">No sections assigned</div>
        ) : (
          <ul className="space-y-0.5">
            {sectionsTeaching.map((s) => (
              <li key={s.section_id} className="text-xs text-gray-700">
                {s.course.name} §{s.section_number} —{' '}
                <span className="text-gray-500">
                  {s.time_block.days} {s.time_block.start_time}
                </span>
              </li>
            ))}
          </ul>
        )}
      </div>

      {instructor.course_preferences.length > 0 && (
        <div className="mb-3">
          <div className="mb-1 text-xs font-medium uppercase tracking-wide text-gray-500">
            Course preferences
          </div>
          <ul className="space-y-1">
            {instructor.course_preferences.map((cp) => (
              <li key={cp.course_id} className="flex items-center justify-between gap-2">
                <span className="truncate text-xs text-gray-700">{cp.course_name}</span>
                <PreferenceBadge preference={cp.preference} />
              </li>
            ))}
          </ul>
        </div>
      )}

      {instructor.meeting_preferences.length > 0 && (
        <div>
          <div className="mb-1 text-xs font-medium uppercase tracking-wide text-gray-500">
            Meeting preferences
          </div>
          <ul className="space-y-1">
            {instructor.meeting_preferences.map((mp, i) => (
              <li key={i} className="flex items-center justify-between gap-2">
                <span className="text-xs text-gray-700">{meetingPreferenceLabel(mp, timeBlockLabelById)}</span>
                <PreferenceBadge preference={mp.preference} />
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>,
    document.body,
  );
}
