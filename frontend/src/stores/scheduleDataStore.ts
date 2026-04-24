import { create } from 'zustand';
import {
  getAutomatedCourseSchedulerAPI,
  type SectionRichResponse,
  type WarningResponse,
} from '../api/generated';

export type WsStatus = 'connecting' | 'connected' | 'disconnected';

export interface LockInfo {
  section_id: number;
  locked_by: number;
  display_name: string;
  expires_at: string;
}

type GetToken = () => Promise<string>;

interface ScheduleDataState {
  scheduleId: number | null;
  sections: SectionRichResponse[];
  locks: Map<number, LockInfo>;
  warnings: WarningResponse[];
  status: WsStatus;
  loading: boolean;
}

const WS_BASE = import.meta.env.VITE_API_BASE_URL
  ? import.meta.env.VITE_API_BASE_URL.replace(/^http/, 'ws')
  : 'ws://localhost:8000';

const initialState: ScheduleDataState = {
  scheduleId: null,
  sections: [],
  locks: new Map(),
  warnings: [],
  status: 'disconnected',
  loading: true,
};

export const useScheduleDataStore = create<ScheduleDataState>(() => ({ ...initialState }));

// ── Connection lifecycle (module-scoped, not reactive state) ─────────────────

let subscriberCount = 0;
let currentScheduleId: number | null = null;
let ws: WebSocket | null = null;
let reconnectTimer: ReturnType<typeof setTimeout> | null = null;
let closeTimer: ReturnType<typeof setTimeout> | null = null;
let attempts = 0;
let intentionalClose = false;

function resetState(scheduleId: number) {
  useScheduleDataStore.setState({
    scheduleId,
    sections: [],
    locks: new Map(),
    warnings: [],
    status: 'connecting',
    loading: true,
  });
}

function fetchInitialSnapshot(scheduleId: number) {
  const api = getAutomatedCourseSchedulerAPI();
  api
    .getScheduleLocksSchedulesScheduleIdLocksGet(scheduleId)
    .then((active) => {
      if (currentScheduleId !== scheduleId) return;
      const map = new Map<number, LockInfo>();
      for (const l of active) map.set(l.section_id, l);
      useScheduleDataStore.setState({ locks: map });
    })
    .catch(() => {});
  api
    .getScheduleWarningsSchedulesScheduleIdWarningsGet(scheduleId, { include_dismissed: true })
    .then((list) => {
      if (currentScheduleId !== scheduleId) return;
      useScheduleDataStore.setState({ warnings: list });
    })
    .catch(() => {});
}

function handleMessage(msg: { type: string; payload: unknown }, scheduleId: number) {
  if (currentScheduleId !== scheduleId) return;
  const state = useScheduleDataStore.getState();
  switch (msg.type) {
    case 'schedule': {
      const list = msg.payload as SectionRichResponse[];
      useScheduleDataStore.setState({ sections: list, loading: false });
      break;
    }
    case 'section_created': {
      const created = msg.payload as SectionRichResponse;
      useScheduleDataStore.setState({ sections: [...state.sections, created] });
      break;
    }
    case 'section_updated': {
      const { section_id, data } = msg.payload as {
        section_id: number;
        data: SectionRichResponse;
      };
      useScheduleDataStore.setState({
        sections: state.sections.map((s) => (s.section_id === section_id ? data : s)),
      });
      break;
    }
    case 'section_deleted': {
      const { section_id } = msg.payload as { section_id: number };
      const newLocks = new Map(state.locks);
      newLocks.delete(section_id);
      useScheduleDataStore.setState({
        sections: state.sections.filter((s) => s.section_id !== section_id),
        locks: newLocks,
      });
      break;
    }
    case 'lock_acquired': {
      const info = msg.payload as LockInfo;
      const newLocks = new Map(state.locks);
      newLocks.set(info.section_id, info);
      useScheduleDataStore.setState({ locks: newLocks });
      break;
    }
    case 'lock_released': {
      const { section_id } = msg.payload as { section_id: number };
      const newLocks = new Map(state.locks);
      newLocks.delete(section_id);
      useScheduleDataStore.setState({ locks: newLocks });
      break;
    }
    case 'comment_added': {
      const { section_id } = msg.payload as { section_id: number };
      useScheduleDataStore.setState({
        sections: state.sections.map((s) =>
          s.section_id === section_id
            ? { ...s, comment_count: (s.comment_count ?? 0) + 1 }
            : s,
        ),
      });
      break;
    }
    case 'comment_deleted': {
      const payload = msg.payload as { section_id: number; deleted_count?: number };
      const n =
        typeof payload.deleted_count === 'number' && Number.isFinite(payload.deleted_count)
          ? Math.max(1, Math.floor(payload.deleted_count))
          : 1;
      useScheduleDataStore.setState({
        sections: state.sections.map((s) =>
          s.section_id === payload.section_id
            ? { ...s, comment_count: Math.max(0, (s.comment_count ?? 0) - n) }
            : s,
        ),
      });
      break;
    }
    case 'section_warnings': {
      getAutomatedCourseSchedulerAPI()
        .getScheduleWarningsSchedulesScheduleIdWarningsGet(scheduleId, { include_dismissed: true })
        .then((list) => {
          if (currentScheduleId !== scheduleId) return;
          useScheduleDataStore.setState({ warnings: list });
        })
        .catch(() => {});
      break;
    }
  }
}

