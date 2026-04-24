import { useEffect, useRef } from 'react';
import { useAuth0 } from '@auth0/auth0-react';
import {
  subscribeToSchedule,
  unsubscribeFromSchedule,
  useScheduleDataStore,
  type LockInfo,
  type WsStatus,
} from '../stores/scheduleDataStore';
import type { SectionRichResponse, WarningResponse } from '../api/generated';

export type { LockInfo, WsStatus };

export interface UseScheduleDataResult {
  sections: SectionRichResponse[];
  locks: Map<number, LockInfo>;
  warnings: WarningResponse[];
  loading: boolean;
  status: WsStatus;
}

const EMPTY_LOCKS: Map<number, LockInfo> = new Map();
const EMPTY_SECTIONS: SectionRichResponse[] = [];
const EMPTY_WARNINGS: WarningResponse[] = [];

export function useScheduleData(scheduleId: number | null): UseScheduleDataResult {
  const { getAccessTokenSilently } = useAuth0();
  const getTokenRef = useRef(getAccessTokenSilently);

  useEffect(() => {
    getTokenRef.current = getAccessTokenSilently;
  }, [getAccessTokenSilently]);

  useEffect(() => {
    if (scheduleId == null) return;
    const getToken = () => getTokenRef.current();
    subscribeToSchedule(scheduleId, getToken);
    return () => {
      unsubscribeFromSchedule(scheduleId);
    };
  }, [scheduleId]);

  const activeScheduleId = useScheduleDataStore((s) => s.scheduleId);
  const sections = useScheduleDataStore((s) => s.sections);
  const locks = useScheduleDataStore((s) => s.locks);
  const warnings = useScheduleDataStore((s) => s.warnings);
  const loading = useScheduleDataStore((s) => s.loading);
  const status = useScheduleDataStore((s) => s.status);

  if (scheduleId == null) {
    return {
      sections: EMPTY_SECTIONS,
      locks: EMPTY_LOCKS,
      warnings: EMPTY_WARNINGS,
      loading: false,
      status: 'disconnected',
    };
  }

  // Guard against returning data from a different schedule during a switch.
  if (activeScheduleId !== scheduleId) {
    return {
      sections: EMPTY_SECTIONS,
      locks: EMPTY_LOCKS,
      warnings: EMPTY_WARNINGS,
      loading: true,
      status: 'connecting',
    };
  }

  return { sections, locks, warnings, loading, status };
}
