import { renderHook, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { useSections } from './useSections';
import * as generated from '../api/generated';
import type { SectionResponse } from '../api/generated';

const mockSections: SectionResponse[] = [
  { SectionID: 1, Schedule: 1, TimeBlock: 1, Course: 101, Capacity: 25, Instructor: 3 },
];

describe('useSections', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it('returns sections after successful fetch', async () => {
    vi.spyOn(generated, 'getFastAPI').mockReturnValue({
      getSectionsSectionsGet: vi.fn().mockResolvedValue(mockSections),
    });

    const { result } = renderHook(() => useSections());

    expect(result.current.loading).toBe(true);

    await waitFor(() => expect(result.current.loading).toBe(false));

    expect(result.current.sections).toEqual(mockSections);
    expect(result.current.error).toBeNull();
  });

  it('sets error on failed fetch', async () => {
    vi.spyOn(generated, 'getFastAPI').mockReturnValue({
      getSectionsSectionsGet: vi.fn().mockRejectedValue(new Error('Network Error')),
    });

    const { result } = renderHook(() => useSections());

    await waitFor(() => expect(result.current.loading).toBe(false));

    expect(result.current.sections).toEqual([]);
    expect(result.current.error).toBe('Failed to load sections');
  });

  it('starts in loading state', () => {
    vi.spyOn(generated, 'getFastAPI').mockReturnValue({
      getSectionsSectionsGet: vi.fn().mockReturnValue(new Promise(() => {})),
    });

    const { result } = renderHook(() => useSections());

    expect(result.current.loading).toBe(true);
  });
});