async function connect(scheduleId: number, getToken: GetToken) {
  if (currentScheduleId !== scheduleId) return;

  let token: string;
  try {
    token = await getToken();
  } catch {
    if (currentScheduleId === scheduleId) {
      useScheduleDataStore.setState({ status: 'disconnected' });
    }
    return;
  }
  if (currentScheduleId !== scheduleId) return;

  useScheduleDataStore.setState({ status: 'connecting' });

  const socket = new WebSocket(
    `${WS_BASE}/ws/${scheduleId}?token=${encodeURIComponent(token)}`,
  );
  ws = socket;

  socket.onopen = () => {
    if (ws !== socket) {
      socket.close();
      return;
    }
    attempts = 0;
    useScheduleDataStore.setState({ status: 'connected' });
    socket.send(JSON.stringify({ action: 'init' }));
  };

  socket.onmessage = (event: MessageEvent) => {
    if (ws !== socket) return;
    let msg: { type: string; payload: unknown };
    try {
      msg = JSON.parse(event.data as string);
    } catch {
      return;
    }
    handleMessage(msg, scheduleId);
  };

  socket.onclose = () => {
    if (ws === socket) ws = null;
    if (intentionalClose) return;
    if (currentScheduleId !== scheduleId || subscriberCount === 0) return;
    useScheduleDataStore.setState({ status: 'disconnected' });
    const delay = Math.min(1000 * 2 ** attempts, 10_000);
    attempts++;
    reconnectTimer = setTimeout(() => {
      reconnectTimer = null;
      if (currentScheduleId === scheduleId && subscriberCount > 0) {
        void connect(scheduleId, getToken);
      }
    }, delay);
  };

  socket.onerror = () => {
    socket.close();
  };
}

function openConnection(scheduleId: number, getToken: GetToken) {
  intentionalClose = false;
  attempts = 0;
  fetchInitialSnapshot(scheduleId);
  void connect(scheduleId, getToken);
}

function closeSocket() {
  if (reconnectTimer) {
    clearTimeout(reconnectTimer);
    reconnectTimer = null;
  }
  if (ws) {
    intentionalClose = true;
    try {
      ws.close();
    } catch {
      // ignore
    }
    ws = null;
  }
  attempts = 0;
}

export function subscribeToSchedule(scheduleId: number, getToken: GetToken): void {
  if (closeTimer) {
    clearTimeout(closeTimer);
    closeTimer = null;
  }

  if (currentScheduleId !== scheduleId) {
    closeSocket();
    currentScheduleId = scheduleId;
    subscriberCount = 1;
    resetState(scheduleId);
    openConnection(scheduleId, getToken);
    return;
  }

  subscriberCount++;
  if (!ws) {
    // Socket was deferred-closed; state may still be populated. Reopen without clearing sections.
    useScheduleDataStore.setState({ status: 'connecting' });
    openConnection(scheduleId, getToken);
  }
}

export function unsubscribeFromSchedule(scheduleId: number): void {
  if (currentScheduleId !== scheduleId) return;
  subscriberCount = Math.max(0, subscriberCount - 1);
  if (subscriberCount === 0) {
    if (closeTimer) clearTimeout(closeTimer);
    closeTimer = setTimeout(() => {
      closeTimer = null;
      if (subscriberCount === 0) {
        closeSocket();
        useScheduleDataStore.setState({ status: 'disconnected' });
      }
    }, 0);
  }
}

// ── Test-only helpers ───────────────────────────────────────────────────────

export const __testing = {
  reset() {
    if (reconnectTimer) clearTimeout(reconnectTimer);
    if (closeTimer) clearTimeout(closeTimer);
    reconnectTimer = null;
    closeTimer = null;
    if (ws) {
      intentionalClose = true;
      try {
        ws.close();
      } catch {
        // ignore
      }
    }
    ws = null;
    subscriberCount = 0;
    currentScheduleId = null;
    attempts = 0;
    intentionalClose = false;
    useScheduleDataStore.setState({ ...initialState });
  },
  getSubscriberCount: () => subscriberCount,
  getCurrentScheduleId: () => currentScheduleId,
  getWs: () => ws,
};
