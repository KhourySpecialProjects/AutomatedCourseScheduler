import { useEffect, useState } from 'react';
import { getFastAPI } from '../api/generated';
import type { SectionResponse } from '../api/generated';

interface UseSectionsResult {
  sections: SectionResponse[];
  loading: boolean;
  error: string | null;
}

export function useSections(): UseSectionsResult {
  const [sections, setSections] = useState<SectionResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const { getSectionsSectionsGet } = getFastAPI();
    getSectionsSectionsGet()
      .then(setSections)
      .catch(() => setError('Failed to load sections'))
      .finally(() => setLoading(false));
  }, []);

  return { sections, loading, error };
}
