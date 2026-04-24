import { renderHook, act, waitFor } from '@testing-library/react';
import { vi, describe, it, expect, beforeAll, afterAll, beforeEach, afterEach } from 'vitest';
import { useScheduleData } from './useScheduleData';
import { __testing } from '../stores/scheduleDataStore';
import * as generated from '../api/generated';
import type { SectionRichResponse } from '../api/generated';

// ── Auth0 mock ────────────────────────────────────────────────────────────────
vi.mock('@auth0/auth0-react', () => ({
  useAuth0: () => ({
    getAccessTokenSilently: vi.fn().mockResolvedValue('mock-token'),
  }),
}));

// ── API mock ──────────────────────────────────────────────────────────────────
vi.mock('../api/generated', async (importOriginal) => {
  const actual = await importOriginal<typeof generated>();
  return {
    ...actual,
    getAutomatedCourseSchedulerAPI: vi.fn(() => ({
      getScheduleLocksSchedulesScheduleIdLocksGet: vi.fn().mockResolvedValue([]),
      getScheduleWarningsSchedulesScheduleIdWarningsGet: vi.fn().mockResolvedValue([]),
    })),
  };
});

// ── WebSocket mock ────────────────────────────────────────────────────────────
interface MockWs {
  url: string;
  send: ReturnType<typeof vi.fn>;
  close: ReturnType<typeof vi.fn>;
  onopen: ((e: Event) => void) | null;
  onmessage: ((e: { data: string }) => void) | null;
  onclose: ((e: { code?: number }) => void) | null;
  onerror: ((e: Event) => void) | null;
}

let mockWs: MockWs;
const MockWebSocket = vi.fn().mockImplementation((url: string) => {
  mockWs = {
    url,
    send: vi.fn(),
    close: vi.fn().mockImplementation(function (this: MockWs) {
      this.onclose?.({ code: 1000 });
    }),
    onopen: null,
    onmessage: null,
    onclose: null,
    onerror: null,
  };
  return mockWs;
});

beforeAll(() => {
  vi.stubGlobal('WebSocket', MockWebSocket);
});
afterAll(() => {
  vi.unstubAllGlobals();
});
beforeEach(() => {
  MockWebSocket.mockClear();
});
afterEach(() => {
  __testing.reset();
});

// ── Fixtures ──────────────────────────────────────────────────────────────────
const makeSection = (overrides: Partial<SectionRichResponse> = {}): SectionRichResponse => ({
  section_id: 1,
  section_number: 1,
  capacity: 30,
  schedule_id: 10,
  comment_count: 0,
  crosslisted_section_id: null,
  course: { course_id: 5, subject: 'CS', code: 3500, name: 'Algorithms', description: 'Algo', credits: 4 },
  time_block: { time_block_id: 2, days: 'MWR', start_time: '09:00', end_time: '10:30' },
  instructors: [],
  ...overrides,
});

async function renderConnected(scheduleId = 10) {
  const hookResult = renderHook(({ id }: { id: number }) => useScheduleData(id), {
    initialProps: { id: scheduleId },
  });
  await waitFor(() => expect(MockWebSocket).toHaveBeenCalled());
  await act(async () => {
    mockWs.onopen?.(new Event('open'));
  });
  return hookResult;
}

function sendMessage(type: string, payload: unknown) {
  act(() => {
    mockWs.onmessage?.({ data: JSON.stringify({ type, payload }) });
  });
}

