import type { SectionRichResponse } from '../api/generated';
import SectionComments from './SectionComments';

interface Props {
  section: SectionRichResponse;
  onClose: () => void;
}

const PREFERENCE_STYLES: Record<string, { label: string; style: string }> = {
  'Eager to teach': { label: 'Eager', style: 'text-green-700 bg-green-50 border border-green-200' },
  'Willing to teach': { label: 'Willing', style: 'text-amber-700 bg-amber-50 border border-amber-200' },
  "Not my cup of tea": { label: 'Not interested', style: 'text-red-700 bg-red-50 border border-red-200' },
};

function coursePreferenceFor(
  instructor: SectionRichResponse['instructors'][0],
  courseId: number,
) {
  return instructor.course_preferences.find((cp) => cp.course_id === courseId);
}

function meetingPreferenceFor(
  instructor: SectionRichResponse['instructors'][0],
  days: string,
  startHour: number,
) {
  const category = deriveMeetingCategory(days, startHour);
  return instructor.meeting_preferences.find((mp) => mp.meeting_time === category);
}

function deriveMeetingCategory(days: string, startHour: number): string {
  if (startHour >= 17) return 'Evening';
  const period = startHour < 12 ? 'Morning' : 'Afternoon';
  return `${days} ${period}`;
}

function parseHour(timeStr: string): number {
  const [time, meridiem] = timeStr.split(' ');
  const [h] = time.split(':').map(Number);
  if (meridiem === 'PM' && h !== 12) return h + 12;
  if (meridiem === 'AM' && h === 12) return 0;
  return h;
}

export default function SectionDetailPanel({ section, onClose }: Props) {
  const startHour = parseHour(section.time_block.start_time);

  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black/20 z-40"
        onClick={onClose}
      />

      {/* Panel */}
      <div className="fixed right-0 top-0 h-full w-96 bg-white shadow-xl z-50 overflow-y-auto flex flex-col">
        {/* Header */}
        <div className="flex items-start justify-between p-6 border-b border-gray-100">
          <div>
            <h2 className="text-lg font-semibold text-gray-900">{section.course.name}</h2>
            <p className="text-sm text-gray-500 mt-0.5">
              Section {section.section_number} · {section.course.credits} credits
            </p>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 p-1 rounded"
            aria-label="Close"
          >
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <div className="flex-1 p-6 space-y-6">
          {/* Course info */}
          <section>
            <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">Course</h3>
            <p className="text-sm text-gray-700">{section.course.description}</p>
          </section>

          {/* Time & capacity */}
          <section>
            <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">Schedule</h3>
            <div className="space-y-1.5">
              <div className="flex items-center gap-2 text-sm">
                <svg className="w-4 h-4 text-gray-400 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <span className="font-medium text-gray-900">{section.time_block.days}</span>
                <span className="text-gray-600">
                  {section.time_block.start_time} – {section.time_block.end_time}
                </span>
              </div>
              <div className="flex items-center gap-2 text-sm text-gray-600">
                <svg className="w-4 h-4 text-gray-400 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z" />
                </svg>
                <span>Capacity: {section.capacity}</span>
              </div>
            </div>
          </section>

          {/* Instructors */}
          <section>
            <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3">
              {section.instructors.length === 1 ? 'Instructor' : 'Instructors'}
            </h3>

            {section.instructors.length === 0 ? (
              <p className="text-sm text-gray-400 italic">Unassigned</p>
            ) : (
              <div className="space-y-4">
                {section.instructors.map((instructor) => {
                  const coursePref = coursePreferenceFor(instructor, section.course.course_id);
                  const meetingPref = meetingPreferenceFor(instructor, section.time_block.days, startHour);

                  return (
                    <div key={instructor.nuid} className="border border-gray-100 rounded-lg p-3">
                      <div className="mb-2">
                        <div className="font-medium text-gray-900 text-sm">
                          {instructor.first_name} {instructor.last_name}
                        </div>
                        <div className="text-xs text-gray-500">{instructor.title}</div>
                        <a
                          href={`mailto:${instructor.email}`}
                          className="text-xs text-indigo-600 hover:underline"
                        >
                          {instructor.email}
                        </a>
                      </div>

                      <div className="space-y-1.5 mt-3">
                        <div className="flex items-center justify-between text-xs">
                          <span className="text-gray-500">Course preference</span>
                          {coursePref ? (
                            <span
                              className={`px-2 py-0.5 rounded-full text-xs font-medium ${PREFERENCE_STYLES[coursePref.preference]?.style ?? 'text-gray-500 bg-gray-50 border border-gray-200'}`}
                            >
                              {PREFERENCE_STYLES[coursePref.preference]?.label ?? coursePref.preference}
                            </span>
                          ) : (
                            <span className="text-gray-400">No preference recorded</span>
                          )}
                        </div>

                        <div className="flex items-center justify-between text-xs">
                          <span className="text-gray-500">Time preference</span>
                          {meetingPref ? (
                            <span
                              className={`px-2 py-0.5 rounded-full text-xs font-medium ${PREFERENCE_STYLES[meetingPref.preference]?.style ?? 'text-gray-500 bg-gray-50 border border-gray-200'}`}
                            >
                              {PREFERENCE_STYLES[meetingPref.preference]?.label ?? meetingPref.preference}
                            </span>
                          ) : (
                            <span className="text-gray-400">No preference recorded</span>
                          )}
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </section>

          <SectionComments sectionId={section.section_id} />
        </div>
      </div>
    </>
  );
}
