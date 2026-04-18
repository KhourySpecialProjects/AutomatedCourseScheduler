import { createPortal } from 'react-dom';
import type { InstructorInfo, SectionRichResponse } from '../api/generated';

const PREFERENCE_STYLES: Record<string, string> = {
  'Eager to teach': 'bg-green-100 text-green-800',
  'Willing to teach': 'bg-amber-100 text-amber-800',
  "Not my cup of tea": 'bg-red-100 text-red-800',
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
      s.schedule_id === scheduleId &&
      s.instructors.some((i) => i.nuid === instructor.nuid),
  );

  const top = anchorRect.bottom + window.scrollY + 8;
  const left = Math.min(anchorRect.left + window.scrollX, window.innerWidth - 320);

  return createPortal(
    <div
      className="fixed z-50 w-72 bg-white border border-gray-200 rounded-lg shadow-lg p-4 text-sm"
      style={{ top, left }}
    >
      <div className="mb-3">
        <div className="font-semibold text-gray-900">
          {instructor.first_name} {instructor.last_name}
        </div>
        <div className="text-xs text-burgundy-600">{instructor.email}</div>
      </div>

      <div className="mb-3">
        <div className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-1">
          This Schedule ({sectionsTeaching.length} section{sectionsTeaching.length !== 1 ? 's' : ''})
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
          <div className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-1">
            Course Preferences
          </div>
          <ul className="space-y-1">
            {instructor.course_preferences.map((cp) => (
              <li key={cp.course_id} className="flex items-center justify-between gap-2">
                <span className="text-xs text-gray-700 truncate">{cp.course_name}</span>
                <PreferenceBadge preference={cp.preference} />
              </li>
            ))}
          </ul>
        </div>
      )}

      {instructor.meeting_preferences.length > 0 && (
        <div>
          <div className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-1">
            Meeting Preferences
          </div>
          <ul className="space-y-1">
            {instructor.meeting_preferences.map((mp, i) => (
              <li key={i} className="flex items-center justify-between gap-2">
                {/* need to get the actual time block rather than id */}
                <span className="text-xs text-gray-700">{mp.time_block_id}</span>
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
