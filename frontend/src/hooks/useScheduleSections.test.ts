import { renderHook, waitFor } from '@testing-library/react';
import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest';
import { useScheduleSections } from './useScheduleSections';
import * as generated from '../api/generated';
import type { SectionRichResponse } from '../api/generated';

const mockSection: SectionRichResponse = {
  section_id: 1,
  section_number: 1,
  capacity: 30,
  schedule_id: 42,
  course: { course_id: 10, name: 'Algorithms', description: 'Algo course', credits: 4 },
  time_block: {
    time_block_id: 5,
    days: 'MWR',
    start_time: '09:00',
    end_time: '10:30',
  },
  instructors: [
    {
      nuid: 100,
      first_name: 'Alice',
      last_name: 'Smith',
      email: 'alice@example.com',
      course_preferences: [],
      meeting_preferences: [],
    },
  ],
};

describe('useScheduleSections', () => {
  let getRichSpy: ReturnType<typeof vi.fn>;

  beforeEach(() => {
    getRichSpy = vi.fn();
    vi.spyOn(generated, 'getAutomatedCourseSchedulerAPI').mockReturnValue({
      getScheduleSectionsRichSchedulesScheduleIdSectionsRichGet: getRichSpy,
    } as unknown as ReturnType<typeof generated.getAutomatedCourseSchedulerAPI>);
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('returns loading=true initially', () => {
    getRichSpy.mockReturnValue(new Promise(() => {})); // never resolves
    const { result } = renderHook(() => useScheduleSections(42));
    expect(result.current.loading).toBe(true);
    expect(result.current.sections).toEqual([]);
    expect(result.current.error).toBeNull();
  });

  it('resolves sections and clears loading on success', async () => {
    getRichSpy.mockResolvedValue([mockSection]);
    const { result } = renderHook(() => useScheduleSections(42));

    await waitFor(() => expect(result.current.loading).toBe(false));

    expect(result.current.sections).toEqual([mockSection]);
    expect(result.current.error).toBeNull();
  });

  it('sets error and clears loading on failure', async () => {
    getRichSpy.mockRejectedValue(new Error('Network error'));
    const { result } = renderHook(() => useScheduleSections(42));

    await waitFor(() => expect(result.current.loading).toBe(false));

    expect(result.current.error).toBe('Failed to load sections.');
    expect(result.current.sections).toEqual([]);
  });

  it('calls the API with the provided scheduleId', async () => {
    getRichSpy.mockResolvedValue([]);
    renderHook(() => useScheduleSections(99));

    await waitFor(() => expect(getRichSpy).toHaveBeenCalledWith(99));
  });

  it('re-fetches when scheduleId changes', async () => {
    getRichSpy.mockResolvedValue([mockSection]);
    const { rerender } = renderHook(({ id }) => useScheduleSections(id), {
      initialProps: { id: 1 },
    });

    await waitFor(() => expect(getRichSpy).toHaveBeenCalledWith(1));

    getRichSpy.mockResolvedValue([]);
    rerender({ id: 2 });

    await waitFor(() => expect(getRichSpy).toHaveBeenCalledWith(2));
    expect(getRichSpy).toHaveBeenCalledTimes(2);
  });

  it('ignores stale response after scheduleId changes mid-flight', async () => {
    let resolveFirst!: (v: SectionRichResponse[]) => void;
    const firstRequest = new Promise<SectionRichResponse[]>((res) => {
      resolveFirst = res;
    });

    getRichSpy
      .mockReturnValueOnce(firstRequest)
      .mockResolvedValueOnce([mockSection]);

    const { result, rerender } = renderHook(({ id }) => useScheduleSections(id), {
      initialProps: { id: 1 },
    });

    // Change scheduleId before first request resolves
    rerender({ id: 2 });

    // Wait for second request to finish
    await waitFor(() => expect(result.current.loading).toBe(false));

    // Resolve the stale first request — should not overwrite state
    resolveFirst([{ ...mockSection, section_id: 999 }]);

    // Give a tick for any potential state update
    await new Promise((r) => setTimeout(r, 20));

    expect(result.current.sections).toEqual([mockSection]);
  });
});
