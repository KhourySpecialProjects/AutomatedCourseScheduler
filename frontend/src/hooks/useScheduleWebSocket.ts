import { useEffect, useRef, useState } from 'react';
import { useAuth0 } from '@auth0/auth0-react';
import { getAutomatedCourseSchedulerAPI, type SectionRichResponse } from '../api/generated';

const WS_BASE = import.meta.env.VITE_API_BASE_URL
  ? import.meta.env.VITE_API_BASE_URL.replace(/^http/, 'ws')
  : 'ws://localhost:8000';

export type WsStatus = 'connecting' | 'connected' | 'disconnected';

export interface LockInfo {
  section_id: number;
  locked_by: number;
  display_name: string;
  expires_at: string;
}

export interface UseScheduleWebSocketResult {
  sections: SectionRichResponse[];
  locks: Map<number, LockInfo>;
  loading: boolean;
  status: WsStatus;
}

export function useScheduleWebSocket(scheduleId: number): UseScheduleWebSocketResult {
  const { getAccessTokenSilently } = useAuth0();
  const [sections, setSections] = useState<SectionRichResponse[]>([]);
  const [locks, setLocks] = useState<Map<number, LockInfo>>(new Map());
  const [loading, setLoading] = useState(true);
  const [status, setStatus] = useState<WsStatus>('connecting');
  const sectionsRef = useRef<SectionRichResponse[]>([]);
  const locksRef = useRef<Map<number, LockInfo>>(new Map());

  // Fetch initial lock state (locks are not broadcast on connect, only on change)
  useEffect(() => {
    const { getScheduleLocksSchedulesScheduleIdLocksGet } = getAutomatedCourseSchedulerAPI();
    getScheduleLocksSchedulesScheduleIdLocksGet(scheduleId).then((activeLocks) => {
      const map = new Map<number, LockInfo>();
      for (const l of activeLocks) {
        map.set(l.section_id, l);
      }
      locksRef.current = map;
      setLocks(new Map(map));
    }).catch(() => {});
  }, [scheduleId]);

  useEffect(() => {
    let ws: WebSocket | null = null;
    let reconnectTimer: ReturnType<typeof setTimeout> | null = null;
    let attempts = 0;
    let cancelled = false;

    async function connect() {
      if (cancelled) return;

      let token: string;
      try {
        token = await getAccessTokenSilently();
      } catch {
        if (!cancelled) setStatus('disconnected');
        return;
      }

      if (cancelled) return;
      setStatus('connecting');

      ws = new WebSocket(`${WS_BASE}/ws/${scheduleId}?token=${encodeURIComponent(token)}`);

      ws.onopen = () => {
        if (cancelled) { ws?.close(); return; }
        attempts = 0;
        setStatus('connected');
        ws?.send(JSON.stringify({ action: 'init' }));
      };

      ws.onmessage = (event: MessageEvent) => {
        if (cancelled) return;
        let msg: { type: string; payload: unknown };
        try {
          msg = JSON.parse(event.data as string);
        } catch {
          return;
        }

        switch (msg.type) {
          case 'schedule': {
            const list = msg.payload as SectionRichResponse[];
            sectionsRef.current = list;
            setSections(list);
            setLoading(false);
            break;
          }
          case 'section_created': {
            const created = msg.payload as SectionRichResponse;
            sectionsRef.current = [...sectionsRef.current, created];
            setSections(sectionsRef.current);
            break;
          }
          case 'section_updated': {
            const { section_id, data } = msg.payload as {
              section_id: number;
              data: SectionRichResponse;
            };
            sectionsRef.current = sectionsRef.current.map((s) =>
              s.section_id === section_id ? data : s,
            );
            setSections(sectionsRef.current);
            break;
          }
          case 'section_deleted': {
            const { section_id } = msg.payload as { section_id: number };
            sectionsRef.current = sectionsRef.current.filter(
              (s) => s.section_id !== section_id,
            );
            setSections(sectionsRef.current);
            // Clear any lock for the deleted section
            locksRef.current = new Map(locksRef.current);
            locksRef.current.delete(section_id);
            setLocks(new Map(locksRef.current));
            break;
          }
          case 'lock_acquired': {
            const lockInfo = msg.payload as LockInfo;
            locksRef.current = new Map(locksRef.current);
            locksRef.current.set(lockInfo.section_id, lockInfo);
            setLocks(new Map(locksRef.current));
            break;
          }
          case 'lock_released': {
            const { section_id } = msg.payload as { section_id: number };
            locksRef.current = new Map(locksRef.current);
            locksRef.current.delete(section_id);
            setLocks(new Map(locksRef.current));
            break;
          }
          case 'comment_added': {
            const payload = msg.payload as { section_id: number };
            const { section_id: sid } = payload;
            sectionsRef.current = sectionsRef.current.map((s) =>
              s.section_id === sid
                ? { ...s, comment_count: (s.comment_count ?? 0) + 1 }
                : s,
            );
            setSections([...sectionsRef.current]);
            break;
          }
          case 'comment_deleted': {
            const payload = msg.payload as { section_id: number };
            const { section_id: sid } = payload;
            sectionsRef.current = sectionsRef.current.map((s) =>
              s.section_id === sid
                ? { ...s, comment_count: Math.max(0, (s.comment_count ?? 0) - 1) }
                : s,
            );
            setSections([...sectionsRef.current]);
            break;
          }
        }
      };

      ws.onclose = () => {
        if (cancelled) return;
        setStatus('disconnected');
        const delay = Math.min(1000 * 2 ** attempts, 10_000);
        attempts++;
        reconnectTimer = setTimeout(connect, delay);
      };

      ws.onerror = () => {
        ws?.close();
      };
    }

    connect();

    return () => {
      cancelled = true;
      if (reconnectTimer) clearTimeout(reconnectTimer);
      ws?.close();
    };
  }, [scheduleId]); // getAccessTokenSilently is stable

  return { sections, locks, loading, status };
}
