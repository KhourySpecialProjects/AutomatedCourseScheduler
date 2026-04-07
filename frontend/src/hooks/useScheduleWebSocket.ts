import { useEffect, useRef, useState } from 'react';
import { useAuth0 } from '@auth0/auth0-react';
import type { SectionRichResponse } from '../api/generated';

const WS_BASE = import.meta.env.VITE_API_BASE_URL
  ? import.meta.env.VITE_API_BASE_URL.replace(/^http/, 'ws')
  : 'ws://localhost:8000';

export type WsStatus = 'connecting' | 'connected' | 'disconnected';

interface UseScheduleWebSocketResult {
  sections: SectionRichResponse[];
  loading: boolean;
  status: WsStatus;
}

export function useScheduleWebSocket(scheduleId: number): UseScheduleWebSocketResult {
  const { getAccessTokenSilently } = useAuth0();
  const [sections, setSections] = useState<SectionRichResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [status, setStatus] = useState<WsStatus>('connecting');
  // Stable ref so event handlers always see the latest list without re-subscribing
  const sectionsRef = useRef<SectionRichResponse[]>([]);

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
        // Ask the server for the current section list
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
  }, [scheduleId]); // getAccessTokenSilently is stable; scheduleId drives reconnects

  return { sections, loading, status };
}
