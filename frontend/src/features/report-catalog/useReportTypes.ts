'use client';

import { useEffect, useState } from 'react';
import { abortRequest, apiFetch, isAbortError } from '@/shared/api/client';
import { API_ENDPOINTS } from '@/shared/api/endpoints';
import { toMessage } from '@/shared/errors/apiError';
import type { ReportType } from '@/shared/api/types';

export function useReportTypes(enabled = true) {
  const [reportTypes, setReportTypes] = useState<ReportType[]>([]);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!enabled) return;
    const controller = new AbortController();
    apiFetch<ReportType[]>(API_ENDPOINTS.reportTypes.list, { signal: controller.signal })
      .then(setReportTypes)
      .catch((err) => {
        if (!isAbortError(err, controller.signal)) setError(toMessage(err, 'تعذر تحميل أنواع التقارير.'));
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });
    return () => abortRequest(controller);
  }, [enabled]);

  return { reportTypes, error, loading };
}
