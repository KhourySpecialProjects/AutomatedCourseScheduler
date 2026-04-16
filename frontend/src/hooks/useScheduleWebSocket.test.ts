import { renderHook, act, waitFor } from '@testing-library/react';
import { vi, describe, it, expect, beforeAll, afterAll, beforeEach } from 'vitest';
import { useScheduleWebSocket } from './useScheduleWebSocket';
import * as generated from '../api/generated';
import type { SectionRichResponse } from '../api/generated';

// ── Auth0 mock ────────────────────────────────────────────────────────────────
vi.mock('@auth0/auth0-react', () => ({
  useAuth0: () => ({
    getAccessTokenSilently: vi.fn().mockResolvedValue('mock-token'),
  }),
}));

// ── API mock (initial locks fetch) ────────────────────────────────────────────
vi.mock('../api/generated', async (importOriginal) => {
  const actual = await importOriginal<typeof generated>();
  return {
    ...actual,
    getAutomatedCourseSchedulerAPI: vi.fn(() => ({
      getScheduleLocksSchedulesScheduleIdLocksGet: vi.fn().mockResolvedValue([]),
    })),
  };
});

// ── WebSocket mock ────────────────────────────────────────────────────────────
interface MockWs {
  send: ReturnType<typeof vi.fn>;
  close: ReturnType<typeof vi.fn>;
  onopen: ((e: Event) => void) | null;
  onmessage: ((e: { data: string }) => void) | null;
  onclose: ((e: { code?: number }) => void) | null;
  onerror: ((e: Event) => void) | null;
}

let mockWs: MockWs;

const MockWebSocket = vi.fn().mockImplementation(() => {
  mockWs = {
    send: vi.fn(),
    close: vi.fn(),
    onopen: null,
    onmessage: null,
    onclose: null,
    onerror: null,
  };
  return mockWs;
});

// Stub WebSocket once for the whole suite so stale async coroutines
// never hit Node 24's built-in WebSocket after unstub.
beforeAll(() => { vi.stubGlobal('WebSocket', MockWebSocket); });
afterAll(() => { vi.unstubAllGlobals(); });
beforeEach(() => { MockWebSocket.mockClear(); });

// ── Fixtures ──────────────────────────────────────────────────────────────────
const makeSection = (overrides: Partial<SectionRichResponse> = {}): SectionRichResponse => ({
  section_id: 1,
  section_number: 1,
  capacity: 30,
  schedule_id: 10,
  comment_count: 0,
  crosslisted_section_id: null,
  course: { course_id: 5, name: 'Algorithms', description: 'Algo', credits: 4 },
  time_block: { time_block_id: 2, days: 'MWR', start_time: '09:00', end_time: '10:30' },
  instructors: [],
  ...overrides,
});

// ── Helpers ───────────────────────────────────────────────────────────────────

/** Render hook and advance to the connected state. */
async function renderConnected(scheduleId = 10) {
  const hookResult = renderHook(() => useScheduleWebSocket(scheduleId));
  // Wait for connect()'s async chain (getToken → new WebSocket) to complete
  await waitFor(() => expect(MockWebSocket).toHaveBeenCalled());
  // Trigger onopen and flush state
  await act(async () => { mockWs.onopen?.(new Event('open')); });
  return hookResult;
}

function sendMessage(type: string, payload: unknown) {
  act(() => {
    mockWs.onmessage?.({ data: JSON.stringify({ type, payload }) });
  });
}

