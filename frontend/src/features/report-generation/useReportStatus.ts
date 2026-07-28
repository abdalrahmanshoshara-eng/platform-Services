'use client';

import { useEffect, useRef, useState } from 'react';
import { abortRequest, apiFetch } from '@/shared/api/client';
import { API_ENDPOINTS } from '@/shared/api/endpoints';
import { TERMINAL_STATUSES, type ReportStatusPayload } from '@/shared/api/types';

const BASE_INTERVAL = 2000;
const MAX_INTERVAL = 10000;

/**
 * Poll a report's status until it reaches a terminal state.
 * - stops on completed/failed/cancelled
 * - stops and cleans up on unmount (no duplicate timers)
 * - backs off on transient network errors, bounded by MAX_INTERVAL
 */
export function useReportStatus(reportId: number | null, initialStatus?: ReportStatusPayload['status']) {
  const [state, setState] = useState<ReportStatusPayload | null>(null);
  const [polling, setPolling] = useState(false);
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    if (reportId == null) return;
    if (initialStatus && TERMINAL_STATUSES.includes(initialStatus)) return;

    let cancelled = false;
    let interval = BASE_INTERVAL;
    const controller = new AbortController();
    setPolling(true);

    const tick = async () => {
      try {
        const payload = await apiFetch<ReportStatusPayload>(API_ENDPOINTS.reports.status(reportId), {
          signal: controller.signal,
        });
        if (cancelled) return;
        setState(payload);
        interval = BASE_INTERVAL; // reset backoff on success
        if (TERMINAL_STATUSES.includes(payload.status)) {
          setPolling(false);
          return;
        }
      } catch {
        if (cancelled) return;
        interval = Math.min(interval * 2, MAX_INTERVAL); // bounded backoff
      }
      timer.current = setTimeout(tick, interval);
    };

    tick();

    return () => {
      cancelled = true;
      abortRequest(controller);
      if (timer.current) clearTimeout(timer.current);
    };
  }, [reportId, initialStatus]);

  return { state, polling };
}