// ── Tests ─────────────────────────────────────────────────────────────────────
describe('useScheduleData', () => {
  it('starts loading/connecting and reaches connected on open', async () => {
    const { result } = renderHook(() => useScheduleData(10));
    expect(result.current.loading).toBe(true);
    expect(result.current.status).toBe('connecting');
    expect(result.current.sections).toEqual([]);

    await waitFor(() => expect(MockWebSocket).toHaveBeenCalled());
    await act(async () => {
      mockWs.onopen?.(new Event('open'));
    });

    expect(result.current.status).toBe('connected');
    expect(mockWs.send).toHaveBeenCalledWith(JSON.stringify({ action: 'init' }));
  });

  it('passes scheduleId to the WebSocket URL', async () => {
    renderHook(() => useScheduleData(7));
    await waitFor(() => expect(MockWebSocket).toHaveBeenCalled());
    expect(MockWebSocket.mock.calls[0][0]).toContain('/ws/7');
  });

  it('returns empty state when scheduleId is null and does not open a socket', () => {
    const { result } = renderHook(() => useScheduleData(null));
    expect(result.current.loading).toBe(false);
    expect(result.current.status).toBe('disconnected');
    expect(MockWebSocket).not.toHaveBeenCalled();
  });

  it('sets sections and clears loading on "schedule" event', async () => {
    const { result } = await renderConnected();
    const section = makeSection();
    sendMessage('schedule', [section]);
    expect(result.current.sections).toEqual([section]);
    expect(result.current.loading).toBe(false);
  });

  it('appends section on "section_created"', async () => {
    const { result } = await renderConnected();
    sendMessage('schedule', [makeSection({ section_id: 1 })]);
    sendMessage('section_created', makeSection({ section_id: 2, section_number: 2 }));
    expect(result.current.sections).toHaveLength(2);
    expect(result.current.sections[1].section_id).toBe(2);
  });

  it('patches the correct row on "section_updated"', async () => {
    const { result } = await renderConnected();
    sendMessage('schedule', [
      makeSection({ section_id: 1 }),
      makeSection({ section_id: 2, section_number: 2 }),
    ]);
    sendMessage('section_updated', { section_id: 1, data: makeSection({ section_id: 1, capacity: 99 }) });
    expect(result.current.sections[0].capacity).toBe(99);
    expect(result.current.sections[1].section_id).toBe(2);
  });

  it('removes the correct row on "section_deleted"', async () => {
    const { result } = await renderConnected();
    sendMessage('schedule', [
      makeSection({ section_id: 1 }),
      makeSection({ section_id: 2, section_number: 2 }),
    ]);
    sendMessage('section_deleted', { section_id: 1 });
    expect(result.current.sections).toHaveLength(1);
    expect(result.current.sections[0].section_id).toBe(2);
  });

  it('increments comment_count on "comment_added"', async () => {
    const { result } = await renderConnected();
    sendMessage('schedule', [makeSection({ section_id: 1, comment_count: 2 })]);
    sendMessage('comment_added', { section_id: 1 });
    expect(result.current.sections[0].comment_count).toBe(3);
  });

  it('decrements comment_count by deleted_count on "comment_deleted"', async () => {
    const { result } = await renderConnected();
    sendMessage('schedule', [makeSection({ section_id: 1, comment_count: 2 })]);
    sendMessage('comment_deleted', { section_id: 1, deleted_count: 2 });
    expect(result.current.sections[0].comment_count).toBe(0);
  });

  it('adds a lock on "lock_acquired" and removes it on "lock_released"', async () => {
    const { result } = await renderConnected();
    const lockInfo = { section_id: 1, locked_by: 42, display_name: 'Jane Doe', expires_at: '2099-01-01T00:00:00Z' };
    sendMessage('lock_acquired', lockInfo);
    expect(result.current.locks.get(1)).toEqual(lockInfo);

    sendMessage('lock_released', { section_id: 1 });
    expect(result.current.locks.has(1)).toBe(false);
  });
});

describe('useScheduleData — subscriber lifecycle', () => {
  it('two subscribers to the same scheduleId share one WebSocket', async () => {
    const hook1 = renderHook(() => useScheduleData(10));
    await waitFor(() => expect(MockWebSocket).toHaveBeenCalledTimes(1));
    await act(async () => {
      mockWs.onopen?.(new Event('open'));
    });

    const hook2 = renderHook(() => useScheduleData(10));
    await act(async () => {
      // no new socket should open
    });
    expect(MockWebSocket).toHaveBeenCalledTimes(1);

    const section = makeSection();
    sendMessage('schedule', [section]);
    expect(hook1.result.current.sections).toEqual([section]);
    expect(hook2.result.current.sections).toEqual([section]);
  });

  it('keeps the socket open when one of two subscribers unmounts', async () => {
    const hook1 = await renderConnected(10);
    const socketRef = mockWs;

    const hook2 = renderHook(() => useScheduleData(10));
    expect(MockWebSocket).toHaveBeenCalledTimes(1);

    await act(async () => {
      hook1.unmount();
      await new Promise((r) => setTimeout(r, 5));
    });

    expect(socketRef.close).not.toHaveBeenCalled();
    expect(__testing.getSubscriberCount()).toBe(1);
    void hook2;
  });

  it('defers close on last unsubscribe and cancels it if a new subscriber mounts for the same scheduleId', async () => {
    const hook1 = await renderConnected(10);
    const socketRef = mockWs;

    await act(async () => {
      hook1.unmount();
    });
    // Subscriber count is 0 but the close is deferred via setTimeout(0).
    expect(socketRef.close).not.toHaveBeenCalled();

    // Re-subscribe in the same tick (simulates route change Schedules → Faculty).
    const hook2 = renderHook(() => useScheduleData(10));
    await act(async () => {
      await new Promise((r) => setTimeout(r, 5));
    });

    expect(socketRef.close).not.toHaveBeenCalled();
    expect(MockWebSocket).toHaveBeenCalledTimes(1);
    void hook2;
  });

  it('closes the socket after the deferred window if no re-subscribe arrives', async () => {
    const hook1 = await renderConnected(10);
    const socketRef = mockWs;

    await act(async () => {
      hook1.unmount();
      await new Promise((r) => setTimeout(r, 5));
    });

    expect(socketRef.close).toHaveBeenCalled();
    expect(__testing.getSubscriberCount()).toBe(0);
  });

  it('switches connection when a subscriber requests a different scheduleId', async () => {
    const { rerender } = await renderConnected(10);
    const firstSocket = mockWs;

    await act(async () => {
      rerender({ id: 20 });
    });
    await waitFor(() => expect(MockWebSocket).toHaveBeenCalledTimes(2));

    expect(firstSocket.close).toHaveBeenCalled();
    expect(MockWebSocket.mock.calls[1][0]).toContain('/ws/20');
  });
});