// ── Tests ─────────────────────────────────────────────────────────────────────
describe('useScheduleWebSocket', () => {
  it('starts loading/connecting and reaches connected on open', async () => {
    const { result } = renderHook(() => useScheduleWebSocket(10));
    // Before WebSocket connects: loading state
    expect(result.current.loading).toBe(true);
    expect(result.current.status).toBe('connecting');
    expect(result.current.sections).toEqual([]);

    // Wait for WS creation and open
    await waitFor(() => expect(MockWebSocket).toHaveBeenCalled());
    await act(async () => { mockWs.onopen?.(new Event('open')); });

    expect(result.current.status).toBe('connected');
    expect(mockWs.send).toHaveBeenCalledWith(JSON.stringify({ action: 'init' }));
  });

  it('passes scheduleId to the WebSocket hook', async () => {
    renderHook(() => useScheduleWebSocket(7));
    await waitFor(() => expect(MockWebSocket).toHaveBeenCalled());
    expect(MockWebSocket.mock.calls[0][0]).toContain('/ws/7');
  });

  it('sets sections and clears loading on "schedule" event', async () => {
    const { result } = await renderConnected();

    const section = makeSection();
    sendMessage('schedule', [section]);

    expect(result.current.sections).toEqual([section]);
    expect(result.current.loading).toBe(false);
  });

  it('appends section on "section_created" event', async () => {
    const { result } = await renderConnected();

    sendMessage('schedule', [makeSection({ section_id: 1 })]);
    sendMessage('section_created', makeSection({ section_id: 2, section_number: 2 }));

    expect(result.current.sections).toHaveLength(2);
    expect(result.current.sections[1].section_id).toBe(2);
  });

  it('patches the correct row on "section_updated" event', async () => {
    const { result } = await renderConnected();

    sendMessage('schedule', [
      makeSection({ section_id: 1 }),
      makeSection({ section_id: 2, section_number: 2 }),
    ]);
    sendMessage('section_updated', { section_id: 1, data: makeSection({ section_id: 1, capacity: 99 }) });

    expect(result.current.sections[0].capacity).toBe(99);
    expect(result.current.sections[1].section_id).toBe(2);
  });

  it('removes the correct row on "section_deleted" event', async () => {
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
    sendMessage('comment_added', { section_id: 1, comment_id: 9, user_id: 1, content: 'x' });
    expect(result.current.sections[0].comment_count).toBe(3);
  });

  it('decrements comment_count on "comment_deleted"', async () => {
    const { result } = await renderConnected();
    sendMessage('schedule', [makeSection({ section_id: 1, comment_count: 2 })]);
    sendMessage('comment_deleted', { section_id: 1, comment_id: 9 });
    expect(result.current.sections[0].comment_count).toBe(1);
  });

  it('decrements comment_count by deleted_count when parent delete removes replies', async () => {
    const { result } = await renderConnected();
    sendMessage('schedule', [makeSection({ section_id: 1, comment_count: 2 })]);
    sendMessage('comment_deleted', {
      section_id: 1,
      comment_id: 9,
      deleted_comment_ids: [9, 10],
      deleted_count: 2,
    });
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

  it('sets status=disconnected and schedules reconnect on close', async () => {
    // Connect with real timers, then switch to fake timers for reconnect assertions
    const { result } = await renderConnected();
    MockWebSocket.mockClear();

    vi.useFakeTimers();
    try {
      await act(async () => { mockWs.onclose?.({ code: 1001 }); });
      expect(result.current.status).toBe('disconnected');

      await act(async () => { vi.advanceTimersByTime(1500); });
      expect(MockWebSocket).toHaveBeenCalledTimes(1);
    } finally {
      vi.useRealTimers();
    }
  });

  it('closes WebSocket and cancels reconnect on unmount', async () => {
    // Connect with real timers, then switch to fake timers for unmount assertions
    const { result, unmount } = await renderConnected();
    const wsRef = mockWs;

    vi.useFakeTimers();
    try {
      await act(async () => { unmount(); });

      MockWebSocket.mockClear();
      await act(async () => { vi.advanceTimersByTime(5000); });

      expect(wsRef.close).toHaveBeenCalled();
      expect(MockWebSocket).not.toHaveBeenCalled();
      void result;
    } finally {
      vi.useRealTimers();
    }
  });
});
