import { useEffect, useState } from 'react';
import { getAutomatedCourseSchedulerAPI, SectionRichResponse } from '../api/generated';

interface UseScheduleSectionsResult {
  sections: SectionRichResponse[];
  loading: boolean;
  error: string | null;
}

export function useScheduleSections(scheduleId: number): UseScheduleSectionsResult {
  const [sections, setSections] = useState<SectionRichResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    const { getScheduleSectionsRichSchedulesScheduleIdSectionsRichGet } = getAutomatedCourseSchedulerAPI();

    getScheduleSectionsRichSchedulesScheduleIdSectionsRichGet(scheduleId)
      .then((data) => {
        if (!cancelled) {
          setSections(data);
          setLoading(false);
          setError(null);
        }
      })
      .catch(() => {
        if (!cancelled) {
          setError('Failed to load sections.');
          setLoading(false);
        }
      });

    return () => {
      cancelled = true;
    };
  }, [scheduleId]);

  return { sections, loading, error };
}
