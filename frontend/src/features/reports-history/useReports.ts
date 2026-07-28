'use client';

import { useEffect, useState } from 'react';
import { abortRequest, apiFetch, isAbortError } from '@/shared/api/client';
import { toMessage } from '@/shared/errors/apiError';
import type { GeneratedReport, PaginatedResponse } from '@/shared/api/types';

export function useReports() {
  const [reports, setReports] = useState<GeneratedReport[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const controller = new AbortController();
    apiFetch<PaginatedResponse<GeneratedReport>>('/reports/', { signal: controller.signal })
      .then((res) => setReports(res.results))
      .catch((err) => {
        if (!isAbortError(err, controller.signal)) setError(toMessage(err, 'تعذر تحميل التقارير.'));
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });
    return () => abortRequest(controller);
  }, []);

  return { reports, loading, error };
}
